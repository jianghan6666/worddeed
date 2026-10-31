import csv,gzip,json,hashlib,pathlib,sys,collections
base=pathlib.Path(sys.argv[1])
out={}
for f in sorted(base.glob('*.csv.gz')):
 h=hashlib.sha256()
 with f.open('rb') as z:
  for b in iter(lambda:z.read(1024*1024),b''):h.update(b)
 counts=collections.Counter(); n=0;bad=0
 with gzip.open(f,'rt',encoding='utf-8-sig',newline='') as g:
  r=csv.DictReader(g); cols=r.fieldnames
  for row in r:
   n+=1;bad+=int(None in row);counts[row.get('year','')]+=1
 out[f.name]={'bytes':f.stat().st_size,'sha256':h.hexdigest(),'rows':n,'columns':cols,'column_count':len(cols),'year_counts':dict(sorted(counts.items())),'malformed_rows':bad,'gzip_read_to_eof':True}
(base/'validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(out,ensure_ascii=False))
