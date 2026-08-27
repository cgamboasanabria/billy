"""Generate a self-contained interactive study HTML.

The output is a single file with images embedded as base64 data URIs so it
opens correctly on Windows, Linux Mint or any browser without external assets.

To prevent the child from peeking at the answers via the file source (View
Source / Notepad / Ctrl+F), the answers are encoded as numeric option indices
rather than answer text. The interactive panel reveals the correct option only
after the user clicks one. Both the Study tab (active recall: see question,
reveal answer on demand) and the Quiz tab (see question with options, click
to check) are rendered client-side from the same JSON blob.
"""

from __future__ import annotations

import base64
import json as _json
import mimetypes
from pathlib import Path

from Script.functions.data_model import Matter, Question


def _data_uri(image_path: str) -> str:
    """Return a base64 data URI for the given image file."""
    path = Path(image_path)
    if not path.exists():
        return ""
    mime = mimetypes.guess_type(str(path))[0] or "image/jpeg"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _quiz_mc(matter: Matter) -> list[Question]:
    """Return questions usable in the multiple-choice quiz.

    Only questions with real options are quizzed, and any missing topic is
    bucketed under 'General' so the retry-on-fail grouping always works.
    """
    questions: list[Question] = []
    for q in matter.all_questions():
        if len(q.options) >= 2 and q.answer in q.options:
            if not q.topic:
                q.topic = "General"
            questions.append(q)
    return questions


def _build_image_map(matter: Matter) -> dict[str, str]:
    """Collect a deduplicated data-URI map for every referenced image."""
    image_map: dict[str, str] = {}
    for q in matter.all_questions():
        if not q.image_path:
            continue
        key = Path(q.image_path).name
        if key not in image_map:
            image_map[key] = _data_uri(q.image_path)
    return image_map


def _image_map_js(image_map: dict[str, str]) -> str:
    return (
        "{"
        + ",".join(
            f"{_json.dumps(k, ensure_ascii=False)}:{_json.dumps(v)}" for k, v in image_map.items()
        )
        + "}"
    )


def _image_key_for(q: Question, image_map: dict[str, str]) -> str:
    if not q.image_path:
        return ""
    return Path(q.image_path).name if Path(q.image_path).name in image_map else ""


def _questions_json(matter: Matter, image_map: dict[str, str]) -> str:
    """Build the JSON payload embedded in the HTML.

    Each entry is ``{q, topic, opts, a, exp, cita, img}`` where ``a`` is the
    index of the correct option inside ``opts``. Storing the index rather than
    the answer text keeps the answer out of plain-text source greps.
    """
    entries: list[str] = []
    for q in _quiz_mc(matter):
        entries.append(
            json_dumps(
                {
                    "q": q.question,
                    "topic": q.topic,
                    "opts": q.options,
                    "a": q.options.index(q.answer) if q.answer in q.options else 0,
                    "exp": q.explanation,
                    "cita": q.cita_textual,
                    "p": q.page,
                    "img": _image_key_for(q, image_map),
                }
            )
        )
    questions_js = "[" + ",".join(entries) + "]"
    return questions_js


def _study_json(matter: Matter, image_map: dict[str, str]) -> str:
    """Group questions by topic so the study panel can render topic tabs."""
    by_topic: dict[str, list[dict]] = {}
    for q in matter.all_questions():
        topic = q.topic or "General"
        entry: dict = {
            "q": q.question,
            "opts": q.options,
            "a": -1,
            "exp": q.explanation,
            "cita": q.cita_textual,
            "p": q.page,
            "img": _image_key_for(q, image_map),
        }
        if q.answer in q.options:
            entry["a"] = q.options.index(q.answer)
        elif not q.options:
            entry["opts"] = []
            entry["exp"] = q.cita_textual or "(sin opciones)"
        by_topic.setdefault(topic, []).append(entry)
    return json_dumps(by_topic)


def render_subject_html(matter: Matter) -> str:
    """Build the self-contained HTML for a subject and return it as a string."""
    image_map = _build_image_map(matter)
    images_js = _image_map_js(image_map)
    quiz_data = _questions_json(matter, image_map)
    study_data = _study_json(matter, image_map)

    html = _TEMPLATE.replace("__TITLE__", matter.name)
    html = html.replace("__IMAGES__", images_js)
    html = html.replace("__QUESTIONS__", quiz_data)
    html = html.replace("__STUDY__", study_data)
    return html


def generate_subject_html(matter: Matter, output_path: str | Path) -> Path:
    """Write the self-contained HTML for a subject and return its path."""
    dest = Path(output_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(render_subject_html(matter), encoding="utf-8")
    return dest


def json_dumps(value: object) -> str:
    return _json.dumps(value, ensure_ascii=False)


_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Estudio: __TITLE__</title>
<style>
:root{--main:#006400;--accent:#ffdf00;--correct:#28a745;--wrong:#dc3545;--muted:#888;}
body{font-family:Arial,sans-serif;background:#f0fff0;color:#333;margin:0;padding:20px;text-align:center;}
.container{max-width:820px;margin:auto;background:#fff;padding:20px;border-radius:10px;box-shadow:0 4px 8px rgba(0,0,0,.1);}
h1,h2,h3{color:var(--main);}
.progress-container{width:100%;background:#e0e0e0;border-radius:5px;margin-bottom:20px;}
.progress-bar{width:0%;height:20px;background:var(--accent);border-radius:5px;text-align:center;line-height:20px;color:#333;transition:width .5s;}
.tabs{display:flex;justify-content:center;margin-bottom:20px;flex-wrap:wrap;}
.tab-button{background:var(--main);color:#fff;border:none;padding:10px 20px;margin:5px;border-radius:5px;cursor:pointer;font-size:16px;}
.tab-button:hover,.tab-button.active{background:#004d00;}
.content{display:none;text-align:left;padding:15px;border:1px solid #ddd;border-radius:5px;}
.content.active{display:block;}
.question{font-size:1.2em;margin-bottom:20px;}
.options{display:flex;flex-direction:column;}
.option{background:#f1f1f1;border:1px solid #ddd;padding:15px;margin:5px 0;border-radius:5px;cursor:pointer;text-align:left;}
.option:hover{background:#e0e0e0;}
.feedback{margin-top:15px;padding:10px;border-radius:5px;font-size:1.1em;text-align:left;}
.study-card{border-left:4px solid var(--main);margin:10px 0;padding:10px;background:#fafafa;text-align:left;}
.study-card .study-q{font-weight:bold;margin-bottom:5px;}
.study-card .study-actions{margin-top:8px;}
.study-card .study-actions button{font-size:.95em;padding:6px 12px;}
.study-panel,.study-panel.active{display:none;text-align:left;}
.study-panel.active{display:block;}
.ref-image{max-width:100%;margin:10px 0;border:1px solid #ccc;border-radius:5px;}
.cita{color:#555;font-size:.95em;font-style:italic;}
.hidden{display:none;}
#results-container{display:none;text-align:center;}
</style>
</head>
<body>
<div class="container">
<h1>Estudio de __TITLE__</h1>
<div class="tabs">
<button class="tab-button active" data-tab="estudio" onclick="showContent('estudio')">Estudiar</button>
<button class="tab-button" data-tab="quiz" onclick="showContent('quiz')">Practicar</button>
</div>
<div id="estudio" class="content active"></div>
<div id="quiz" class="content">
<h3>Prueba de Conocimiento</h3>
<div class="progress-container"><div class="progress-bar" id="progress-bar">0%</div></div>
<div id="quiz-container">
<p class="question" id="question"></p>
<div class="options" id="options"></div>
<div class="feedback" id="feedback"></div>
</div>
<div id="results-container">
<h2>Completaste la prueba</h2>
<p>Puntuacion: <strong id="score"></strong></p>
<button class="tab-button" onclick="restartQuiz()">Jugar de Nuevo</button>
</div>
</div>
</div>
<script>
const IMGS = __IMAGES__;
const allQuestions = __QUESTIONS__;
const STUDY = __STUDY__;

const qEl=document.getElementById('question');
const optsEl=document.getElementById('options');
const fbEl=document.getElementById('feedback');
const bar=document.getElementById('progress-bar');
const quizBox=document.getElementById('quiz-container');
const results=document.getElementById('results-container');
const scoreEl=document.getElementById('score');
const estudioEl=document.getElementById('estudio');

let queue=[];let idx=0;let score=0;let correct=0;let total=0;
let currentQuestion=null;

function shuffle(a){for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]];}return a;}
function showContent(t){
  document.getElementById('estudio').style.display='none';
  document.getElementById('quiz').style.display='none';
  document.querySelectorAll('.tabs>.tab-button').forEach(b=>b.classList.remove('active'));
  const btn=document.querySelector('.tabs>.tab-button[data-tab="'+t+'"]');
  if(btn){btn.classList.add('active');}
  document.getElementById(t).style.display='block';
  if(t==='estudio'){renderStudy();}
  if(t==='quiz'&&total===0){startQuiz();}
}
function renderStudy(){
  estudioEl.innerHTML='';
  const topics=Object.keys(STUDY);
  if(!topics.length){estudioEl.innerHTML='<p>No hay contenido de estudio todavia.</p>';return;}
  const nav=document.createElement('div');nav.className='tabs';
  const panels=document.createElement('div');
  topics.forEach((t,i)=>{
    const b=document.createElement('button');
    b.className='tab-button'+(i===0?' active':'');
    b.textContent=t;
    b.onclick=()=>{nav.querySelectorAll('.tab-button').forEach(x=>x.classList.remove('active'));b.classList.add('active');panels.querySelectorAll('.study-panel').forEach(p=>p.classList.remove('active'));panels.querySelector('.study-panel[data-i="'+i+'"]').classList.add('active');};
    nav.appendChild(b);
    const panel=document.createElement('div');
    panel.className='study-panel'+(i===0?' active':'');
    panel.dataset.i=i;
    (STUDY[t]||[]).forEach((q,qi)=>{
      const card=document.createElement('div');card.className='study-card';
      const qEl2=document.createElement('p');qEl2.className='study-q';qEl2.textContent=q.q;card.appendChild(qEl2);
      const optsBox=document.createElement('div');optsBox.className='options hidden';optsBox.id='opts-'+i+'-'+qi;
      shuffle([...(q.opts||[]).keys()]).forEach((oi)=>{
        const o=q.opts[oi];
        const d=document.createElement('div');d.className='option';d.textContent=o;
        d.dataset.idx=oi;
        d.onclick=()=>{
          optsBox.querySelectorAll('.option').forEach(x=>{x.onclick=null;});
          if(q.a>=0){
            optsBox.querySelectorAll('.option').forEach((x)=>{
              const xi=Number(x.dataset.idx);
              if(xi===q.a){x.style.background='var(--correct)';x.style.color='#fff';}
              if(xi===oi&&oi!==q.a){x.style.background='var(--wrong)';x.style.color='#fff';}
            });
            const fb=document.createElement('div');fb.className='feedback';
            if(oi===q.a){fb.style.background='#e8f5e9';fb.textContent='Correcto';}
            else{fb.style.background='#ffebee';fb.innerHTML='Incorrecto. La respuesta correcta era: <b>'+q.opts[q.a]+'</b>';}
            card.appendChild(fb);
          }
          if(q.exp){const e=document.createElement('p');e.className='feedback';e.textContent=q.exp;card.appendChild(e);}
          if(q.cita){const c=document.createElement('p');c.className='cita';c.textContent='Cita: '+q.cita+(q.p?' (pagina '+q.p+')':'');card.appendChild(c);}
          if(q.img){const im=document.createElement('img');im.className='ref-image';im.src=IMGS[q.img]||'';im.alt='Imagen de referencia';card.appendChild(im);}
        };
        optsBox.appendChild(d);
      });
      card.appendChild(optsBox);
      if(q.opts&&q.opts.length){
        const actions=document.createElement('div');actions.className='study-actions';
        const btn=document.createElement('button');btn.className='tab-button';btn.textContent='Mostrar opciones';
        btn.onclick=()=>{optsBox.classList.toggle('hidden');btn.textContent=optsBox.classList.contains('hidden')?'Mostrar opciones':'Ocultar opciones';};
        actions.appendChild(btn);card.appendChild(actions);
      }else{
        const cita=document.createElement('p');cita.className='cita';cita.textContent=q.exp||q.cita||'';card.appendChild(cita);
      }
      panel.appendChild(card);
    });
    panels.appendChild(panel);
  });
  estudioEl.appendChild(nav);
  estudioEl.appendChild(panels);
}
function startQuiz(){queue=shuffle([...allQuestions]);total=queue.length;idx=0;score=0;correct=0;results.style.display='none';quizBox.style.display='block';updateBar();showQuestion();}
function restartQuiz(){total=0;startQuiz();}
function showQuestion(){fbEl.innerHTML='';fbEl.style.background='transparent';const c=queue[idx];currentQuestion=c;qEl.textContent=c.q;optsEl.innerHTML='';shuffle([...c.opts.keys()]).forEach((oi)=>{const b=document.createElement('div');b.textContent=c.opts[oi];b.className='option';b.dataset.idx=oi;b.onclick=()=>check(oi,b);optsEl.appendChild(b);});}
function next(){if(idx<queue.length){showQuestion();}else{quizBox.style.display='none';results.style.display='block';scoreEl.textContent=score+' de '+total;}}
function check(sel,btn){const c=queue[idx];optsEl.querySelectorAll('.option').forEach(o=>o.onclick=null);let html='';
if(sel===c.a){score++;correct++;btn.style.background='var(--correct)';btn.style.color='#fff';html='<div class="feedback" style="background:#e8f5e9">Correcto<br>'+c.exp+'</div>';idx++;}
else{btn.style.background='var(--wrong)';btn.style.color='#fff';optsEl.querySelectorAll('.option').forEach((o)=>{if(o.dataset.idx===String(c.a)){o.style.background='var(--correct)';o.style.color='#fff';}});html='<div class="feedback" style="background:#ffebee">Incorrecto. La opcion correcta era: <b>'+c.opts[c.a]+'</b><br>'+c.exp+'</div>';
const topic=c.topic;queue.splice(idx,1);const r=queue.findIndex(q=>q.topic===topic);if(r!==-1){const [m]=queue.splice(r,1);queue.splice(idx,0,m);}}
if(c.img){html+='<img class="ref-image" src="'+IMGS[c.img]+'" alt="Imagen de referencia">';}
if(c.cita){html+='<p class="cita">Cita: <i>'+c.cita+'</i>'+(c.p?' (pagina '+c.p+')':'')+'</p>';}
html+='<button class="tab-button" style="margin-top:15px" onclick="next()">Avanzar</button>';
fbEl.innerHTML=html;fbEl.style.background='transparent';updateBar();
window.__lastQuestion=c;}
function updateBar(){const p=(correct/total)*100;bar.style.width=p+'%';bar.textContent=Math.round(p)+'%';}
showContent('estudio');
window.__getCurrent=()=>currentQuestion;
</script>
</body>
</html>
"""
