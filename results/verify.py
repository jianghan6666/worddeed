"""Verify preserved result bytes and reviewer-browser completeness (standard library)."""
import argparse,csv,hashlib,io,json,math,re,zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PREFIX='nbm-full-results-2026-10-31/results/'


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path);args=p.parse_args()
    archive=zipfile.ZipFile(args.archive) if args.archive else None
    def data(name):return archive.read(PREFIX+name) if archive else (ROOT/name).read_bytes()
    def exists(name):return PREFIX+name in archive.namelist() if archive else (ROOT/name).exists()
    def load(name):return json.loads(data(name))
    def rows(name):return list(csv.DictReader(io.StringIO(data(name).decode('utf-8-sig'))))
    manifest=load('MANIFEST.json')
    for row in manifest['files']:
        payload=data(row['path'])
        if len(payload)!=row['bytes'] or hashlib.sha256(payload).hexdigest()!=row['sha256']:
            raise ValueError('Result identity mismatch: '+row['path'])
    topics=load('step1/catalogue.json')['topics'];assert len(topics)==354
    record_index=load('step2/READER_INDEX.json');assert len(record_index)==144
    assert len({x['path'] for x in record_index})==95
    totals={v:{k:0 for k in ['relevant','irrelevant','unresolved']} for v in ['primary','supplementary']}
    trials=sorted({x['trial_id'] for x in record_index});assert len(trials)==12
    for trial in trials:
        text=data('step2/explorers/'+trial+'.html').decode()
        embedded=json.loads(re.search(r'<script type="application/json" id="payload">(.*?)</script>',text,re.S).group(1))
        assert embedded['topics']==topics
        for variant in totals:
            selection=load(f'step2/analyses/{variant}/handoffs/{trial}/selected_topics.json')['final']
            sets=[set(selection[k]) for k in totals[variant]]
            assert len(set.union(*sets))==354 and sum(map(len,sets))==354
            for key in selection:totals[variant][key]+=len(selection[key])
            assert embedded['majorities'][variant]==rows(f'step2/analyses/{variant}/handoffs/{trial}/topic_labels.csv')
            for r in record_index:
                if r['trial_id']==trial and r['variant']==variant:
                    assert embedded['records'][variant][r['stage']][r['reader_id']]==load(r['path'])
    assert totals['primary']=={'relevant':3795,'irrelevant':452,'unresolved':1}
    assert totals['supplementary']=={'relevant':3796,'irrelevant':452,'unresolved':0}
    selected=data('step2/analyses/primary/handoffs/b1-gpt-6-astra-P0-xhigh/selected_topics.json')
    assert selected==data('step3/selected_topics.json')
    scores=rows('step3/results/risk_scores.csv');assert len(scores)==29506
    assert len({r['panel_id'] for r in scores})==29506
    scorecols=[k for k in scores[0] if k.startswith('risk_score_')];assert len(scorecols)==16
    assert all(math.isfinite(float(r[k])) for r in scores for k in scorecols)
    models=rows('step4/full/estimates/model_summary.csv');assert len(models)==25
    assert len({r['model_id'] for r in models})==25 and all(r['status']=='success' for r in models)
    coefficients=rows('step4/full/estimates/coefficients.csv');assert len(coefficients)==1799
    scorecoef=[r for r in coefficients if r['term']=='rd_score'];assert len(scorecoef)==16
    assert all(float(r['coef'])<0 and float(r['p_cluster'])<.01 for r in scorecoef)
    evidence=load('EVIDENCE_MANIFEST.json');extra=0
    if archive or (ROOT/'reader-evidence').exists():
        for row in evidence['files']:
            payload=data(row['path'])
            assert len(payload)==row['bytes'] and hashlib.sha256(payload).hexdigest()==row['sha256'],row['path']
            extra+=1
    # Check only the newly authored reading paths; historical copies keep original links.
    pages=['report.html','step2/explorers/index.html']+['step2/explorers/'+t+'.html' for t in trials]
    for page in pages:
        for target in re.findall(r'(?:href|src)="([^"#]+)"',data(page).decode()):
            if '://' in target or target.startswith('data:'):continue
            from posixpath import normpath,join,dirname
            resolved=normpath(join(dirname(page),target))
            assert exists(resolved),(page,target)
    print(json.dumps({'passed':True,'browsable_files_verified':len(manifest['files']),
                     'additional_evidence_files_verified':extra,'topics':354,'trials':12,
                     'indexed_reader_positions':144,'distinct_reader_records':95,
                     'handoffs':24,'firm_year_scores':29506,'score_columns':16,
                     'model_specifications':25,'coefficient_rows':1799,
                     'scope':'Identity and packaging checks; no new empirical estimation.'},indent=2))
    if archive:archive.close()


if __name__=='__main__':main()
