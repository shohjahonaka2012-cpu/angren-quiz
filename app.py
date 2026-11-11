"""Davlat bayrogʻi viktorinasi — Angren. Flask + SQLite.

Ishga tushirish:  see README.md
"""
import csv
import io
import os
import re
import secrets
import sqlite3
import time
from collections import defaultdict, deque
from functools import wraps

from flask import Flask, Response, g, jsonify, render_template, request

from questions import QUESTIONS

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("DB_PATH", os.path.join(BASE, "data", "quiz.db"))
ONE_ATTEMPT = os.environ.get("ONE_ATTEMPT_PER_PHONE", "1") == "1"
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
TOTAL = len(QUESTIONS)

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024
if os.environ.get("TRUST_PROXY") == "1":  # nginx / Caddy orqasida
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# ------------------------------------------------------------------ DB
SCHEMA = """
CREATE TABLE IF NOT EXISTS attempts(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  token TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL, phone TEXT NOT NULL, school TEXT NOT NULL, mfy TEXT NOT NULL,
  lang TEXT, created INTEGER NOT NULL, finished INTEGER, score INTEGER, total INTEGER);
CREATE TABLE IF NOT EXISTS answers(
  attempt_id INTEGER NOT NULL, qi INTEGER NOT NULL, choice INTEGER NOT NULL,
  qtext TEXT, chosen TEXT, correct_text TEXT, is_correct INTEGER, ts INTEGER,
  PRIMARY KEY(attempt_id, qi));
CREATE INDEX IF NOT EXISTS ix_phone ON attempts(phone);
"""


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH, timeout=10)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_):
    d = g.pop("db", None)
    if d is not None:
        d.close()


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.execute("PRAGMA journal_mode=WAL")
    c.executescript(SCHEMA)
    have = {r[1] for r in c.execute("PRAGMA table_info(answers)")}
    for col, typ in (("qtext", "TEXT"), ("chosen", "TEXT"), ("correct_text", "TEXT"), ("is_correct", "INTEGER"), ("ts", "INTEGER")):
        if col not in have:  # eski bazalar uchun
            c.execute(f"ALTER TABLE answers ADD COLUMN {col} {typ}")
    c.commit()
    c.close()


init_db()

# ------------------------------------------------------------ helpers
_hits = defaultdict(deque)


def limited(key, n, window):
    now, q = time.time(), _hits[key]
    while q and now - q[0] > window:
        q.popleft()
    if len(q) >= n:
        return True
    q.append(now)
    return False


def err(code, status=400):
    return jsonify(error=code), status


def clean_phone(raw):
    d = re.sub(r"\D", "", str(raw))
    if len(d) == 9:
        d = "998" + d
    return "+" + d if re.fullmatch(r"998\d{9}", d) else None


def mask_name(name):
    p = name.split()
    return f"{p[0]} {p[1][0]}." if len(p) > 1 else p[0]


@app.after_request
def headers(r):
    r.headers["X-Content-Type-Options"] = "nosniff"
    r.headers["X-Frame-Options"] = "DENY"
    r.headers["Referrer-Policy"] = "same-origin"
    r.headers["Content-Security-Policy"] = (
        "default-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src https://fonts.gstatic.com; img-src 'self' data:; frame-ancestors 'none'")
    if request.path.startswith("/api/"):
        r.headers["Cache-Control"] = "no-store"
    return r


# ---------------------------------------------------------------- pages
@app.get("/")
def index():
    return app.send_static_file("index.html")


# ------------------------------------------------------------------ API
@app.get("/api/questions")
def api_questions():
    """Savollar — toʻgʻri javobsiz."""
    return jsonify({lang: [dict(q=x[lang]["q"], o=x[lang]["o"]) for x in QUESTIONS] for lang in ("uz", "ru")})


@app.post("/api/start")
def api_start():
    if limited("start:" + (request.remote_addr or "?"), 30, 3600):
        return err("rate", 429)
    j = request.get_json(silent=True) or {}
    name = " ".join(str(j.get("name", "")).split())
    school = " ".join(str(j.get("school", "")).split())
    mfy = " ".join(str(j.get("mfy", "")).split())
    phone = clean_phone(j.get("phone", ""))
    words = [w for w in name.split() if len(w) > 1]
    if not (len(words) >= 2 and len(name) <= 100 and phone and 2 <= len(school) <= 100 and 2 <= len(mfy) <= 100):
        return err("bad")
    lang = "ru" if j.get("lang") == "ru" else "uz"
    d = db()
    if ONE_ATTEMPT:
        if d.execute("SELECT 1 FROM attempts WHERE phone=? AND finished IS NOT NULL", (phone,)).fetchone():
            return err("dup", 409)
    token = secrets.token_urlsafe(24)
    d.execute("INSERT INTO attempts(token,name,phone,school,mfy,lang,created,total) VALUES(?,?,?,?,?,?,?,?)",
              (token, name, phone, school, mfy, lang, int(time.time()), TOTAL))
    d.commit()
    return jsonify(token=token, total=TOTAL)


def get_attempt(token):
    return db().execute("SELECT * FROM attempts WHERE token=?", (str(token),)).fetchone()


@app.post("/api/answer")
def api_answer():
    j = request.get_json(silent=True) or {}
    a = get_attempt(j.get("token", ""))
    qi, ch = j.get("q"), j.get("choice")
    if not a or a["finished"] is not None:
        return err("bad")
    if not (isinstance(qi, int) and isinstance(ch, int) and 0 <= qi < TOTAL and 0 <= ch < 4):
        return err("bad")
    d = db()
    q = QUESTIONS[qi]
    lg = "ru" if j.get("lang") == "ru" else (a["lang"] or "uz")
    cur = d.execute(
        "INSERT OR IGNORE INTO answers(attempt_id,qi,choice,qtext,chosen,correct_text,is_correct,ts) VALUES(?,?,?,?,?,?,?,?)",
        (a["id"], qi, ch, q[lg]["q"], q[lg]["o"][ch], q[lg]["o"][q["a"]], int(ch == q["a"]), int(time.time())))
    d.commit()
    return jsonify(correct=q["a"], already=cur.rowcount == 0)


@app.post("/api/finish")
def api_finish():
    j = request.get_json(silent=True) or {}
    a = get_attempt(j.get("token", ""))
    if not a:
        return err("bad")
    d = db()
    if a["finished"] is None:
        score = d.execute("SELECT COALESCE(SUM(is_correct),0) FROM answers WHERE attempt_id=?", (a["id"],)).fetchone()[0]
        d.execute("UPDATE attempts SET finished=?, score=?, total=? WHERE id=?", (int(time.time()), score, TOTAL, a["id"]))
        d.commit()
    else:
        score = a["score"]
    return jsonify(score=score, total=TOTAL, percent=round(score * 100 / TOTAL))


@app.get("/api/board")
def api_board():
    rows = db().execute(
        "SELECT name,school,score,total FROM attempts WHERE finished IS NOT NULL "
        "ORDER BY score DESC, finished ASC LIMIT 100").fetchall()
    return jsonify(rows=[dict(name=mask_name(r["name"]), school=r["school"], score=r["score"], total=r["total"]) for r in rows])


# ---------------------------------------------------------------- admin
def admin_required(f):
    @wraps(f)
    def wrap(*a, **k):
        if not ADMIN_PASSWORD:
            return Response("ADMIN_PASSWORD oʻrnatilmagan — admin panel oʻchirilgan.", 503)
        au = request.authorization
        ok = au and secrets.compare_digest(au.username or "", ADMIN_USER) and secrets.compare_digest(au.password or "", ADMIN_PASSWORD)
        if not ok:
            return Response("Login kerak", 401, {"WWW-Authenticate": 'Basic realm="Admin"'})
        return f(*a, **k)
    return wrap


def filtered():
    q = request.args.get("q", "").strip()
    sql, args = "SELECT * FROM attempts WHERE 1=1" + ("" if request.args.get("all") == "1" else " AND finished IS NOT NULL"), []
    if q:
        sql += " AND (name LIKE ? OR phone LIKE ? OR school LIKE ? OR mfy LIKE ?)"
        args += [f"%{q}%"] * 4
    return db().execute(sql + " ORDER BY score DESC, finished ASC, created DESC", args).fetchall(), q


def dur(sec):
    if sec is None or sec < 0:
        return "—"
    sec = int(sec)
    return f"{sec // 60} daq {sec % 60} son" if sec >= 60 else f"{sec} son"


def timed(attempt, answers):
    """Har bir javob uchun sarflangan soniyalar (oldingi javob yoki boshlanishdan boshlab)."""
    out, prev = [], attempt["created"]
    for x in sorted(answers, key=lambda r: (r["ts"] or 0, r["qi"])):
        d = dict(x)
        d["sec"] = (x["ts"] - prev) if x["ts"] else None
        prev = x["ts"] or prev
        out.append(d)
    return sorted(out, key=lambda r: r["qi"])


def fmt(t):
    return time.strftime("%d.%m.%Y %H:%M", time.localtime(t)) if t else "—"


@app.get("/admin/attempt/<int:aid>")
@admin_required
def attempt(aid):
    d = db()
    a = d.execute("SELECT * FROM attempts WHERE id=?", (aid,)).fetchone()
    if not a:
        return Response("Topilmadi", 404)
    ans = timed(a, d.execute("SELECT * FROM answers WHERE attempt_id=?", (aid,)).fetchall())
    others = d.execute("SELECT * FROM attempts WHERE phone=? ORDER BY created", (a["phone"],)).fetchall()
    total_sec = (a["finished"] - a["created"]) if a["finished"] else None
    avg_sec = round(total_sec / len(ans)) if total_sec is not None and ans else None
    return render_template("attempt.html", a=a, ans=ans, fmt=fmt, dur=dur, total=TOTAL, others=others,
                           total_sec=total_sec, avg_sec=avg_sec)


@app.get("/admin/answers.csv")
@admin_required
def answers_csv():
    """Uzun format: har bir ishtirokchining har bir savoli bir qatorda (butun tarix)."""
    d = db()
    secs = {}
    for a in d.execute("SELECT * FROM attempts").fetchall():
        for x in timed(a, d.execute("SELECT * FROM answers WHERE attempt_id=?", (a["id"],)).fetchall()):
            secs[(a["id"], x["qi"])] = x["sec"]
    rows = d.execute(
        "SELECT a.id, a.name, a.phone, a.school, a.mfy, a.finished, x.qi, x.qtext, x.chosen, x.correct_text, x.is_correct, x.ts "
        "FROM attempts a JOIN answers x ON x.attempt_id=a.id ORDER BY a.id, x.qi").fetchall()
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["Urinish", "F.I.Sh.", "Telefon", "Maktab", "MFY", "Yakunlangan", "Savol №", "Savol", "Javobi", "Toʻgʻri javob", "Natija", "Vaqt", "Sarflangan soniya"])
    for r in rows:
        w.writerow([r["id"], safe(r["name"]), r["phone"], safe(r["school"]), safe(r["mfy"]), "ha" if r["finished"] else "yoʻq",
                    r["qi"] + 1, safe(r["qtext"] or ""), safe(r["chosen"] or ""), safe(r["correct_text"] or ""),
                    "toʻgʻri" if r["is_correct"] else "xato", fmt(r["ts"]), secs.get((r["id"], r["qi"]), "")])
    return Response("\ufeff" + out.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=javoblar-tarixi.csv"})


@app.get("/admin")
@admin_required
def admin():
    rows, q = filtered()
    d = db()
    grp = lambda col: d.execute(
        f"SELECT MIN({col}) AS k, COUNT(*) AS n, AVG(score*100.0/total) AS avg FROM attempts "
        f"WHERE finished IS NOT NULL GROUP BY LOWER(TRIM({col})) ORDER BY avg DESC, n DESC LIMIT 50").fetchall()
    stats = d.execute("SELECT COUNT(*) AS n, AVG(score*100.0/total) AS avg FROM attempts WHERE finished IS NOT NULL").fetchone()
    started = d.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]
    return render_template("admin.html", rows=rows[:500], total_rows=len(rows), q=q, stats=stats, started=started,
                           mfys=grp("mfy"), schools=grp("school"), fmt=fmt, dur=dur, all=request.args.get("all") == "1")


def safe(v):  # CSV formula injection himoyasi
    s = str(v)
    return "'" + s if s[:1] in "=+-@\t\r" else s


@app.get("/admin/export.csv")
@admin_required
def export():
    rows, _ = filtered()
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["#", "F.I.Sh.", "Telefon", "Maktab", "MFY", "Ball", "Foiz", "Til", "Boshlagan", "Yakunlagan", "Davomiyligi (soniya)"])
    for i, r in enumerate(rows, 1):
        w.writerow([i, safe(r["name"]), r["phone"], safe(r["school"]), safe(r["mfy"]), r["score"] * 100 // r["total"],
                    round(r["score"] * 100 / r["total"]), r["lang"], fmt(r["created"]), fmt(r["finished"]), r["finished"] - r["created"]]
                  if r["finished"] else [i, safe(r["name"]), r["phone"], safe(r["school"]), safe(r["mfy"]), "", "", r["lang"], fmt(r["created"]), "tugatmagan", ""])
    return Response("\ufeff" + out.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=natijalar.csv"})


if __name__ == "__main__":
    app.run(debug=False, port=int(os.environ.get("PORT", 8000)))
