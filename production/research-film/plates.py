"""Draw the manuscript figure details and the film’s original evidence graphics."""
from pathlib import Path
from functools import lru_cache
from math import cos, sin
from PIL import Image, ImageDraw, ImageFont
W,H=1600,900
C={'ink':'#132D33','paper':'#FCF9F1','teal':'#126560','mint':'#8AD9BB','gold':'#AC562F','sand':'#FAC49A','muted':'#435F60','line':'#C1CFC6','light':'#DFECE4','dim':'#92ACA8','white':'#FFFFFF','deep':'#0D292D','mid':'#24464A','tint':'#F1DDCA'}
FONT_DIR=Path('/System/Library/Fonts/Supplemental')
MONO=Path('/System/Library/Fonts/Menlo.ttc')
@lru_cache(None)
def font(size,kind):
    paths={'r':FONT_DIR/'Arial.ttf','b':FONT_DIR/'Arial Bold.ttf','s':FONT_DIR/'Georgia.ttf','i':FONT_DIR/'Georgia Italic.ttf','m':MONO}
    return ImageFont.truetype(str(paths[kind]),size)
def color(k): return C.get(k,k)
def txt(x,y,s,size=34,c='ink',kind='r',anchor='lt'):
    f=font(size,kind)
    bb=D.textbbox((x,y),s,font=f,anchor=anchor)
    if bb[0] < 0 or bb[2] > W or bb[1] < 0 or bb[3]>H:
        raise ValueError((shot,s,bb))
    D.text((x,y),s,font=f,fill=color(c),anchor=anchor)
def wrap(x,y,s,maxw,size=35,c='ink',kind='r',lead=1.3):
    f=font(size,kind); lines=[]; line=''
    for token in s.split():
        t=' '.join(filter(None,(line,token)))
        if f.getlength(t)>maxw and line: lines.append(line);line=token
        else: line=t
    if line: lines.append(line)
    for v in lines: txt(x,y,v,size,c,kind);y+=round(size*lead)
    return y
def line(points,c='line',w=2): D.line(points,fill=color(c),width=w)
def rect(box,c): D.rectangle(box,fill=color(c))
def orb(x,y,r,c): D.ellipse((x-r,y-r,x+r,y+r),fill=color(c))
def arrow(x1,y1,x2,y2,c='teal'):
    import math
    line([(x1,y1),(x2,y2)],c,4)
    a=math.atan2(y2-y1,x2-x1)
    D.polygon([(x2,y2),(x2-16*cos(a-.44),y2-16*sin(a-.44)),(x2-16*cos(a+.44),y2-16*sin(a+.44))],fill=color(c))
def label(x,y,s,dark=False):
    txt(x,y,s,23,'mint' if dark else 'teal','m')
def title(s):
    txt(82,119,s,64,'paper' if dark else 'ink','s')
def deck(x,y,s,w=680,size=40):
    return wrap(x,y,s,w,size,'paper' if dark else 'ink','s',1.30)
def tag(x,y,text,positive,small=False):
    bg,fg=('light','teal') if positive else ('tint','gold')
    f=font(31 if not small else 27,'b')
    w=round(f.getlength(text))+48
    rect((x,y,x+w,y+52),bg)
    txt(x+24,y+10,text,f.size,fg,'b')
def note(x,y,s):
    txt(x,y,s,25,'dim' if dark else 'muted','r')
def tick_axis(x,y,w,vals,names,color_key='muted'):
    line((x,y,x+w,y),'line',3)
    for q,n in zip(vals,names):
        xx=x+q*w
        line((xx,y-8,xx,y+8),'line',3)
        txt(xx,y+20,n,25,color_key,'m','mt')
def fold(x,y,w,h,n,selected):
    rect((x,y,x+w,y+h),'teal' if selected else 'light')
    txt(x+w/2,y+22,n,30,'white' if selected else 'teal','m','mt')
def figcrop(box, area):
    x,y,w,h=area
    fw,fh=F.size
    fb=[round(a*b) for a,b in zip(box,[fw/468,fh/451,fw/468,fh/451])]
    sn=F.crop(fb); sn.thumbnail((w,h),Image.Resampling.LANCZOS)
    # Permit enlarging a cropped high-resolution figure when appropriate.
    scale=min(w/(fb[2]-fb[0]),h/(fb[3]-fb[1]))
    if scale>1: sn=F.crop(fb).resize((round((fb[2]-fb[0])*scale),round((fb[3]-fb[1])*scale)),Image.Resampling.LANCZOS)
    left=x+(w-sn.width)//2; top=y+(h-sn.height)//2
    rect((left-2,top-2,left+sn.width+2,top+sn.height+2),'line')
    I.paste(sn,(left,top))
def page(k,ch):
    global I,D,dark,shot
    shot=k; dark=k in ['opening','causes','speech','question','coef','shocks','shuffle','route']
    I=Image.new('RGB',(W,H),color('deep' if dark else 'paper')); D=ImageDraw.Draw(I)
    textc='dim' if dark else 'muted'
    line((82,82,1518,82),'mid' if dark else 'line',2)
    txt(82,39,'MATCH WORDS WITH DEEDS',23,'paper' if dark else 'ink','m')
    txt(1520,39,f'{ch+1:02}   /   '+['QUESTION','FRAMEWORK','READER EVIDENCE','PREDICTION','DIVIDENDS','OPEN TESTS'][ch],23,textc,'m','rt')
    # Caption-safe lower edge. All essential visual content stays above y=730.
    if k=='opening':
        label(85,158,'A RESEARCH FILM',True)
        txt(78,244,'Match Words',103,'paper','s');txt(78,367,'with Deeds',103,'paper','i')
        wrap(86,555,'What can speech and spending reveal about a CEO’s willingness to take risks?',780,39,'paper','r')
        # Two trajectories meet at a single observation.
        for y,c,t in [(287,'mint','Words'),(528,'sand','Deeds')]:
            txt(1045,y-68,t,37,c,'s')
            line([(1050,y),(1166,y),(1306,405),(1480,405)],c,5)
            orb(1050,y,9,c)
        orb(1480,405,12,'paper')
        note(84,709,'An AI-empowered proxy framework for organizational microfoundations')
    if k=='causes':
        title('One investment, two explanations')
        label(85,212,'ATTRIBUTION   /   WHO OR WHAT DROVE THE DECISION?',True)
        for y,c,a,b in [(288,'mint','01','An executive welcomes risk'),(518,'sand','02','The industry offers an opportunity')]:
            txt(86,y,a,30,c,'m');deck(175,y-12,b,620,50)
            line([(760,y+40),(849,y+40),(1000,420),(1100,420)],c,4)
        txt(1140,350,'High R&D',55,'paper','s')
        txt(1140,430,'spending',55,'paper','s')
    if k=='speech':
        title('An earnings call adds another clue')
        label(85,207,'AUTHENTICITY   /   DOES THE SPEECH REFLECT THE BELIEF?',True)
        line((787,254,787,625),'mid',3)
        label(85,279,'WHAT INVESTORS HEAR',True)
        deck(85,350,'An executive sounds willing to take risks.',610,57)
        txt(856,279,'WHAT THE FIRM DOES',23,'sand','m')
        deck(856,350,'The firm may still invest very little.',635,57)
        note(86,690,'Illustrative possibilities')
    if k=='question':
        label(85,200,'THE MEASUREMENT QUESTION',True)
        txt(82,302,'When both are ambiguous,',74,'paper','s')
        txt(82,412,'what do they tell us together?',74,'mint','i')
        line((86,570,1480,570),'mid',2)
        note(86,619,'First application   /   CEO risk preference')
    if k in ['figwhole','figback']:
        figcrop((0,0,468,451),(800,104,705,655))
        label(86,176,'FIGURE 1   /   RESEARCH FRAMEWORK')
        deck(84,250,'Choose the trait before choosing its measures.' if k=='figwhole' else 'What evidence would support the trait claim?',650,59)
        wrap(87,516,('CEO application: willingness to take risks.' if k=='figwhole' else 'Convergence asks whether the score tracks both narrative and behavioral measures.'),630,36,'muted')
    if k in ['figwords','figdeeds']:
        iswords=k=='figwords'; xx=82
        label(xx,160,'FIGURE 1   /   DETAIL')
        deck(xx,224,'Read across firms.' if iswords else 'Start with an observed decision.',600,62)
        wrap(xx,440,'Discover common topics, then ask which ones carry evidence about the trait.' if iswords else 'Choose a theoretically justified behavioral anchor. Specify any covariates for the application.',585,37,'muted')
        box=(4,68,244,219) if iswords else (249,68,463,201)
        figcrop(box,(732,170,791,489))
    if k=='figjoin':
        label(85,148,'FIGURE 1   /   THE TWO BRANCHES MEET')
        figcrop((5,218,463,351),(80,226,1435,403))
        note(86,676,'Application-specific features and covariates; held-out predictions form the synthesized proxy.')
    if k=='topic':
        title('A borderline topic')
        txt(81,259,'224',165,'teal','s')
        deck(624,277,'Discussion of the Canadian market',785,61)
        line((83,485,1509,485),'line',2)
        label(85,543,'DESCRIPTORS ALONE')
        note(86,708,'The CEO application keeps the 354-topic catalogue fixed across readers.')
        for j in range(3):
            x=616+j*288; txt(x,546,f'Reader {chr(65+j)}',29,'muted','r');tag(x,604,'Exclude',False)
    if k=='topicreview':
        title('What did expansion imply?')
        label(86,239,'TOPIC 224   /   PASSAGE REVIEW')
        for y,a,b,c in [(345,'Readers B and C','Expansion can reveal a willingness to take risk.','teal'),(522,'Reader A','Location alone tells us where the firm operates.','gold')]:
            txt(87,y,a,39,c,'b');wrap(576,y-10,b,903,49,'ink','s')
        note(86,712,'Paraphrase of reader judgments.')
    if k=='votes':
        title('Two votes retained the topic')
        for i,t in enumerate(['Reader','Descriptors','After passage review']): txt([85,504,965][i],251,t,30,'muted','b')
        for j in range(3):
            y=317+j*113;line((85,y-14,1517,y-14),'line')
            txt(85,y+12,chr(65+j),39,'ink','s')
            tag(504,y,'Exclude',False);tag(965,y,'Include' if j else 'Exclude',bool(j))
        note(86,687,'Selected trial   /   b1-gpt-6-astra-P0-xhigh')
    if k=='ranges':
        title('What changed across 12 trials?')
        label(86,230,'TOPICS RETAINED   /   OUT OF 354 REGULAR TOPICS')
        for y,t,n,l,r,c in [(358,'Descriptors','66–87',66,87,'gold'),(500,'Source review','313–321',313,321,'teal')]:
            txt(85,y,t,41,'ink','s');txt(454,y,n,40,c,'m')
            xx=698; ww=772;line((xx,y+19,xx+ww,y+19),'line',4)
            a=xx+ww*l/354;b=xx+ww*r/354;line((a,y+19,b,y+19),c,13)
            orb(a,y+19,8,c);orb(b,y+19,8,c)
        tick_axis(698,627,772,[0,0.5,1],['0','177','354'])
    if k=='choice':
        title('The trial used for prediction')
        txt(82,259,'321',158,'teal','s')
        txt(426,375,'/ 354 topics',46,'muted','r')
        line((81,488,1507,488),'line',2)
        label(86,541,'NEXT QUESTION')
        wrap(574,527,'How often would human readers agree on the borderline topics?',932,51,'ink','s')
        note(86,708,'Trial   /   b1-gpt-6-astra-P0-xhigh')
    if k=='features':
        title('Inside the delivered model')
        for x,n,lab,detail in [(84,'321','Topic densities','Transformed within the selected topics'),(838,'1','Sentiment feature','One word-weighted aggregate per firm-year')]:
            txt(x,244,n,112,'teal','s');txt(x,395,lab,47,'ink','s');wrap(x,481,detail,630,36,'muted')
        line((767,243,767,587),'line',2)
        note(86,687,'Prediction included no firm controls or fixed effects.')
    if k=='target':
        title('The decision being predicted')
        label(85,244,'BEHAVIORAL TARGET   /   SAME FISCAL YEAR')
        txt(85,347,'Research and development spending',66,'ink','s')
        line((85,455,1275,455),'gold',5)
        txt(85,499,'Total assets',66,'ink','s')
        note(85,704,'Target available when assets are positive.')
    if k=='missing':
        title('A consequential coding choice')
        txt(82,263,'42.7%',140,'gold','s')
        wrap(700,280,'of observations with an available target used zero for missing R&D.',750,49,'ink','s')
        line((85,526,1516,526),'line',2)
        label(86,593,'12,452 OF 29,191 TARGET-AVAILABLE FIRM-YEARS')
        note(86,687,'Missing spending with positive assets was coded as zero.')
    if k=='folds':
        title('Hold out the connected firms')
        label(86,234,'ONE OF FIVE SPLITS   /   ILLUSTRATION')
        for j in range(5): fold(86+j*286,330,250,99,str(j+1),j==4)
        txt(85,466,'Train on four folds',40,'ink','s');txt(1230,466,'Score here',38,'teal','s')
        wrap(85,588,'All years of a firm and all firms linked through a CEO stayed in the same fold.',1325,41,'muted')
    if k=='metric':
        title('Prediction of same-year R&D / assets')
        label(86,228,'CROSS-FITTED R²   /   COMMON TARGET')
        for j,(n,v) in enumerate([('Ridge',0.5351),('XGBoost',0.6128)]):
            y=345+j*125;txt(84,y,n,41,'ink','s');rect((403,y,1203,y+45),'light')
            rect((403,y,403+800*v,y+45),'teal');txt(1245,y,f'{v:.4f}',43,'teal','m')
        tick_axis(403,575,800,[0,0.5,1],['0','0.5','1'])
        note(86,702,'29,506 firm-years scored   /   29,191 with a target for evaluation')
    if k=='gap':
        title('The score and the signed gap')
        for y,t,b,c in [(280,'Synthesized proxy','Predicted R&D / assets','teal'),(495,'Proposed signed gap','Observed minus predicted behavior','gold')]:
            txt(85,y,t,36,c,'b');wrap(620,y-9,b,852,55,'ink','s')
        line((86,430,1515,430),'line')
        note(86,694,'A signed gap records departure from the fitted behavior. Intent requires separate evidence.')
    if k=='divsetup':
        title('A different corporate decision')
        label(86,238,'DIVIDEND POLICY   /   CALISKAN–DOUKAS SETTING')
        deck(83,337,'Did the firm pay a dividend?',1400,78)
        note(86,538,'Dependent variable   /   dividend-payer status')
        note(86,607,'Fiscal years   /   2013–2023')
    if k=='divscale':
        title('The score going into the dividend model')
        for x,num,t,sub in [(86,'01','Predict','Use the out-of-fold prediction.'),(570,'02','Clip at zero','Set negative predictions to zero.'),(1064,'03','Convert','Multiply the ratio by 100.')]:
            txt(x,264,num,32,'teal','m');txt(x,337,t,54,'ink','s');wrap(x,444,sub,412,37,'muted')
        line((86,600,1514,600),'line',2)
        note(86,672,'Model unit   /   one percentage point of predicted R&D / assets')
    if k=='coef':
        title('Column (8), with actual R&D controls')
        txt(78,248,'−0.1423',135,'mint','s')
        txt(90,427,'log-odds coefficient',40,'paper','r')
        line((800,258,800,507),'mid',2)
        txt(889,295,'0.0347',84,'paper','s')
        txt(894,422,'firm-clustered SE',38,'dim','r')
        line((86,586,1512,586),'mid',2)
        note(86,639,'XGBoost score   /   per percentage point of predicted R&D / assets')
        note(86,695,'2,927 observations   /   591 firms   /   dividend-payer logit')
    if k=='direction':
        title('The direction was consistent')
        txt(83,268,'16 / 16',117,'teal','s')
        deck(693,283,'score specifications had a negative coefficient.',765,56)
        line((86,518,1510,518),'line',2)
        txt(86,585,'Higher scores',46,'ink','s')
        arrow(442,612,705,612)
        txt(760,585,'Lower odds of paying a dividend',43,'ink','s')
    if k=='benchmark':
        title('Both component proxies enter')
        label(86,222,'FINAL APPENDIX   /   TABLE A13')
        txt(84,306,'8 / 8',112,'teal','s')
        wrap(610,304,'Synthesized-proxy coefficients remain negative at p < 0.01.',861,47,'ink','s')
        line((86,491,1510,491),'line',2)
        txt(86,544,'Ridge: −0.146',43,'teal','s')
        txt(810,544,'XGBoost: −0.141',43,'teal','s')
        note(86,625,'Inside-debt specification; narrative proxy and actual R&D controls included.')
        note(86,692,'Author-reported extension; outside the existing 25-model reproduction.')
    if k=='shocks':
        title('A common cause')
        label(86,239,'ALTERNATIVE EXPLANATION',True)
        txt(88,410,'Industry shock',57,'paper','s')
        line([(569,447),(675,447),(784,333),(921,333)],'mint',4)
        line([(569,447),(675,447),(784,563),(921,563)],'sand',4)
        txt(959,300,'Earnings-call topics',47,'mint','s');txt(959,531,'R&D spending',47,'sand','s')
    if k=='shuffle':
        title('A permutation test')
        label(86,237,'PROPOSED COMPARISON',True)
        deck(85,334,'Observed topic features',610,56);deck(851,334,'Shuffled topic features',615,56)
        line((785,310,785,582),'mid',2)
        line((86,607,1507,607),'mid',2)
        note(86,665,'Equal predictive performance would weaken the case for topic selection.')
    if k=='route':
        title('Inspect the evidence')
        for j,(a,b) in enumerate([('01','Read the CEO results'),('02','Reproduce the fitted models'),('03','Inspect the planned tests')]):
            y=248+j*124
            txt(86,y,a,32,'mint','m')
            txt(222,y-10,b,52,'paper','s')
            line((86,y+82,1515,y+82),'mid')
        note(86,689,'WordDeed   /   Proposal, appendix, results, and replication links in the transcript.')
    return I

def configure(figure, font_dir, mono_font):
    global F, FONT_DIR, MONO
    F = Image.open(figure).convert('RGB')
    FONT_DIR = font_dir
    MONO = mono_font
    font.cache_clear()
