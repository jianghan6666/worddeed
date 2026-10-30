"""第 1 步：component 级数据 -> firm-year 输入表。

输入：data/components/components.parquet、data/components/topic_distr.npz、data/compustat/compustat_panel_firms.csv
输出：<out>/firm_year_inputs.parquet（默认 rerun/，不覆盖包内交付的 data/firm_year_inputs.parquet）

用法（包根目录）：python code/01_build_inputs.py [--out rerun]
耗时约 1–2 分钟，峰值内存约 6GB。
"""

import argparse
import time
from pathlib import Path

import step3_lib as L


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(L.ROOT / "rerun"))
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    panel = L.build_inputs(L.DATA / "components" / "components.parquet", L.DATA / "components" / "topic_distr.npz",
                           L.DATA / "compustat" / "compustat_panel_firms.csv")
    panel.to_parquet(out / "firm_year_inputs.parquet", index=False)
    print(f"已写入 {out / 'firm_year_inputs.parquet'}：{panel.shape}，{time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
