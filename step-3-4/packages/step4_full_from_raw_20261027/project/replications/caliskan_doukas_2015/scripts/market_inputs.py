"""Strict pre-fiscal-end CRSP windows for the Table 4 replication.

No regressions are estimated.  Requests must contain one unique event_id per
company/fiscal-date event and a historically linked PERMNO.  Monthly price
volatility excludes the fiscal-end calendar month.  Daily return volatility
uses the 255 *market* dates strictly before datadate, so missing observations
are never replaced by older valid returns.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
from pathlib import Path
import time

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


VERSION = "strict-market-windows-v2"
CACHE_LAYOUT = "strict-market-windows-v1"
CALENDAR_RULE = "all-market dates with at least one finite economic RETX (>=-1), including zero"
DAILY_FILE = "dsf_all_2005-01-01_2024-06-30.csv.gz"
MONTHLY_FILE = "msf_all_2000-12_2024-06.csv.gz"
BUCKETS = 64


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def market_date_counts(frame: pd.DataFrame):
    """Source SAS event rows can occur on nontrading dates; require a return."""
    dates = pd.to_datetime(frame["date"], errors="raise")
    returns = pd.to_numeric(frame["retx"], errors="coerce").astype("float64")
    valid = np.isfinite(returns) & returns.ge(-1)
    return dates.value_counts(), dates.loc[valid].value_counts()


def _accumulate_counts(target, counts):
    for day, count in counts.items():
        target[day] = target.get(day, 0) + int(count)


def _save_calendar_evidence(cache_dir, all_counts, valid_counts):
    evidence = pd.DataFrame({"date": sorted(all_counts)})
    evidence["raw_source_rows"] = evidence["date"].map(all_counts).astype("int64")
    evidence["finite_economic_retx_rows"] = evidence["date"].map(valid_counts).fillna(0).astype("int64")
    evidence["is_market_date"] = evidence["finite_economic_retx_rows"].gt(0)
    evidence.to_parquet(cache_dir / "market_calendar_evidence.parquet", index=False)
    calendar = pd.DatetimeIndex(evidence.loc[evidence["is_market_date"], "date"])
    pd.DataFrame({"date": calendar}).to_parquet(cache_dir / "market_calendar.parquet", index=False)
    meta = {"calendar_rule": CALENDAR_RULE, "market_date_count": len(calendar),
        "source_date_count": len(evidence),
        "global_valid_return_rows": int(evidence["finite_economic_retx_rows"].sum()),
        "excluded_event_only_dates": evidence.loc[~evidence["is_market_date"], "date"].dt.strftime("%Y-%m-%d").tolist()}
    return calendar, meta


def _refresh_cached_calendar(source, cache_dir):
    all_counts, valid_counts = {}, {}
    for number, chunk in enumerate(pd.read_csv(source, compression="gzip", usecols=["date", "RETX"],
            dtype="string", chunksize=500_000)):
        chunk.columns = chunk.columns.str.lower()
        all_part, valid_part = market_date_counts(chunk)
        _accumulate_counts(all_counts, all_part)
        _accumulate_counts(valid_counts, valid_part)
        if number % 20 == 0:
            print(f"all-market calendar stream: {(number+1)*500_000:,} rows scanned", flush=True)
    return _save_calendar_evidence(cache_dir, all_counts, valid_counts)


def _unique_records(frame: pd.DataFrame, keys: list[str], values: list[str]):
    """Collapse exact duplicates; reject conflicting values at the same key."""
    duplicate_rows = int(frame.duplicated(keys, keep=False).sum())
    if not duplicate_rows:
        return frame, 0
    reduced = frame.drop_duplicates(keys + values)
    if reduced.duplicated(keys, keep=False).any():
        bad = reduced.loc[reduced.duplicated(keys, keep=False), keys]
        raise ValueError("Conflicting CRSP records at identical keys: " + bad.head().to_json(orient="records"))
    return reduced, len(frame) - len(reduced)


def monthly_features(monthly: pd.DataFrame, requests: pd.DataFrame) -> pd.DataFrame:
    """Compute annualized SD of exactly 60 consecutive monthly log changes."""
    frame = monthly.copy()
    frame["date"] = pd.to_datetime(frame["date"])
    frame["period"] = frame["date"].dt.to_period("M")
    frame["prc"] = pd.to_numeric(frame["prc"], errors="coerce").astype("float64")
    frame["cfacpr"] = pd.to_numeric(frame["cfacpr"], errors="coerce").astype("float64")
    valid = np.isfinite(frame["prc"]) & np.isfinite(frame["cfacpr"])
    valid &= frame["prc"].ne(0) & frame["cfacpr"].gt(0)
    frame["adjusted_price"] = np.where(valid, frame["prc"].abs() / frame["cfacpr"], np.nan)
    frame, _ = _unique_records(frame, ["permno", "period"], ["adjusted_price", "date"])
    groups = {int(key): data.set_index("period").sort_index() for key, data in frame.groupby("permno")}
    rows = []
    for req in requests.itertuples(index=False):
        cutoff = pd.Timestamp(req.datadate)
        end = cutoff.to_period("M") - 1
        months = pd.period_range(end=end, periods=61, freq="M")
        data = groups.get(int(req.permno))
        prices = np.full(61, np.nan) if data is None else data["adjusted_price"].reindex(months).to_numpy(float)
        with np.errstate(divide="ignore", invalid="ignore"):
            changes = np.diff(np.log(prices))
        n_valid = int(np.isfinite(changes).sum())
        complete = n_valid == 60
        rows.append({
            "event_id": str(req.event_id),
            "sigma60": float(np.std(changes, ddof=1) * np.sqrt(12)) if complete else np.nan,
            "n_month_returns": n_valid,
            "n_month_prices": int(np.isfinite(prices).sum()),
            "sigma60_complete": complete,
            "sigma60_price_start_month": str(months[0]),
            "sigma60_return_start_month": str(months[1]),
            "sigma60_end_month": str(months[-1]),
            "sigma60_failure": "" if complete else "requires_61_consecutive_valid_monthly_prices",
        })
    return pd.DataFrame(rows)


def daily_features(daily: pd.DataFrame, requests: pd.DataFrame, calendar) -> pd.DataFrame:
    """Use strict 255-market-date windows; metadata may use the fiscal date."""
    frame = daily.copy()
    frame["date"] = pd.to_datetime(frame["date"])
    for field in ["retx", "shrcd", "exchcd"]:
        frame[field] = pd.to_numeric(frame[field], errors="coerce").astype("float64")
    # CRSP SAS missing codes must not become economic returns.  A stock price
    # return below -100% is not economically admissible; it remains missing.
    frame.loc[~np.isfinite(frame["retx"]) | frame["retx"].lt(-1), "retx"] = np.nan
    frame, _ = _unique_records(frame, ["permno", "date"], ["retx", "shrcd", "exchcd"])
    groups = {int(key): data.set_index("date").sort_index() for key, data in frame.groupby("permno")}
    calendar = pd.DatetimeIndex(calendar).sort_values().unique()
    rows = []
    for req in requests.itertuples(index=False):
        cutoff = pd.Timestamp(req.datadate)
        position = int(calendar.searchsorted(cutoff, side="left"))
        dates = calendar[max(0, position - 255):position]
        data = groups.get(int(req.permno))
        returns = np.full(len(dates), np.nan) if data is None else data["retx"].reindex(dates).to_numpy(float)
        n_valid = int(np.isfinite(returns).sum())
        complete = len(dates) == 255 and n_valid == 255
        market_position = int(calendar.searchsorted(cutoff, side="right")) - 1
        last_market_date = calendar[market_position] if market_position >= 0 else pd.NaT
        latest = None
        if data is not None:
            history_position = int(data.index.searchsorted(cutoff, side="right")) - 1
            if history_position >= 0:
                latest = data.iloc[history_position]
                last_date = data.index[history_position]
            else:
                last_date = pd.NaT
        else:
            last_date = pd.NaT
        rows.append({
            "event_id": str(req.event_id),
            "retvol255": float(np.std(returns, ddof=1) * 100) if complete else np.nan,
            "n_daily_returns": n_valid,
            "n_market_days": len(dates),
            "retvol255_complete": complete,
            "retvol255_window_start": dates[0] if len(dates) else pd.NaT,
            "retvol255_window_end": dates[-1] if len(dates) else pd.NaT,
            "last_trade_date": last_date,
            "last_market_date_le_fye": last_market_date,
            "last_shrcd": latest["shrcd"] if latest is not None else np.nan,
            "last_exchcd": latest["exchcd"] if latest is not None else np.nan,
            "market_history_age_days": (cutoff - last_date).days if pd.notna(last_date) else np.nan,
            "retvol255_failure": "" if complete else "requires_255_valid_returns_on_preceding_market_dates",
        })
    return pd.DataFrame(rows)


def _daily_cache(source: Path, requests: pd.DataFrame, cache_parent: Path, source_sha: str):
    """Stream the full market date calendar, storing only requested securities."""
    permnos = sorted(requests["permno"].unique().tolist())
    signature = hashlib.sha256(json.dumps({"version": CACHE_LAYOUT, "source_sha256": source_sha,
        "permnos": permnos}, sort_keys=True).encode()).hexdigest()
    cache_dir = cache_parent / ("daily_" + signature[:20])
    meta_file = cache_dir / "cache_manifest.json"
    if meta_file.exists():
        meta = json.loads(meta_file.read_text(encoding="utf8"))
        if meta.get("complete") and meta.get("signature") == signature:
            if meta.get("calendar_rule") != CALENDAR_RULE:
                calendar, calendar_meta = _refresh_cached_calendar(source, cache_dir)
                meta.update(calendar_meta)
                meta_file.write_text(json.dumps(meta, indent=2)+"\n", encoding="utf8")
                return cache_dir, calendar, meta
            return cache_dir, pd.DatetimeIndex(pd.read_parquet(cache_dir / "market_calendar.parquet")["date"]), meta
    # An interrupted cache is never treated as complete or deleted recursively.
    if cache_dir.exists():
        cache_dir = cache_parent / ("daily_" + signature[:20] + "_" + str(time.time_ns()))
    cache_dir.mkdir(parents=True)
    schema = pa.schema([("permno", pa.int64()), ("date", pa.timestamp("ns")),
        ("retx", pa.float64()), ("shrcd", pa.float64()), ("exchcd", pa.float64())])
    writers = {}
    all_date_counts, valid_date_counts = {}, {}
    selected_rows = 0
    source_rows = 0
    wanted = set(permnos)
    began = time.monotonic()
    try:
        for number, chunk in enumerate(pd.read_csv(source, compression="gzip",
            usecols=["PERMNO", "date", "RETX", "SHRCD", "EXCHCD"], dtype="string", chunksize=500_000)):
            chunk.columns = chunk.columns.str.lower()
            chunk["date"] = pd.to_datetime(chunk["date"], errors="coerce")
            if chunk["date"].isna().any():
                raise ValueError("Missing or invalid source daily dates")
            all_part, valid_part = market_date_counts(chunk)
            _accumulate_counts(all_date_counts, all_part)
            _accumulate_counts(valid_date_counts, valid_part)
            source_rows += len(chunk)
            ids = pd.to_numeric(chunk["permno"], errors="coerce")
            chunk = chunk.loc[ids.isin(wanted)].copy()
            if len(chunk):
                chunk["permno"] = pd.to_numeric(chunk["permno"], errors="raise").astype("int64")
                for column in ["retx", "shrcd", "exchcd"]:
                    chunk[column] = pd.to_numeric(chunk[column], errors="coerce").astype("float64")
                selected_rows += len(chunk)
                bucket = chunk["permno"] % BUCKETS
                for key, data in chunk.groupby(bucket, sort=False):
                    key = int(key)
                    if key not in writers:
                        writers[key] = pq.ParquetWriter(cache_dir / f"bucket_{key:02d}.parquet", schema, compression="zstd")
                    table = pa.Table.from_pandas(data[schema.names], schema=schema, preserve_index=False)
                    writers[key].write_table(table)
            if number % 10 == 0:
                print(f"daily stream: {source_rows:,} raw rows, {selected_rows:,} selected rows", flush=True)
    finally:
        for writer in writers.values():
            writer.close()
    calendar, calendar_meta = _save_calendar_evidence(cache_dir, all_date_counts, valid_date_counts)
    meta = {"version": VERSION, "signature": signature, "source": str(source),
        "source_sha256": source_sha, "requested_permno_count": len(permnos),
        "source_rows": source_rows, "cached_rows": selected_rows,
        "market_date_count": len(calendar), "elapsed_seconds": time.monotonic()-began,
        "complete": True, **calendar_meta}
    meta_file.write_text(json.dumps(meta, indent=2)+"\n", encoding="utf8")
    return cache_dir, calendar, meta


def build_market_inputs(requests_path, raw_dir, output_path, audit_dir):
    """Build requested market inputs and persist window/provenance audits."""
    requests_path, raw_dir = Path(requests_path), Path(raw_dir)
    output_path, audit_dir = Path(output_path), Path(audit_dir)
    audit_dir.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    requests = pd.read_parquet(requests_path)
    required = {"event_id", "gvkey", "fyear", "datadate", "permno"}
    if not required.issubset(requests.columns):
        raise ValueError(f"Missing request columns: {required-set(requests.columns)}")
    requests = requests[list(sorted(required))].copy()
    requests["event_id"] = requests["event_id"].astype(str)
    if requests["event_id"].duplicated().any():
        raise ValueError("event_id must be unique")
    requests["datadate"] = pd.to_datetime(requests["datadate"], errors="raise")
    requests["permno"] = pd.to_numeric(requests["permno"], errors="raise").astype("int64")
    if requests["datadate"].isna().any() or requests["permno"].le(0).any():
        raise ValueError("Invalid request date or PERMNO")
    if not len(requests):
        raise ValueError("No market requests supplied")
    daily_source, monthly_source = raw_dir / DAILY_FILE, raw_dir / MONTHLY_FILE
    source_sha = {"daily": sha256_file(daily_source), "monthly": sha256_file(monthly_source),
                  "requests": sha256_file(requests_path)}
    monthly = pd.read_csv(monthly_source, compression="gzip", usecols=["PERMNO", "date", "PRC", "CFACPR"], dtype="string")
    monthly.columns = monthly.columns.str.lower()
    monthly["permno"] = pd.to_numeric(monthly["permno"], errors="coerce")
    monthly = monthly.loc[monthly["permno"].isin(requests["permno"])].copy()
    monthly["permno"] = monthly["permno"].astype("int64")
    print(f"monthly source selected {len(monthly):,} records", flush=True)
    mfeatures = monthly_features(monthly, requests)
    mfeatures.to_parquet(audit_dir / "monthly_features.parquet", index=False)
    del monthly
    gc.collect()
    cache_dir, calendar, cache_meta = _daily_cache(daily_source, requests,
        output_path.parent / "market_cache", source_sha["daily"])
    evidence = pd.read_parquet(cache_dir / "market_calendar_evidence.parquet")
    evidence.to_csv(audit_dir / "market_calendar_evidence.csv", index=False)
    evidence.loc[~evidence["is_market_date"]].to_csv(audit_dir / "excluded_event_only_dates.csv", index=False)
    evidence.loc[evidence["is_market_date"], ["date"]].to_csv(audit_dir / "corrected_market_calendar.csv", index=False)
    daily_results = []
    for bucket, subrequests in requests.groupby(requests["permno"] % BUCKETS):
        path = cache_dir / f"bucket_{int(bucket):02d}.parquet"
        if path.exists():
            frame = pd.read_parquet(path)
        else:
            frame = pd.DataFrame(columns=["permno", "date", "retx", "shrcd", "exchcd"])
        daily_results.append(daily_features(frame, subrequests, calendar))
        del frame
        gc.collect()
    dfeatures = pd.concat(daily_results, ignore_index=True)
    output = requests[["event_id", "gvkey", "fyear", "datadate", "permno"]].merge(
        mfeatures, on="event_id", how="left", validate="one_to_one").merge(
        dfeatures, on="event_id", how="left", validate="one_to_one")
    assert len(output) == len(requests) and output["event_id"].is_unique
    assert (output["last_trade_date"].isna() | (output["last_trade_date"] <= output["datadate"])).all()
    assert (output["retvol255_window_end"].isna() | (output["retvol255_window_end"] < output["datadate"])).all()
    output.to_parquet(output_path, index=False)
    failed = output.loc[~output["sigma60_complete"] | ~output["retvol255_complete"]]
    failed.to_csv(audit_dir / "incomplete_market_windows.csv", index=False)
    summary = {"version": VERSION, "requests": str(requests_path), "output": str(output_path),
        "source_sha256": source_sha, "output_sha256": sha256_file(output_path),
        "request_rows": len(requests), "output_rows": len(output),
        "requested_permnos": int(requests["permno"].nunique()),
        "sigma60_complete": int(output["sigma60_complete"].sum()),
        "retvol255_complete": int(output["retvol255_complete"].sum()),
        "both_complete": int((output["sigma60_complete"] & output["retvol255_complete"]).sum()),
        "no_historical_security_record": int(output["last_trade_date"].isna().sum()),
        "cache": cache_meta,
        "conventions": {"monthly": "61 consecutive monthly abs(PRC)/CFACPR prices; 60 log changes strictly before fiscal-end month; ddof=1; annualize sqrt(12)",
            "daily": "255 full-market trading dates strictly before datadate; RETX sample sd ddof=1 times100; no annualization or backfilling",
            "market_calendar": CALENDAR_RULE,
            "security_metadata": "Last CRSP daily observation <= datadate; last_trade_date names an observation, not proof of a trade",
            "return_missing": "Nonnumeric codes/nonfinite and RETX<-1 remain missing"},
        "regressions_run": False}
    (audit_dir / "market_build_summary.json").write_text(json.dumps(summary, indent=2)+"\n", encoding="utf8")
    print(json.dumps({key: summary[key] for key in ["output_rows", "sigma60_complete", "retvol255_complete", "both_complete"]}), flush=True)
    return output


def main():
    base = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requests", type=Path, default=base / "data/interim/market_requests.parquet")
    parser.add_argument("--raw-dir", type=Path, default=base / "data/raw/crsp")
    parser.add_argument("--output", type=Path, default=base / "data/interim/market_inputs.parquet")
    parser.add_argument("--audit-dir", type=Path, default=base / "data/audit/market_inputs")
    args = parser.parse_args()
    build_market_inputs(args.requests, args.raw_dir, args.output, args.audit_dir)


if __name__ == "__main__":
    main()
