"""Verify all25 own-model panels of frozen Excel and optional new replay.

Reads XLSX XML; never opens or authors the workbook. Python stdlib only.
Published-paper sheet1 remains a manually transcribed reference, not an estimate.
"""
from pathlib import Path
import argparse,csv,hashlib,json,math,re,sys,zipfile
import xml.etree.ElementTree as ET
NS={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

def close(a,b,tol=1e-12):
    return math.isclose(float(a),float(b),rel_tol=tol,abs_tol=tol)

def readcsv(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as stream:
        return list(csv.DictReader(stream))

def workbook(path):
    with zipfile.ZipFile(path) as archive:
        strings=[]
        if 'xl/sharedStrings.xml' in archive.namelist():
            strings=[''.join(t.itertext()) for t in ET.fromstring(
                archive.read('xl/sharedStrings.xml')).findall('s:si',NS)]
        rels={e.attrib['Id']:e.attrib['Target'] for e in ET.fromstring(
            archive.read('xl/_rels/workbook.xml.rels'))}
        wb=ET.fromstring(archive.read('xl/workbook.xml'))
        styles=ET.fromstring(archive.read('xl/styles.xml'))
        formats={int(e.attrib['numFmtId']):e.attrib['formatCode'] for e in
                 styles.findall('s:numFmts/s:numFmt',NS)}
        xfs=styles.findall('s:cellXfs/s:xf',NS);sheets={}
        for sheet in wb.findall('s:sheets/s:sheet',NS):
            name=sheet.attrib['name']
            rid=sheet.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']
            target=rels[rid]
            target=target.lstrip('/') if target.startswith('/') else 'xl/'+target
            cells={}
            for cell in ET.fromstring(archive.read(target)).findall('.//s:sheetData/s:row/s:c',NS):
                val=cell.find('s:v',NS);typ=cell.attrib.get('t');addr=cell.attrib['r']
                if typ=='inlineStr':
                    inline=cell.find('s:is',NS)
                    value=''.join(inline.itertext()) if inline is not None else None
                elif typ=='s' and val is not None:
                    value=strings[int(val.text)]
                elif val is not None:
                    value=val.text if typ in ['str','e'] else float(val.text)
                else:
                    value=None
                fmt=formats.get(int(xfs[int(cell.attrib.get('s',0))].attrib['numFmtId']),'')
                stars=max([len(x) for x in re.findall(r'\*+',fmt.replace(chr(92),''))] or [0])
                cells[addr]={'value':value,'stars':stars}
            sheets[name]=cells
    return sheets

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workbook',type=Path,required=True)
    parser.add_argument('--payload',type=Path,required=True)
    parser.add_argument('--generated',type=Path,
                        help='Optional new regression directory to compare to Excel')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    payload=json.loads(args.payload.read_text(encoding='utf-8-sig'))
    sheets=workbook(args.workbook);newcoef={};newmeta={};newspec={}
    if args.generated:
        newcoef={(r['model_id'],r['term']):r for r in readcsv(args.generated/'stata/coefficients.csv')}
        newmeta={r['model_id']:r for r in readcsv(args.generated/'stata/model_summary.csv')}
        newspec={r['model_id']:r for r in json.loads((args.generated/'model_specifications.json').read_text(encoding='utf8'))['models']}
    numeric=[];footers=[];panels=[];newchecks=[]
    for name,table in [('2 Replication',payload['tables'][1]),
                       ('3 No actual RD',payload['tables'][2]),
                       ('4 With actual RD',payload['tables'][3])]:
        cells=sheets[name]
        avalues={int(re.search(r'\d+',a).group()):v['value'] for a,v in cells.items() if re.fullmatch(r'A\d+',a)}
        starts=[]
        for panel in table['panels']:
            hits=[r for r,v in avalues.items() if v==panel['title']]
            assert len(hits)==1,(name,panel['title'],hits)
            starts.append(hits[0])
        for pi,panel in enumerate(table['panels']):
            start=starts[pi];end=starts[pi+1] if pi+1<len(starts) else max(avalues)+1
            for row in panel['rows']:
                hits=[r for r,v in avalues.items() if v==row['label'] and start<r<end]
                assert len(hits)==1,(name,row['term'],hits)
                rix=hits[0]
                for ci,expected in enumerate(row['cells']):
                    if expected is None:
                        continue
                    col=chr(ord('B')+ci)
                    for offset,field in [(0,'coef'),(1,'stat')]:
                        addr=f'{col}{rix+offset}';cell=cells[addr]
                        assert close(cell['value'],expected[field]),(name,addr,field)
                        if offset==0:
                            assert cell['stars']==expected['stars'],(name,addr,'stars')
                        numeric.append({'sheet':name,'cell':addr,'model_id':expected['model_id'],
                                        'term':row['term'],'kind':field})
                    if args.generated:
                        new=newcoef[(expected['model_id'],row['term'])]
                        assert close(new['coef'],expected['coef'],tol=1e-5)
                        assert close(new['se_cluster'],expected['stat'],tol=1e-5)
                        p=float(new['p_cluster']);star=3 if p<.01 else 2 if p<.05 else 1 if p<.1 else 0
                        assert star==expected['stars']
                        newchecks.append({'model_id':expected['model_id'],'term':row['term'],
                                          'coef_SE_and_stars_agree':True})
            for footer in panel['footer_rows']:
                hits=[r for r,v in avalues.items() if v==footer['label'] and start<r<end]
                assert len(hits)==1,(name,footer['label'],hits)
                rix=hits[0]
                for ci,expected in enumerate(footer['cells']):
                    addr=f'{chr(ord("B")+ci)}{rix}';actual=cells[addr]['value']
                    assert close(actual,expected) if isinstance(expected,(int,float)) else actual==expected
                    mid=panel['columns'][ci]['model_id']
                    footers.append({'sheet':name,'cell':addr,'model_id':mid,'label':footer['label']})
                    if args.generated:
                        value=None
                        if footer['label']=='N':value=float(newmeta[mid]['N_oim'])
                        if footer['label']=='Firm clusters':value=float(newmeta[mid]['N_clusters'])
                        if footer['label']=='Log likelihood':value=float(newmeta[mid]['ll_oim'])
                        if footer['label']=='Pseudo R2':value=1-float(newmeta[mid]['ll_oim'])/newspec[mid]['ll_null']
                        if value is not None:
                            assert close(value,expected,tol=1e-5),(mid,footer['label'],value,expected)
            panels.append({'sheet':name,'panel':panel['title'],
                           'models':[c['model_id'] for c in panel['columns']]})
    report={'passed':True,'workbook_sha256':hashlib.sha256(args.workbook.read_bytes()).hexdigest(),
            'own_model_panels':len(panels),'model_count':len({m for p in panels for m in p['models']}),
            'numeric_coefficient_SE_cells':len(numeric),'footer_cells':len(footers),
            'all_coefficient_SE_and_stars_match_payload':True,
            'new_replay_compared':bool(args.generated),'new_replay_core_terms':len(newchecks),
            'panels':panels,'checks':newchecks,
            'note':'Paper reference sheet1 and Excel ModelData sheet are not new regressions.'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k not in ['panels','checks']},indent=2))

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('Presentation check failed: '+str(exc),file=sys.stderr)
        sys.exit(1)
