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
        d.execute("DELETE FROM answers WHERE attempt_id IN (SELECT id FROM attempts WHERE phone=? AND finished IS NULL)", (phone,))
        d.execute("DELETE FROM attempts WHERE phone=? AND finished IS NULL", (phone,))
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
    cur = d.execute("INSERT OR IGNORE INTO answers(attempt_id,qi,choice) VALUES(?,?,?)", (a["id"], qi, ch))
    d.commit()
    return jsonify(correct=QUESTIONS[qi]["a"], already=cur.rowcount == 0)


@app.post("/api/finish")
def api_finish():
    j = request.get_json(silent=True) or {}
    a = get_attempt(j.get("token", ""))
    if not a:
        return err("bad")
    d = db()
    if a["finished"] is None:
        rows = d.execute("SELECT qi,choice FROM answers WHERE attempt_id=?", (a["id"],)).fetchall()
        score = sum(1 for r in rows if QUESTIONS[r["qi"]]["a"] == r["choice"])
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
    sql, args = "SELECT * FROM attempts WHERE finished IS NOT NULL", []
    if q:
        sql += " AND (name LIKE ? OR phone LIKE ? OR school LIKE ? OR mfy LIKE ?)"
        args += [f"%{q}%"] * 4
    return db().execute(sql + " ORDER BY score DESC, finished ASC", args).fetchall(), q


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
                           mfys=grp("mfy"), schools=grp("school"), fmt=lambda t: time.strftime("%d.%m.%Y %H:%M", time.localtime(t)))


def safe(v):  # CSV formula injection himoyasi
    s = str(v)
    return "'" + s if s[:1] in "=+-@\t\r" else s


@app.get("/admin/export.csv")
@admin_required
def export():
    rows, _ = filtered()
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["#", "F.I.Sh.", "Telefon", "Maktab", "MFY", "Ball", "Foiz", "Til", "Sana"])
    for i, r in enumerate(rows, 1):
        w.writerow([i, safe(r["name"]), r["phone"], safe(r["school"]), safe(r["mfy"]), r["score"] * 100 // r["total"],
                    round(r["score"] * 100 / r["total"]), r["lang"], time.strftime("%Y-%m-%d %H:%M", time.localtime(r["finished"]))])
    return Response("\ufeff" + out.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=natijalar.csv"})


if __name__ == "__main__":
    app.run(debug=False, port=int(os.environ.get("PORT", 8000)))
