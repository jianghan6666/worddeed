"""Losslessly project the raw transcript identity fields used by matching.

The supplied identity projection is sufficient for the matching stages. This
optional exporter documents exactly how it was made from the upstream transcript
snapshot; the speech corpus is not needed for frozen-score replication.
"""
from pathlib import Path
import argparse, hashlib, json
import pandas as pd

COLS=['orig_row','companyid','transcriptid','transcriptpersonid','directorid',
      'transcriptpersonname','execid','exec_fullname','companyname_execucomp',
      'companyname','mostimportantdateutc','year','retained_word_count','proid']

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source-pickle',required=True,type=Path)
    ap.add_argument('--output',required=True,type=Path)
    args=ap.parse_args()
    source=args.source_pickle.resolve();dest=args.output.resolve()
    if dest.exists():raise FileExistsError('Exporter never overwrites an existing output: '+str(dest))
    raw=pd.read_pickle(source)
    selected=raw[COLS].copy()
    assert raw.orig_row.is_unique and len(selected)==len(raw)
    dest.parent.mkdir(parents=True,exist_ok=True)
    selected.to_pickle(dest,compression={'method':'gzip','compresslevel':6,'mtime':0})
    got=pd.read_pickle(dest)
    pd.testing.assert_frame_equal(selected,got,check_exact=True)
    info={'status':'passed','source_filename':source.name,'source_sha256':sha(source),
          'source_bytes':source.stat().st_size,'source_rows':len(raw),
          'source_columns':len(raw.columns),'rows':len(got),'columns':COLS,
          'output_sha256':sha(dest),'output_bytes':dest.stat().st_size,
          'dtypes':got.dtypes.astype(str).to_dict(),
          'all_rows_retained':True,'row_order_preserved':True,
          'values_dtypes_index_exact':True,'no_aggregation_or_match_flags':True,
          'date_storage':'Raw mixed string/Timestamp objects retained exactly.'}
    dest.with_name(dest.name+'.metadata.json').write_text(json.dumps(info,indent=2),encoding='utf8')
    print(json.dumps(info,indent=2))

if __name__=='__main__':main()
