from flask import Flask, render_template_string, request, jsonify
import sqlite3
import os

app = Flask(__name__)
DB_PATH = 'data/quiz.db'

def init_db():
    os.makedirs('data', exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            school TEXT,
            mfy TEXT,
            score INTEGER,
            total INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Siz bergan mukammal dizayn va dastur kodi
HTML_PAGE = """<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Davlat bayrogʻi · Angren</title>
<link href="https://fonts.googleapis.com/css2?family=Onest:wght@400;600;800&display=swap" rel="stylesheet">
<style>
:root{--bg:#f6f9fa;--card:#fff;--ink:#0d2b38;--mut:#55707c;--blue:#0099b5;--green:#1eb53a;--red:#ce1126;--line:#d8e4e8;--ok:#e2f6e6;--no:#fde6e8;
box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0a1b24;--card:#11303d;--ink:#eaf4f7;--mut:#9db9c4;--line:#24475a;--ok:#12402250;--no:#4a1a2150;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#0a1b24;--card:#11303d;--ink:#eaf4f7;--mut:#9db9c4;--line:#24475a;--ok:#12402250;--no:#4a1a2150;color-scheme:dark}
*{box-sizing:inherit}html{scroll-padding-top:env(safe-area-inset-top,0px)}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 Onest,system-ui,"Segoe UI",Roboto,Arial,sans-serif}
header{position:sticky;top:env(safe-area-inset-top,0px);z-index:5;background:var(--card);border-bottom:1px solid var(--line)}
.bar{max-width:960px;margin:auto;display:flex;align-items:center;gap:12px;padding:10px 16px;flex-wrap:wrap}
.brand{font-weight:800;display:flex;gap:10px;align-items:center;cursor:pointer;margin-right:auto}
nav{display:flex;gap:4px;flex-wrap:wrap}
nav button,.lang button{border:0;background:none;color:var(--ink);font:inherit;padding:8px 12px;border-radius:8px;cursor:pointer}
nav button.on{background:var(--blue);color:#fff}
.lang{display:flex;border:1px solid var(--line);border-radius:10px;overflow:hidden}
.lang button.on{background:var(--ink);color:var(--bg);font-weight:800}
button:focus-visible,input:focus-visible{outline:3px solid var(--blue);outline-offset:2px}
main{max-width:960px;margin:auto;padding:24px 16px 56px}
.hero{display:grid;gap:28px;align-items:center;padding:12px 0 8px}
@media(min-width:760px){.hero{grid-template-columns:1.1fr 1fr}}
h1{font-size:clamp(30px,6vw,50px);line-height:1.08;margin:0 0 14px;font-weight:800;letter-spacing:-.02em}
h2{font-size:26px;margin:0 0 16px}
p.lead{color:var(--mut);font-size:18px;margin:0 0 22px;max-width:46ch}
.flag{width:100%;height:auto;border-radius:10px;box-shadow:0 14px 34px rgba(13,43,56,.28)}
.btn{border:0;background:var(--green);color:#fff;font:inherit;font-weight:800;padding:14px 26px;border-radius:12px;cursor:pointer;font-size:17px}
.btn.alt{background:none;color:var(--ink);border:2px solid var(--line)}
.btn:disabled{opacity:.4;cursor:default}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:22px;max-width:560px}
label{display:block;font-weight:600;margin:14px 0 6px}
input{width:100%;font:inherit;padding:12px 14px;border:2px solid var(--line);border-radius:10px;background:var(--bg);color:var(--ink)}
input.bad{border-color:var(--red)}.err{color:var(--red);font-size:14px;min-height:18px}
.prog{height:8px;background:var(--line);border-radius:8px;overflow:hidden;margin:6px 0 20px}
.prog i{display:block;height:100%;background:linear-gradient(90deg,var(--blue),var(--green));transition:width .3s}
.opt{display:block;width:100%;text-align:left;font:inherit;padding:14px 16px;margin:10px 0;border:2px solid var(--line);border-radius:12px;background:var(--card);color:var(--ink);cursor:pointer}
.opt:hover:not(:disabled){border-color:var(--blue)}
.opt.ok{background:var(--ok);border-color:var(--green)}.opt.no{background:var(--no);border-color:var(--red)}
.q{font-size:22px;font-weight:600;line-height:1.35;margin:0 0 12px}
.big{font-size:72px;font-weight:800;line-height:1}
.facts{display:grid;gap:14px}@media(min-width:700px){.facts{grid-template-columns:1fr 1fr}}
.fact{background:var(--card);border:1px solid var(--line);border-left:6px solid var(--blue);border-radius:12px;padding:16px 18px}
.fact:nth-child(3n+2){border-left-color:var(--green)}.fact:nth-child(3n){border-left-color:var(--red)}
.fact b{display:block;margin-bottom:4px}
.tw{overflow-x:auto}table{border-collapse:collapse;width:100%;min-width:420px}
th,td{text-align:left;padding:10px 12px;border-bottom:1px solid var(--line)}th{color:var(--mut);font-weight:600}
.note{color:var(--mut);font-size:14px;margin-top:14px}
@media(prefers-reduced-motion:reduce){*{transition:none!important}}
</style>
</head>
<body>
<header><div class="bar">
<div class="brand" id="brand"><svg width="34" height="17" viewBox="0 0 200 100" aria-hidden="true"><rect width="200" height="34" fill="#0099b5"/><rect y="33" width="200" height="34" fill="#fff"/><rect y="66" width="200" height="34" fill="#1eb53a"/><rect y="32" width="200" height="3" fill="#ce1126"/><rect y="65" width="200" height="3" fill="#ce1126"/></svg><span id="bt"></span></div>
<nav id="nav"></nav>
<div class="lang"><button data-l="uz">UZ</button><button data-l="ru">RU</button></div>
</div></header>
<main id="app"></main>
<script>
const T={uz:{
brand:"Bayroq · Angren",n:["Bosh sahifa","Viktorina","Qiziqarli faktlar","Natijalar"],
h:"Bayrogʻimizni qanchalik bilasiz?",p:"Angren shahri yoshlari va oʻquvchilari uchun viktorina: 10 ta savol, 100 ball. Oʻz bilimingizni sinab koʻring.",
go:"Viktorinani boshlash",rt:"Ishtirokchi maʼlumotlari",nm:"F.I.Sh. (toʻliq ism va familiya)",ph:"Telefon raqami",sc:"Taʼlim olayotgan maktab",mf:"MFY (mahalla fuqarolar yigʻini)",e4:"MFY nomini kiriting.",
e1:"Ism va familiyani toʻliq kiriting.",e2:"Raqamni +998 90 123 45 67 koʻrinishida kiriting.",e3:"Maktab nomini kiriting.",
start:"Boshlash",qn:(a,b)=>`Savol ${a} / ${b}`,next:"Keyingi savol",fin:"Natijani koʻrish",
res:"Sizning natijangiz",lv:["Yaxshi urinish — faktlarni oʻqib, qayta urinib koʻring","Yaxshi natija!","Aʼlo! Siz bayroq bilimdonisiz"],
pt:"ball",again:"Qayta topshirish",sv:"Natija umumiy roʻyxatga saqlandi.",sl:"Natija shu qurilmada saqlandi.",
fh:"Qiziqarli faktlar",rh:"Natijalar jadvali",rk:["#","Ishtirokchi","Maktab","Ball","%"],none:"Hozircha natijalar yoʻq.",csv:"CSV yuklab olish",
loc:"Bu roʻyxat faqat shu qurilmadagi natijalarni koʻrsatadi.",
Q:[["Davlat bayrogʻi qaysi yilda qabul qilingan?",["1991","1992","1995","2001"],0],
["Bayroqdagi yulduzlar soni nechta?",["8","10","12","14"],2],
["Oq rang nimani anglatadi?",["Tinchlik va poklik","Mustaqillik","Adolat","Birdamlik"],0],
["Yashil rang nimaning ramzi?",["Choʻl","Tabiat va yangilanish","Togʻlar","Qurgʻoqchilik"],1],
["Bayroqdagi ingichka qizil chiziqlar nimani bildiradi?",["Chegara","Hayotbaxsh kuch","Bayram","Sanʼat"],1],
["Bayroq ranglari yuqoridan pastga qanday joylashgan?",["Yashil, oq, koʻk","Oq, koʻk, yashil","Koʻk, oq, yashil","Koʻk, yashil, oq"],2],
["Yarim oy nimani ifodalaydi?",["Yangi mustaqil davlatning yangilanishini","Qishni","Savdoni","Sportni"],0],
["Davlat bayrogʻi kuni qachon nishonlanadi?",["1-sentabr","18-noyabr","8-dekabr","21-mart"],1],["Bayroqning tomonlar nisbati qanday?",["1:1","1:2","2:3","3:4"],1],["Ranglarni ajratib turuvchi ingichka qizil chiziqlar nechta?",["1","2","3","4"],1]],
F:[["Bayroqlar fani","Bayroqlarni oʻrganadigan fan vexillologiya deb ataladi. Uning mutaxassislari har bir bayroqning tarixi, dizayni va ramzlarini tadqiq qiladi."],["Uch davlat ramzi","Bayroq, gerb va madhiya — Oʻzbekistonning uchta davlat ramzi. Gerbda Xumo qushi tasvirlangan, madhiya soʻzlarini shoir Abdulla Oripov yozgan."],["Eski nomlari","Eski oʻzbek tilida bayroq maʼnosida «tugʻ» va «alam» soʻzlari ham ishlatilgan."],["Temur tugʻi","Amir Temur davriga oid manbalarda tugʻlardagi uch halqa tasviri tilga olinadi — bu belgi Temur tamgʻasi bilan bogʻliq deb yoziladi."],["Mustaqillikdan oldin","Mustaqillikdan oldin Oʻzbekiston SSR bayrogʻi qizil fonda boʻlib, pastki qismida moviy chiziq bor edi."],["Eng qadimiy bayroq","Daniya bayrogʻi — Dannebrog dunyoda uzluksiz qoʻllanilayotgan eng qadimiy milliy bayroq hisoblanadi, uning tarixi taxminan sakkiz asrga borib taqaladi."],["Toʻrtburchak emas","Dunyoda yagona davlat bayrogʻi toʻrtburchak shaklida emas — bu Nepal bayrogʻi, u ikki uchburchakdan iborat."],["Qizil rang","Dunyo davlat bayroqlarida eng koʻp uchraydigan ranglardan biri qizil."],["Bayroq emojisi","🇺🇿 belgisi aslida ikki harf — U va Z dan tuziladi. Koʻpchilik telefonlarda bu ikki harf birlashib bayroqqa aylanadi."],["Alifbo tartibida","Nyu-Yorkdagi BMT shtab-kvartirasi oldida aʼzo davlatlar bayroqlari inglizcha alifbo tartibida turadi."],["Olimpiada","Mustaqil Oʻzbekiston terma jamoasi Olimpiya oʻyinlarida birinchi marta 1996-yilda Atlantada qatnashgan."],["Yarim ustunda","Motam kunlarida davlat bayroqlari odatda ustunning yarmigacha tushiriladi — bu hurmat belgisi."],["Yerga tegmasin","Bayroqni yerga tekkizmaslik va ehtiyotkorlik bilan tutish bayroq madaniyatining asosiy qoidalaridan biri."],["Yaxshi dizayn","Bayroq dizaynerlari qoida qoʻllaydi: bayroq shunchalik sodda boʻlsin-ki, uni bola xotiradan chiza olsin."],["Angren","Angren — Toshkent viloyatidagi yirik sanoat shaharlaridan biri, koʻmir konlari bilan mashhur."],
]},
ru:{
brand:"Флаг · Ангрен",n:["Главная","Викторина","Интересные факты","Результаты"],
h:"Насколько хорошо вы знаете наш флаг?",p:"Викторина для молодёжи и школьников города Ангрен: 10 вопросов, 100 баллов. Проверьте свои знания.",
go:"Начать викторину",rt:"Данные участника",nm:"Ф.И.О. (полностью)",ph:"Номер телефона",sc:"Школа, в которой вы учитесь",mf:"МСГ (махалля)",e4:"Укажите название МСГ (махалли).",
e1:"Введите имя и фамилию полностью.",e2:"Введите номер в формате +998 90 123 45 67.",e3:"Укажите название школы.",
start:"Начать",qn:(a,b)=>`Вопрос ${a} из ${b}`,next:"Следующий вопрос",fin:"Показать результат",
res:"Ваш результат",lv:["Хорошая попытка — прочтите факты и попробуйте снова","Хороший результат!","Отлично! Вы знаток флага"],
pt:"баллов",again:"Пройти заново",sv:"Результат сохранён в общем списке.",sl:"Результат сохранён на этом устройстве.",
fh:"Интересные факты",rh:"Таблица результатов",rk:["#","Участник","Школа","Баллы","%"],none:"Пока нет результатов.",csv:"Скачать CSV",
loc:"В списке только результаты с этого устройства.",
Q:[["В каком году принят Государственный флаг?",["1991","1992","1995","2001"],0],
["Сколько звёзд на флаге?",["8","10","12","14"],2],
["Что означает белый цвет?",["Мир и чистоту","Независимость","Справедливость","Единство"],0],
["Что символизирует зелёный цвет?",["Пустыню","Природу и обновление","Горы","Засуху"],1],
["Что означают тонкие красные полосы?",["Границу","Жизненную силу","Праздник","Искусство"],1],
["Как расположены цвета сверху вниз?",["Зелёный, белый, голубой","Белый, голубой, зелёный","Голубой, белый, зелёный","Голубой, зелёный, белый"],2],
["Что выражает полумесяц?",["Обновление молодого независимого государства","Зиму","Торговлю","Спорт"],0],
["Когда отмечается День Государственного флага?",["1 сентября","18 ноября","8 декабря","21 марта"],1],["Каково соотношение сторон флага?",["1:1","1:2","2:3","3:4"],1],["Сколько тонких красных полос разделяют цвета?",["1","2","3","4"],1]],
F:[["Наука о флагах","Наука, изучающая флаги, называется вексиллологией. Её специалисты исследуют историю, дизайн и символику каждого флага."],["Три государственных символа","Флаг, герб и гимн — три государственных символа Узбекистана. На гербе изображена птица Хумо, а слова гимна написал поэт Абдулла Арипов."],["Старые названия","В старом узбекском языке для обозначения знамени использовались также слова «туг» и «алам»."],["Знамя Темура","В источниках эпохи Амира Темура упоминается изображение трёх колец на знамёнах — этот знак связывают с тамгой Темура."],["До независимости","До обретения независимости флаг Узбекской ССР был красным, а в нижней части проходила голубая полоса."],["Самый древний флаг","Флаг Дании — Даннеброг — считается самым древним непрерывно используемым национальным флагом, его история насчитывает около восьми веков."],["Не прямоугольник","В мире только флаг Непала не имеет формы прямоугольника — он состоит из двух треугольников."],["Красный цвет","Красный — один из самых распространённых цветов на государственных флагах мира."],["Эмодзи-флаг","Значок 🇺🇿 на самом деле состоит из двух букв — U и Z. На большинстве телефонов они объединяются в флаг."],["По алфавиту","Перед зданием ООН в Нью-Йорке флаги стран-членов стоят в порядке английского алфавита."],["Олимпиада","Независимый Узбекистан впервые выступил на Олимпийских играх в 1996 году в Атланте."],["На половину флагштока","В дни траура государственные флаги обычно спускают до половины флагштока — это знак уважения."],["Не касаться земли","Не допускать касания флага земли и обращаться с ним бережно — одно из главных правил флаговой культуры."],["Хороший дизайн","Дизайнеры флагов следуют правилу: флаг должен быть настолько простым, чтобы ребёнок мог нарисовать его по памяти."],["Ангрен","Ангрен — один из крупных промышленных городов Ташкентской области, известный угольными месторождениями."],
]}};
const $=s=>document.querySelector(s),LK="angren_flag_results";
let L="uz",view="home",P={},qi=0,sc=0,lock=false,BD=null,RD=null,UI=null,saved="";
try{L=localStorage.getItem("lang")||"uz"}catch(e){}
const t=()=>T[L],esc=s=>String(s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
function flag(){let s="";[[34,9,3],[34,16,4],[34,23,5]].forEach(([x0,y,n])=>{for(let i=0;i<n;i++)s+=`<circle cx="${x0+i*9+(5-n)*4.5}" cy="${y}" r="2.2" fill="#fff"/>`});
return `<svg class="flag" viewBox="0 0 200 100" role="img" aria-label="Oʻzbekiston / Узбекистан"><rect width="200" height="34" fill="#0099b5"/><rect y="33" width="200" height="34" fill="#fff"/><rect y="66" width="200" height="34" fill="#1eb53a"/><rect y="32" width="200" height="2.4" fill="#ce1126"/><rect y="65.6" width="200" height="2.4" fill="#ce1126"/><circle cx="19" cy="16" r="10" fill="#fff"/><circle cx="23" cy="16" r="9" fill="#0099b5"/>${s}</svg>`}
function go(v){view=v;render();scrollTo(0,0)}
function render(){document.documentElement.lang=L;try{localStorage.setItem("lang",L)}catch(e){}
$("#bt").textContent=t().brand;document.title=t().brand;
$("#nav").innerHTML=t().n.map((n,i)=>`<button data-v="${["home","reg","facts","board"][i]}" class="${(view==="quiz"||view==="result"?"reg":view)===["home","reg","facts","board"][i]?"on":""}">${n}</button>`).join("");
document.querySelectorAll(".lang button").forEach(b=>b.classList.toggle("on",b.dataset.l===L));
const a=$("#app");({home,reg,quiz,result,facts,board})[view](a)}
function home(a){a.innerHTML=`<section class="hero"><div><h1>${t().h}</h1><p class="lead">${t().p}</p><button class="btn" id="go">${t().go}</button></div>${flag()}</section>`;$("#go").onclick=()=>go("reg")}
function reg(a){const x=t();a.innerHTML=`<div class="card"><h2>${x.rt}</h2><label for="nm">${x.nm}</label><input id="nm" autocomplete="name" value="${esc(P.name||"")}"><div class="err" id="e1"></div>
<label for="ph">${x.ph}</label><input id="ph" type="tel" inputmode="tel" placeholder="+998 90 123 45 67" autocomplete="tel" value="${esc(P.phone||"")}"><div class="err" id="e2"></div>
<label for="sc">${x.sc}</label><input id="sc" placeholder="Angren, 12-maktab" value="${esc(P.school||"")}"><div class="err" id="e3"></div>
<label for="mf">${x.mf}</label><input id="mf" placeholder="Angren, ..." value="${esc(P.mfy||"")}"><div class="err" id="e4"></div>
<p><button class="btn" id="st">${x.start}</button></p></div>`;
$("#st").onclick=()=>{const n=$("#nm").value.trim(),p=$("#ph").value.replace(/[\s()-]/g,""),s=$("#sc").value.trim(),m=$("#mf").value.trim();
const ok=[n.split(/\s+/).filter(w=>w.length>1).length>=2,/^(\+?998)?\d{9}$/.test(p),s.length>=2,m.length>=2];
["nm","ph","sc","mf"].forEach((id,i)=>{$("#"+id).classList.toggle("bad",!ok[i]);$("#e"+(i+1)).textContent=ok[i]?"":x["e"+(i+1)]});
if(ok.every(Boolean)){P={name:n,phone:p,school:s,mfy:m};qi=0;sc=0;lock=false;saved="";go("quiz")}}}
function quiz(a){const x=t(),q=x.Q[qi],N=x.Q.length;
a.innerHTML=`<div class="card" style="max-width:640px"><div>${x.qn(qi+1,N)}</div><div class="prog"><i style="width:${qi/N*100}%"></i></div><p class="q">${q[0]}</p>${q[1].map((o,i)=>`<button class="opt" data-i="${i}">${o}</button>`).join("")}<p id="nx"></p></div>`;
document.querySelectorAll(".opt").forEach(b=>b.onclick=()=>{if(lock)return;lock=true;const i=+b.dataset.i;
if(i===q[2])sc++;document.querySelectorAll(".opt").forEach((o,j)=>{o.disabled=true;if(j===q[2])o.classList.add("ok");else if(j===i)o.classList.add("no")});
$("#nx").innerHTML=`<button class="btn" id="n">${qi+1<N?x.next:x.fin}</button>`;$("#n").focus();
$("#n").onclick=()=>{lock=false;if(qi+1<N){qi++;quiz(a)}else{finish();go("result")}}})}
function finish(){
    const row={name:P.name,phone:P.phone,school:P.school,mfy:P.mfy,score:sc,total:t().Q.length,ts:Date.now(),lang:L};
    try{const r=JSON.parse(localStorage.getItem(LK)||"[]");r.push(row);localStorage.setItem(LK,JSON.stringify(r));saved="l"}catch(e){}
    
    // SQLite bazasiga va admin panelga yuborish
    fetch('/api/submit', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            name: P.name,
            phone: P.phone,
            school: P.school,
            mfy: P.mfy,
            score: sc,
            total: t().Q.length
        })
    }).then(res => res.json()).then(data => {
        if(data.status === 'ok') { saved = "s"; if(view==="result") render(); }
    }).catch(err => {});
}
function result(a){const x=t(),N=x.Q.length,lv=sc/N>=.8?2:sc/N>=.5?1:0;
a.innerHTML=`<div class="card" style="text-align:center"><h2>${x.res}</h2><div class="big" style="color:var(--${lv?"green":"red"})">${sc*10}<span style="font-size:32px;color:var(--mut)"> / ${N*10} ${x.pt}</span></div><p><b>${Math.round(sc/N*100)}%</b> (${sc}/${N}) — ${x.lv[lv]}</p><p class="note">${saved==="s"?x.sv:saved==="l"?x.sl:""}</p><p><button class="btn" id="a1">${x.again}</button> <button class="btn alt" id="a2">${x.fh}</button> <button class="btn alt" id="a3">${x.n[3]}</button></p></div>`;
$("#a1").onclick=()=>go("reg");$("#a2").onclick=()=>go("facts");$("#a3").onclick=()=>go("board")}
function facts(a){a.innerHTML=`<h2>${t().fh}</h2><div class="facts">${t().F.map(f=>`<div class="fact"><b>${f[0]}</b>${f[1]}</div>`).join("")}</div>`}
async function board(a){
    const x=t();
    a.innerHTML=`<h2>${x.rh}</h2><div id="tb"><p>Yuklanmoqda...</p></div>`;
    let rows=[];
    try {
        let res = await fetch('/api/results');
        let data = await res.json();
        if(data.status === 'ok') {
            rows = data.results;
        }
    } catch(e) {}
    
    if(view!=="board")return;
    $("#tb").innerHTML=rows.length?`<div class="tw"><table><tr>${x.rk.map(h=>`<th>${h}</th>`).join("")}</tr>${rows.map((r,i)=>`<tr><td>${i+1}</td><td>${esc(r[1])}</td><td>${esc(r[3])}</td><td><b>${r[4]*10}</b></td><td>${Math.round(r[4]/r[5]*100)}%</td></tr>`).join("")}</table></div>`:`<p>${x.none}</p>`;
}
document.addEventListener("click",e=>{const b=e.target.closest("[data-v],[data-l]");if(!b)return;if(b.dataset.l){L=b.dataset.l;render()}else go(b.dataset.v)});
$("#brand").onclick=()=>go("home");
render();
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/api/submit', methods=['POST'])
def submit_result():
    try:
        data = request.json
        conn = sqlite3.con
