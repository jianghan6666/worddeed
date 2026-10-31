"""Render all25 new Stata fits into standalone HTML and Markdown (stdlib only)."""
from pathlib import Path
import argparse,csv,json,html,math

ROWS=[('rd_score','Predicted synthetic proxy of CEO risk preference (clipped0, pp)'),
      ('cash_m','CEO cash compensation ($m)'),('inside_debt_m','CEO inside debt ($m)'),
      ('ln_rellev','Log CEO relative leverage'),('high_rellev','High relative leverage'),
      ('equity_m','CEO equity wealth ($m)'),('vega_k','CEO Vega ($000 /1pp volatility)'),
      ('age','CEO age (years)'),('ln_tenure','Log CEO tenure'),
      ('rd_at_pct','Actual R&D/assets (pp)'),('rd_missing','R&D missing indicator'),
      ('capx_at_pct','CAPEX/assets (pp)'),('asset_growth','Asset growth (ratio)'),
      ('mb','Market/book'),('profitability_m','Profitability ($m)'),
      ('size_pct','Size percentile'),('re_at','Retained earnings/assets (ratio)'),
      ('retvol255','Daily return volatility (pp)'),('_cons','Constant')]

def read(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as stream:
        return list(csv.DictReader(stream))

def fmt(value):
    value=float(value)
    return f'{value:.3e}' if 0<abs(value)<0.00005 else f'{value:.4f}'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--generated',type=Path,required=True,
                        help='Generated regression directory with stata/ and model_specifications.json')
    args=parser.parse_args();base=args.generated
    specs=json.loads((base/'model_specifications.json').read_text(encoding='utf8'))['models']
    rows=read(base/'stata/coefficients.csv');coeff={(r['model_id'],r['term']):r for r in rows}
    summary={r['model_id']:r for r in read(base/'stata/model_summary.csv')}
    assert len(summary)==25 and all(r['status']=='success' for r in summary.values())
    groups=[]
    for period in ['original_2006_2011','extended_2006_2023','new_2013_2023']:
        groups.append(('Replication, annual CEO B, '+period.replace('_',' '),
                       [s for s in specs if s['table_group']=='replication' and s['period']==period]))
    for group in ['no_rd','with_rd']:
        for algorithm in ['xgboost','ridge']:
            groups.append((group.replace('_',' ')+'; '+algorithm+';2013-2023',
                           [s for s in specs if s['table_group']==group and s['score_model']==algorithm]))
    md=['# Replayed Table 4 results','',
        'These tables were generated from the newly reconstructed data and new Stata fits. '
        'The source workbook is a separate frozen reference. The original published-paper '
        'panel is not re-estimated.','',
        'Logit coefficients; parentheses are GVKEY firm-cluster standard errors '
        '(CR0 × G/(G−1)). Stars: *** p<.01, ** p<.05, * p<.10; normal two-sided Wald tests. '
        'All models include separate SIC2 and fiscal-year dummies and an intercept. '
        'No Delta/Vega regressor, no PCEO, no firm/CEO fixed effects.','']
    htmlparts=[]
    for title,models in groups:
        headers=[s['setting'].replace('m00','No debt/Vega').replace('m0','(').replace('m10','(10')
                 +(')' if s['setting']!='m00' else '') for s in models]
        matrix=[]
        for term,label in ROWS:
            if not any((s['model_id'],term) in coeff for s in models):
                continue
            values=[]
            for s in models:
                c=coeff.get((s['model_id'],term))
                if c is None:
                    values.append('');continue
                p=float(c['p_cluster']);star='***' if p<.01 else '**' if p<.05 else '*' if p<.1 else ''
                values.append(fmt(c['coef'])+star+' ('+fmt(c['se_cluster'])+')')
            matrix.append([label]+values)
        for label,field in [('N','N_oim'),('Firm clusters','N_clusters')]:
            matrix.append([label]+[f'{int(float(summary[s["model_id"]][field])):,}' for s in models])
        matrix.append(['Log likelihood']+[fmt(summary[s['model_id']]['ll_oim']) for s in models])
        matrix.append(['Pseudo R2']+[fmt(1-float(summary[s['model_id']]['ll_oim'])/s['ll_null']) for s in models])
        matrix.append(['Industry/Year FE']+['Yes/Yes']*len(models))
        md+=['## '+title,'','| Variable | '+' | '.join(headers)+' |',
             '|---|'+'---:|'*len(models)]
        md+=['| '+' | '.join(row)+' |' for row in matrix];md+=['']
        h='<h2>'+html.escape(title)+'</h2><table><thead><tr>'+''.join(
            '<th>'+html.escape(x)+'</th>' for x in ['Variable']+headers)+'</tr></thead><tbody>'
        h+=''.join('<tr>'+''.join('<td>'+html.escape(x)+'</td>' for x in row)+'</tr>' for row in matrix)
        htmlparts.append(h+'</tbody></table>')
    dest=base/'tables';dest.mkdir(exist_ok=True)
    (dest/'REPLAYED_TABLES.md').write_text('\n'.join(md),encoding='utf8')
    intro='<h1>Replayed Table 4 results</h1><p>'+html.escape(md[2])+'</p><p>'+html.escape(md[4])+'</p>'
    (dest/'REPLAYED_TABLES.html').write_text('<!doctype html><meta charset="utf-8"><title>Replayed Table 4 results</title>'
        '<style>body{font:16px Arial,sans-serif;max-width:1200px;margin:36px auto;padding:0 20px;color:#203040}'
        'table{border-collapse:collapse;width:100%;margin-bottom:32px}th,td{padding:7px 12px;border-bottom:1px solid #ddd;text-align:right}'
        'th:first-child,td:first-child{text-align:left}th{background:#edf2f7}p{line-height:1.5}</style>'
        +intro+''.join(htmlparts),encoding='utf8')
    print(json.dumps({'tables':len(groups),'models':len(summary),'output':str(dest)},indent=2))

if __name__=='__main__':
    main()
