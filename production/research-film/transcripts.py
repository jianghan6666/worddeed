"""Write both transcript formats from the narration and visual notes."""
from html import escape as esc

def clock(s):return f'{s//60}:{s%60:02}'

def write_transcripts(edition, output_dir):
    O = output_dir
    scenes = edition["scenes"]
    utterances = edition["shots"]
    info = {s["id"]: (s["visual_note"], s["references"]) for s in scenes}
    md=['# Match Words with Deeds','', '**An AI-empowered proxy framework for organizational microfoundations**','','The film follows the framework’s first application, CEO risk preference.','','**Research film transcript** · WordDeed · 4 minutes 30 seconds · English narration synthesized with Kokoro (voice af_heart).','', 'Each chapter includes its narration and a description of the evidence on screen. The final appendix extension and the reproduced 25-model package are identified separately.','', '[Play the research film](match-words-with-deeds.mp4) · [English captions](captions.en.vtt) · [Accessible HTML transcript](transcript.html)','']
    html=['<!doctype html>','<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Match Words with Deeds | Research film transcript</title>', """<style>
    :root{color-scheme:light;font-family:system-ui,sans-serif;color:#142f39;background:#fcf9f1}
    *{box-sizing:border-box}body{max-width:52rem;margin:0 auto;padding:2rem 1.3rem 4rem}main{display:block}
    a{color:#12615f;text-decoration-thickness:.09em;text-underline-offset:.16em}a:focus-visible{outline:3px solid #a95726;outline-offset:3px}
    h1,h2{font-family:Georgia,serif;font-weight:normal;line-height:1.14}h1{font-size:clamp(2.75rem,8vw,4.8rem);margin:.55em 0 .22em}h2{font-size:clamp(1.7rem,5vw,2.55rem);margin:.28em 0 .65em}
    p,li{font-size:1.1rem;line-height:1.65}ol{padding-left:1.6rem}.eyebrow,.clock{font-family:ui-monospace,monospace;letter-spacing:.03em;color:#365654}.eyebrow{font-size:.9rem}.clock{margin:0}.notes{border-left:3px solid #b3c9bd;padding-left:1rem}.notes b{display:block}.ref{font-size:1rem}section{border-top:1px solid #becbc4;padding-top:1.3rem;margin-top:2rem}nav li{padding-bottom:.15rem}
    </style></head><body><main><a href="../../index.html#film">Return to the research film</a><header><p class="eyebrow">WORDDEED · FILM TRANSCRIPT</p><h1>Match Words with Deeds</h1><p><em>An AI-empowered proxy framework for organizational microfoundations</em></p><p>The film follows the framework’s first application, CEO risk preference.</p><p>4 minutes 30 seconds · English narration synthesized with Kokoro (voice <code>af_heart</code>).</p></header>
    <p>Each chapter includes its narration and a description of the evidence on screen. The final appendix extension and the reproduced 25-model package are identified separately.</p>
    <p><a href="match-words-with-deeds.mp4">Play the MP4</a> · <a href="captions.en.vtt">English captions</a> · <a href="transcript.md">Markdown transcript</a></p><nav aria-label="Transcript chapters"><ol>"""]
    for sc in scenes:html.append(f'<li><a href="#{sc["id"]}">{clock(sc["start"])} · {esc(sc["title"])}</a></li>')
    html.append('</ol></nav>')
    for sc in scenes:
        t=sc['id'];s=sc['start'];e=sc['end'];title=sc['title'];spoken=[l['text'] for l in utterances if l['scene']==t]
        note,refs=info[t]
        md.extend([f'## {clock(s)}–{clock(e)} · {title}',''])
        html.append(f'<section id="{t}"><p class="clock">{clock(s)}–{clock(e)}</p><h2>{esc(title)}</h2>')
        for p in (' '.join(spoken[:len(spoken)//2]),' '.join(spoken[len(spoken)//2:])):
            md.extend([p,'']);html.append('<p>'+esc(p)+'</p>')
        md.extend(['**On screen**','',note,''])
        html.append(f'<p class="notes"><b>On screen</b>{esc(note)}</p>')
        if refs:
            md.extend([' · '.join(f'[{label}]({url})' for label,url in refs),''])
            html.append('<p class="ref">'+' · '.join(f'<a href="{esc(url)}">{esc(label)}</a>' for label,url in refs)+'</p>')
        html.append('</section>')
    html.append('</main></body></html>')
    (O/'transcript.md').write_text('\n'.join(md));(O/'transcript.html').write_text('\n'.join(html)+'\n')
