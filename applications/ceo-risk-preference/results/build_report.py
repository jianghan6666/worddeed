"""Render the results report and topic readers from the preserved result files.

Requires reportlab. No scientific estimation or model calls are performed.
"""
from pathlib import Path
import csv,json,html,math
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.graphics.shapes import Drawing, Line, Circle, String, Rect
from reportlab.graphics import renderSVG

ROOT=Path(__file__).resolve().parent
NAVY='#183C47';TEAL='#147D82';ORANGE='#C76B37';GRAY='#60747A';LIGHT='#E7EEF0'
def readcsv(path):
 with (ROOT/path).open(encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def load(path):return json.loads((ROOT/path).read_text())
counts=readcsv('step2/analyses/primary/trial_selection_counts.csv')
metrics=load('step3/results/metrics.json')
robust=readcsv('step3/results/seed_robustness_metrics.csv')
coef=readcsv('step4/full/estimates/coefficients.csv')
models=readcsv('step4/full/estimates/model_summary.csv')
scorecoef={r['model_id']:r for r in coef if r['term']=='rd_score'}
assert len(models)==25 and len(scorecoef)==16
assert all(float(r['coef'])<0 and float(r['p_cluster'])<.01 for r in scorecoef.values())
efforts={'medium':0,'high':1,'xhigh':2}
trials=sorted({r['trial_id'] for r in counts},key=lambda t:('6.1' in t,efforts[t.rsplit('-',1)[1]],t[:2]))
lookup={(r['trial_id'],r['stage']):r for r in counts}

def short(t):return ('Sol 6.1' if '6.1' in t else 'Astra')+' / '+t.rsplit('-',1)[1]+' / '+t[1]
def txt(d,x,y,s,size=9,color=GRAY,anchor='start'):
 d.add(String(x,y,s,fontName='Helvetica',fontSize=size,fillColor=colors.HexColor(color),textAnchor=anchor))

def screening_chart():
 d=Drawing(480,292);left=142;right=468;bottom=28;top=265
 for n in [0,100,200,300,354]:
  x=left+(right-left)*n/354;d.add(Line(x,bottom,x,top,strokeColor=colors.HexColor(LIGHT)))
  txt(d,x,12,str(n),8,anchor='middle')
 for i,t in enumerate(trials):
  y=top-12-i*19
  a=int(lookup[t,'initial_descriptor']['selected_N']);b=int(lookup[t,'source_review']['selected_N'])
  x1=left+(right-left)*a/354;x2=left+(right-left)*b/354
  txt(d,left-10,y-3,short(t),8,anchor='end')
  d.add(Line(x1,y,x2,y,strokeColor=colors.HexColor('#C6D6D9'),strokeWidth=2))
  d.add(Circle(x1,y,3,fillColor=colors.HexColor(ORANGE),strokeColor=None))
  d.add(Circle(x2,y,3,fillColor=colors.HexColor(TEAL),strokeColor=None))
  txt(d,x1-7,y-3,str(a),7,ORANGE,anchor='end');txt(d,x2+6,y-3,str(b),7,TEAL)
 txt(d,142,283,'Descriptor reading',9,ORANGE);txt(d,290,283,'Source review (primary)',9,TEAL)
 return d

def fit_chart():
 d=Drawing(480,152)
 for i,name in enumerate(['ridge','xgboost']):
  y=95-i*58;v=metrics['models'][name]['crossfit']['r2']
  txt(d,82,y+8,name.title(),10,NAVY,anchor='end')
  d.add(Rect(98,y,315,24,fillColor=colors.HexColor(LIGHT),strokeColor=None))
  d.add(Rect(98,y,315*v,24,fillColor=colors.HexColor(TEAL if i==1 else NAVY),strokeColor=None))
  txt(d,98+315*v+8,y+7,f'{v:.4f}',11,NAVY)
 txt(d,98,15,'Cross-fitted R-squared (scale 0 to 1)',9,GRAY)
 return d

def coef_chart():
 d=Drawing(480,330);left=184;right=465;lo=-.43;hi=.02
 sx=lambda v:left+(right-left)*(v-lo)/(hi-lo)
 for v in [-.4,-.3,-.2,-.1,0]:
  x=sx(v);d.add(Line(x,29,x,315,strokeColor=colors.HexColor(LIGHT if v else GRAY)))
  txt(d,x,13,f'{v:.1f}',8,anchor='middle')
 for i,(mid,r) in enumerate(scorecoef.items()):
  y=305-i*17;b=float(r['coef']);se=float(r['se_cluster'])
  label=mid.replace('score_','').replace('xgboost','XGB').replace('ridge','Ridge').replace('_no_rd_',' / no R&D / ').replace('_with_rd_',' / + R&D / ').replace('_rd_',' / + R&D / ')
  color=TEAL if 'xgboost' in mid else ORANGE
  txt(d,left-8,y-3,label,8,NAVY,anchor='end')
  d.add(Line(sx(b-1.96*se),y,sx(b+1.96*se),y,strokeColor=colors.HexColor(color),strokeWidth=1.3))
  d.add(Circle(sx(b),y,2.5,fillColor=colors.HexColor(color),strokeColor=None))
 return d

figures={'screening':screening_chart(),'fit':fit_chart(),'coefficients':coef_chart()}
(ROOT/'figures').mkdir(exist_ok=True)
for name,d in figures.items():renderSVG.drawToFile(d,str(ROOT/'figures'/f'{name}.svg'))

trialtable=[['Requested model / effort / repetition','Stage A','Stage B','Unresolved']]
for t in trials:
 a,b=lookup[t,'initial_descriptor'],lookup[t,'source_review']
 trialtable.append([short(t),a['selected_N'],b['selected_N'],b['unresolved_N']])
metricstable=[['Delivered metric','Ridge','XGBoost']]
for key,label,fmt in [('r2','Cross-fitted R-squared','.4f'),('mse','Mean squared error','.6f'),('corr','Correlation with target','.4f')]:
 metricstable.append([label,*[format(metrics['models'][m]['crossfit'][key],fmt) for m in ['ridge','xgboost']]])
robusttable=[['Seed','Model','Training N','Test N','Test R-sq','OOF comparison R-sq']]
for r in robust:robusttable.append([r['seed'],r['model'],r['n_train'],r['n_test'],f"{float(r['test_r2']):.4f}",f"{float(r['crossfit_same_test_r2']):.4f}"])
modeltable=[['Model ID','N used','Firms','Score coef','Clustered SE']]
for r in models:
 c=scorecoef.get(r['model_id']);modeltable.append([r['model_id'],r['N_cluster'],r['N_clusters'],f"{float(c['coef']):.4f}" if c else 'See full table',f"{float(c['se_cluster']):.4f}" if c else '-'])

sections=[
 {'tag':'READING GUIDE','title':'AI Microfoundation Proxy','paras':[
 'Full results | CEO speech, R&D prediction and dividend policy | 31 October 2026',
 'This report brings together the existing empirical results for all four steps. It preserves the supplied scientific specification and distinguishes reported findings, archived evidence and unresolved questions. It is a results publication; the companion replication package documents computational reruns.',
 'The central score is text-predicted R&D divided by assets. It is a candidate behavioral proxy. Predictive fit and regression significance alone do not establish that it measures psychological risk preference.'],
 'table':[['Step','What is reported'],['1. Represent','354 topics; original descriptions, training metadata and catalogue'],['2. Screen','12 trials, 36 readers; both stages, missingness and recoveries'],['3. Predict','29,506 firm-year scores; Ridge/XGBoost and six robustness runs'],['4. Assess','25 downstream models, including 16 score specifications']],
 'after':['Read the report first. Then open the step folders for full CSV/JSON outputs and original Excel workbooks. Every retained result is indexed with a SHA-256 fingerprint. The complete results ZIP additionally includes the 3,840-file original reader-evidence archive, already expanded for inspection.',
 'Scope: the completed 21 October screening pilot and empirical packages delivered on 27 October 2026. Earlier design proposals and the 19 October pilot are not substituted for this completed application.']},
 {'tag':'STEP 1 / REPRESENT','title':'An existing 354-topic representation','paras':[
 'The supplied BERTopic model was trained on 887,488 speech components with nonmissing political-donation ideology scores, drawn from a 5,765,638-component 2013-2023 corpus. That historical training sample is not restricted to CEOs.',
 'The saved model contains 354 substantive topics (IDs 0-353), plus outlier class -1. There are 482,860 outlier training components (54.4%). The current application uses 1,775,355 CEO-tagged components and the supplied topic densities.'],
 'table':[['Component','Delivered setting or output'],['Embedding','all-mpnet-base-v2; 768 dimensions'],['UMAP','15 neighbors; 5 dimensions; cosine; random_state 42'],['HDBSCAN','min_cluster_size 120; min_samples 100; eom'],['Topic descriptors','Names, sizes, keywords, representatives; Excel and CSV'],['Model artifacts','topics.json and configuration retained in this results package']],
 'after':['The safetensors save does not preserve the fitted UMAP and HDBSCAN objects. A new training run can produce a different topic system; it is not a way to recover missing historical ordering evidence.',
 'The historical density matrix has no embedded row identities or model/column fingerprint. Its ordering remains delivery-declared. Text joins and subsequent input checks should not be described as independent authentication of that historical matrix.'],
 'links':[('Topic descriptions workbook','step1/topic_descriptions_354Topics.xlsx'),('Topic information CSV','step1/topic_info_354Topics.csv'),('Exact screening catalogue','step1/catalogue.json'),('Original training method','step1/methods/1_topic_model_training.md')]},
 {'tag':'STEP 2 / SCREEN','title':'Source review changes the selection','paras':[
 'Twelve P0 trials cross two requested model families, three effort settings and two repetitions. Each trial has three readers. Stage A uses descriptors; Stage B continues each reader through source review. An unweighted two-of-three majority determines selection.',
 'Stage A selected 66-87 topics per trial. Stage B selected 313-321. The figure shows the primary first-attempt results; the growth is sensitivity to the reading procedure, not an accuracy estimate.'],
 'figure':'screening','table':trialtable,
 'links':[('All counts and coverage','step2/analyses/primary/trial_selection_counts.csv'),('Topic-by-topic reader browser','step2/explorers/index.html')]},
 {'tag':'STEP 2 / EVIDENCE','title':'Keep missingness and minority reasons visible','paras':[
 'The primary analysis retains first saves. Six malformed or failed page saves across five readers leave 120 Stage B rows absent. There are 12,624 observed Stage B topic rows out of 12,744. Supplementary recovery records fill the roster without replacing the primary analysis.',
 'Across 4,248 trial-topic decisions, primary totals are 3,795 relevant, 452 irrelevant and one unresolved. Supplementary totals are 3,796, 452 and zero unresolved. The unresolved primary case is topic 224 in repetition 2, Astra Xhigh.',
 'Among 4,247 jointly resolved Stage A-to-B majority comparisons, 2,964 change (69.79%): 2,928 irrelevant-to-relevant and 36 relevant-to-irrelevant. There are 306 topics always selected, 31 always excluded and 17 that vary in the primary Stage B outputs.'],
 'table':[['Evidence or qualification','Retained result'],['Primary complete Stage B rosters','31 of 36 readers'],['Primary mechanical flags','62 (coverage, quotation, keyword and roster flags)'],['Supplementary mechanical flags','12; diagnostics are not semantic error counts'],['Recoveries','51 recovery pairs; 52 supplementary page attempts'],['Scope','12 P0 trials ratified after collection; no winning classifier established']],
 'after':['The delivered Step 3 input uses primary b1-gpt-6-astra-P0-xhigh: 321 selected, 33 excluded and none unresolved. This identifies the analysis actually supplied; it does not establish superiority over the other trials.',
 'The browser exposes all reader reasons, confidence explanations, quotations and missing rows. The full archive also preserves literal attempts, seals, provenance, recoveries and the documented protocol deviation.'],
 'links':[('Primary analysis report','step2/analyses/primary/REPORT.md'),('Supplementary analysis report','step2/analyses/supplementary/REPORT.md'),('All reader record locations','step2/READER_INDEX.json')]},
 {'tag':'STEP 3 / PREDICT','title':'Text predicts R&D intensity','paras':[
 'The model uses 321 selected topic features and one aggregate sentiment feature. Topic features receive a centered log-ratio transformation and standardization. Firm-CEO connected components define grouped five-fold cross-fitting.',
 'The panel contains 29,506 firm-years, 4,517 firms and 6,933 CEOs over 2013-2023. Targets are available for 29,191 rows. Missing R&D is set to zero when assets are positive; 42.7% of available targets arise from this zero-fill rule. The other 315 rows lack a target because assets are missing or nonpositive.'],
 'figure':'fit','table':metricstable,
 'after':['The reported tuning choices are Ridge alpha = 1,000 and XGBoost max_depth = 6. Evaluation uses the delivered target-available rows and winsorization convention. Per-fold counts, settings and bounds are retained in metrics.json.',
 'The score files contain out-of-fold and full-sample fitted versions plus clipped, percentile and standardized transformations. Downstream analysis uses out-of-fold scores. No industry, size or year controls enter this prediction model. This specification differs from the earlier proposed scalar N followed by f(N, controls).'],
 'links':[('All 29,506 firm-year scores (CSV)','step3/results/risk_scores.csv'),('Scores (Parquet)','step3/results/risk_scores.parquet'),('Complete model and fold metrics','step3/results/metrics.json'),('Full method','step3/docs/METHOD.md')]},
 {'tag':'STEP 3 / ROBUSTNESS','title':'The supplied small-training-sample checks','paras':[
 'The delivered robustness exercise uses three random seeds. Each seed forms a grouped 20% training / 20% validation / 60% test split. Hyperparameters are selected on the validation set; test results are compared with the supplied out-of-fold scores on the same rows and target convention.',
 'These six runs describe sensitivity to the supplied split design and training size. They are not six independent validations of psychological meaning.'],
 'table':robusttable,
 'after':['The table reproduces the saved metrics without retraining. Training and test counts, selected hyperparameters, correlations, MSE, training fit and validation fit remain in the complete CSV. The OOF comparison uses models trained on approximately 80% of the available data and is not an equal-training-size benchmark.'],
 'links':[('All robustness metrics','step3/results/seed_robustness_metrics.csv'),('Original robustness report','step3/results/seed_robustness_report.md')]},
 {'tag':'STEP 4 / ASSESS','title':'Dividend associations are consistently negative','paras':[
 'Strict company, person and timing matching yields 2,967 input observations across 600 firms, from an eligible pool of 7,086 firm-years. Ordinary score models retain 2,927 observations across 591 firms after removing industry groups that perfectly predict dividend status. The positive-relative-leverage specification uses 1,653 observations across 340 firms.',
 'Pooled Logit models include separate industry and year effects and company-clustered standard errors. Score = 100 x max(out-of-fold predicted R&D/assets, 0). Four specifications per algorithm, with and without actual R&D controls, give 16 score models. All supplied score coefficients are negative with clustered p < .01.'],
 'figure':'coefficients',
 'after':['Dots show coefficients; lines show 95% Wald intervals (coefficient +/- 1.96 x company-clustered SE). Labels m00, m08, m09 and m10 refer to the supplied specifications. XGB denotes XGBoost.',
 'For XGBoost m08 with actual R&D controls, the coefficient is about -0.1423 (SE 0.0347), implying an odds ratio near 0.867 per one-percentage-point increase in the score. This is a conditional log-odds association, not a probability-point change or causal effect.'],
 'links':[('Full score-model results','step4/score-models/results/RESULTS.html'),('All regression coefficients','step4/full/estimates/coefficients.csv')]},
 {'tag':'STEP 4 / COMPLETE INVENTORY','title':'All 25 supplied model specifications','paras':['This inventory includes the nine baseline/replication specifications and all 16 score specifications. The original five-sheet workbook, full tables, estimates and used-sample records accompany the report. The table gives score coefficients only; full control and fixed-effect coefficients are retained in the coefficient CSV.'],
 'table':modeltable,
 'links':[('Original complete workbook','step4/full/results/table4_annual_b_tables.xlsx'),('All 25 model tables','step4/full/results/REPLAYED_TABLES.html'),('Model summary and diagnostics','step4/full/estimates/model_summary.csv'),('Model specifications','step4/full/estimates/model_reference.json')]},
 {'tag':'INTERPRETATION & FILE GUIDE','title':'What the results establish, and what remains open','paras':[
 'The supplied application connects a recorded topic-selection procedure, grouped prediction of a behavioral target, and a completed dividend analysis. The evidence supports those computational and associational descriptions.',
 'Psychological meaning remains a research question. The score may reflect industry, opportunity sets, firm resources and disclosure practices as well as risk preference. Human-reference screening accuracy and a separate N/B/S construct-validation comparison are not established.',
 'Interpretation also depends on historical density alignment, zero-filled R&D, overlap between speech and target timing, topic fitting that included held-out firms\' text, and selective downstream matching. Clustered regression standard errors condition on frozen scores; they do not propagate first-stage retraining uncertainty. Related specifications are not independent replications.'],
 'table':[['Inspect','Open within the results folder'],['Report and figures','report.html / report.pdf / figures/'],['All topics and descriptors','step1/'],['All 12 trials and all reasons','step2/explorers/index.html'],['Firm-year scores and robustness','step3/results/'],['All downstream tables and estimates','step4/full/'],['Original literal reader evidence','reader-evidence/ (complete ZIP only)'],['File identities and source mapping','MANIFEST.json / SOURCES.json']],
 'after':['This report repackages existing findings; it does not claim a new empirical rerun. Newly executed reproduction evidence belongs to the separate replication package. Historical audit files remain explicitly identified as supplied checks.',
 'All files are shared within the private research repository under the source-data access conditions. Original numerical outputs and reader judgments are retained unchanged; figures, navigation and reader browsers are new presentations of those saved outputs.']}
]

styles={
 'title':ParagraphStyle('title',fontName='Helvetica-Bold',fontSize=23,leading=27,textColor=colors.HexColor(NAVY),spaceAfter=15),
 'body':ParagraphStyle('body',fontName='Helvetica',fontSize=9.5,leading=14,textColor=colors.HexColor('#253C43'),spaceAfter=10),
 'small':ParagraphStyle('small',fontName='Helvetica',fontSize=8,leading=11,textColor=colors.HexColor(GRAY),spaceAfter=5),
 'cell':ParagraphStyle('cell',fontName='Helvetica',fontSize=8,leading=10,textColor=colors.HexColor('#253C43'))}

def pdf_table(rows):
 n=len(rows[0]);widths={2:[154,326],3:[260,110,110],4:[290,64,64,62],5:[242,54,46,69,69],6:[35,62,75,70,88,150]}[n]
 data=[[Paragraph(html.escape(str(x)),styles['cell']) for x in row] for row in rows]
 t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#DCE9EB')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F5F8F8')]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),3 if len(rows)>20 else 6),('BOTTOMPADDING',(0,0),(-1,-1),3 if len(rows)>20 else 6),('LINEBELOW',(0,0),(-1,0),.7,colors.HexColor('#ADC4C9'))]))
 return t

def frame(c,doc):
 c.setStrokeColor(colors.HexColor(TEAL));c.setLineWidth(2);c.line(48,758,564,758)
 c.setFont('Helvetica',8);c.setFillColor(colors.HexColor(GRAY));c.drawString(48,773,'AI MICROFOUNDATION PROXY  /  FULL RESULTS')
 c.drawString(48,28,'Existing study outputs | Private reviewer edition | 31 October 2026')
 c.drawRightString(564,28,str(doc.page))

story=[]
for i,s in enumerate(sections):
 if i:story.append(PageBreak())
 story.append(Paragraph(s['tag'],styles['small']))
 story.append(Paragraph(html.escape(s['title']),styles['title']))
 for p in s['paras']:story.append(Paragraph(html.escape(p),styles['body']))
 if s.get('figure'):story.extend([figures[s['figure']],Spacer(1,8)])
 if s.get('table') and s.get('figure')!='screening':story.extend([pdf_table(s['table']),Spacer(1,12)])
 for p in s.get('after',[]):story.append(Paragraph(html.escape(p),styles['body']))
 for label,path in s.get('links',[]):
  story.append(Paragraph('Source: '+html.escape(label)+' - '+html.escape(path),styles['small']))
SimpleDocTemplate(str(ROOT/'report.pdf'),pagesize=(612,792),rightMargin=66,leftMargin=66,topMargin=58,bottomMargin=48,title='AI Microfoundation Proxy full results: CEO speech, R&D and dividends',author='AI Microfoundation Proxy').build(story,onFirstPage=frame,onLaterPages=frame)

def htmltable(rows):
 return '<div class="tablewrap"><table><thead><tr>'+''.join('<th>'+html.escape(str(x))+'</th>' for x in rows[0])+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(str(x))+'</td>' for x in row)+'</tr>' for row in rows[1:])+'</tbody></table></div>'
css='''*{box-sizing:border-box}body{margin:0;background:#f5f4ef;color:#233d45;font:16px/1.65 system-ui,sans-serif}header{background:#183c47;color:white;padding:64px max(6vw,24px)}header p{max-width:760px;color:#d7e5e7}h1{font:normal 50px/1.1 Georgia,serif;max-width:850px;margin:14px 0}h2{font:normal 34px/1.2 Georgia,serif;margin:8px 0 25px}main{max-width:1100px;margin:auto;padding:30px 24px 80px}section{background:white;border:1px solid #dce6e7;border-radius:6px;padding:35px;margin:24px 0}.tag{font:700 12px/1.5 system-ui;letter-spacing:.13em;color:#147d82}.tablewrap{overflow:auto}table{border-collapse:collapse;width:100%;font-size:14px;margin:20px 0}th{background:#dce9eb;text-align:left}td,th{padding:10px 12px;border-bottom:1px solid #e7eef0}tbody tr:nth-child(even){background:#f6f8f8}a{color:#116f77}nav{display:flex;flex-wrap:wrap;gap:10px}nav a{color:inherit;border:1px solid #78979f;padding:6px 12px;text-decoration:none;border-radius:3px}figure{margin:24px 0}figure img{width:100%;max-width:900px;height:auto}.sources{font-size:13px;border-top:1px solid #e7eef0;padding-top:16px}footer{font-size:13px;color:#60747a}code{font-size:.85em} @media(max-width:600px){h1{font-size:36px}h2{font-size:27px}section{padding:22px}main{padding:16px}}'''
body='<header><div class="tag" style="color:#98d4d3">FULL RESULTS / REVIEWER EDITION</div><h1>From CEO speech to a behavioral proxy</h1><p>All four steps of the supplied AI Microfoundation Proxy application, with complete tables, firm-year scores and reader-level evidence. Prepared 31 October 2026.</p><nav><a href="report.pdf">Download report PDF</a><a href="step2/explorers/index.html">Inspect all topic judgments</a><a href="MANIFEST.json">File inventory</a><a href="https://github.com/joyzhzh/ai-microfoundation-proxy/releases/tag/full-results-2026-10-31">Complete results ZIP</a></nav></header><main>'
for i,s in enumerate(sections):
 body+=f'<section id="section-{i+1}"><div class="tag">{s["tag"]}</div><h2>{html.escape(s["title"])}</h2>'
 body+=''.join('<p>'+html.escape(p)+'</p>' for p in s['paras'])
 if s.get('figure'):body+=f'<figure><img src="figures/{s["figure"]}.svg" alt="{html.escape(s["title"])}"></figure>'
 if s.get('table'):body+=htmltable(s['table'])
 body+=''.join('<p>'+html.escape(p)+'</p>' for p in s.get('after',[]))
 if s.get('links'):body+='<div class="sources">'+ ' &middot; '.join(f'<a href="{path}">{html.escape(label)}</a>' for label,path in s['links'])+'</div>'
 body+='</section>'
body+='<footer>Original scientific results are preserved. New charts and navigation are presentation layers. This report does not claim an independent empirical rerun.</footer></main>'
(ROOT/'report.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AI Microfoundation Proxy - Full results</title><style>'+css+'</style>'+body+'</html>')

# A self-contained, searchable reading page per trial: every field stays inspectable.
explorers=ROOT/'step2/explorers';explorers.mkdir(exist_ok=True)
record_index=load('step2/READER_INDEX.json');catalogue=load('step1/catalogue.json')
js='''const data=JSON.parse(document.getElementById('payload').textContent);let q=document.getElementById('q'),v=document.getElementById('variant'),filter=document.getElementById('status'),list=document.getElementById('list');function render(){list.replaceChildren();let n=0;const variant=v.value;for(const topic of data.topics){let id=String(topic.topic_id),m=data.majorities[variant].find(x=>String(x.topic_id)===id);if(filter.value&&m.label!==filter.value&&!(filter.value==='unresolved'&&m.status!=='resolved'))continue;if(q.value&&!JSON.stringify(topic).toLowerCase().includes(q.value.toLowerCase()))continue;n++;let d=document.createElement('details'),summary=document.createElement('summary');summary.textContent=id+' · '+topic.name+' — '+(m.label||'unresolved')+' | A: '+(m.vote_A||'missing')+' B: '+(m.vote_B||'missing')+' C: '+(m.vote_C||'missing');d.append(summary);d.addEventListener('toggle',()=>{if(!d.open||d.dataset.loaded)return;d.dataset.loaded='yes';for(const stage of ['initial_descriptor','source_review']){let h=document.createElement('h3');h.textContent=stage==='source_review'?'Stage B: source review':'Stage A: descriptor reading';d.append(h);for(const reader of ['A','B','C']){let record=data.records[variant][stage][reader],r=record.labels.find(x=>String(x.topic_id)===id);let box=document.createElement('article'),title=document.createElement('h4');title.textContent='Reader '+reader+(r?' · '+(r.label||r.status):' · MISSING — retained as missing');box.append(title);if(r){for(const [key,value] of Object.entries(r)){if(['topic_id','label','status'].includes(key))continue;let p=document.createElement('p'),b=document.createElement('b'),span=document.createElement('span');b.textContent=key.replaceAll('_',' ')+': ';span.textContent=typeof value==='string'?value:JSON.stringify(value,null,2);p.append(b,span);box.append(p)}}d.append(box)}}});list.append(d)}document.getElementById('count').textContent=n+' topics shown';}q.addEventListener('input',render);v.addEventListener('change',render);filter.addEventListener('change',render);render();'''
for trial in trials:
 data={'topics':catalogue['topics'],'records':{},'majorities':{}}
 for variant in ['primary','supplementary']:
  data['records'][variant]={s:{} for s in ['initial_descriptor','source_review']}
  for r in record_index:
   if r['trial_id']==trial and r['variant']==variant:data['records'][variant][r['stage']][r['reader_id']]=load(r['path'])
  data['majorities'][variant]=readcsv(f'step2/analyses/{variant}/handoffs/{trial}/topic_labels.csv')
 payload=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
 page=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{trial} - topic evidence</title><style>{css}details{{border:1px solid #ccdadd;padding:14px;margin:10px 0;background:white}}summary{{cursor:pointer;font-weight:650}}article{{padding:14px 20px;background:#f4f7f7;margin:12px 0;font-size:14px}}article span{{white-space:pre-wrap}}input,select{{padding:10px;margin:6px;font:inherit;max-width:100%}}</style><header><div class="tag" style="color:#98d4d3">COMPLETE READER EVIDENCE</div><h1>{short(trial)}</h1><p>{trial}. Select a topic to see all three readers at both stages. Missing primary responses remain missing. Supplementary recoveries are shown separately.</p><nav><a href="index.html">All trials</a><a href="../../report.html">Results report</a></nav></header><main><label>Analysis <select id="variant"><option value="primary">Primary: first saves</option><option value="supplementary">Supplementary: indexed recoveries</option></select></label><input id="q" placeholder="Search topic ID, name or keywords" aria-label="Search topic"><select id="status" aria-label="Final label"><option value="">All final labels</option><option value="relevant">Relevant</option><option value="irrelevant">Irrelevant</option><option value="unresolved">Unresolved</option></select><p id="count"></p><div id="list"></div></main><script type="application/json" id="payload">{payload}</script><script>{js}</script></html>'''
 (explorers/(trial+'.html')).write_text(page)
indexrows=[['Trial','Stage A selected','Primary Stage B selected','Read all reasons']]
for t in trials:indexrows.append([short(t),lookup[t,'initial_descriptor']['selected_N'],lookup[t,'source_review']['selected_N'],t])
indexbody='<header><div class="tag" style="color:#98d4d3">STEP 2 / ALL TRIALS</div><h1>Inspect every reader judgment</h1><p>Twelve trials. Three readers per trial. Both reading stages. Primary and supplementary results remain separate.</p><nav><a href="../../report.html">Results report</a></nav></header><main><section><p>Each page works offline and contains all original scientific label fields: rationale, confidence reasons, keyword evidence, source quotations, interpretation assessments and reasons for changes. No missing response is filled with a negative vote.</p><ul>'+''.join(f'<li><a href="{t}.html">{short(t)}</a> — Stage A {lookup[t,"initial_descriptor"]["selected_N"]}; primary Stage B {lookup[t,"source_review"]["selected_N"]}</li>' for t in trials)+'</ul><p>For literal attempts, seals and recovery provenance, use <code>reader-evidence/</code> in the complete results ZIP. The browsable JSON record index is <a href="../READER_INDEX.json">here</a>.</p></section></main>'
(explorers/'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>All AI Microfoundation Proxy topic judgments</title><style>'+css+'</style>'+indexbody+'</html>')
print('Wrote report.pdf, report.html, 3 figures and 13 topic-reader pages.')
