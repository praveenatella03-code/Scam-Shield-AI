import json, os, sqlite3
from datetime import datetime, timezone
def _p(): return os.getenv("DB_PATH","jobshield.db")
def conn():
    c = sqlite3.connect(_p()); c.row_factory = sqlite3.Row; return c
def init():
    with conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS analyses(id INTEGER PRIMARY KEY AUTOINCREMENT,job_title TEXT,company TEXT,
        prediction TEXT,risk_score INTEGER,risk_level TEXT,result_json TEXT,created_at TEXT)""")
def save(title,company,res):
    # Privacy: raw job text and recruiter emails are NOT stored; only the summary result.
    with conn() as c:
        return c.execute("INSERT INTO analyses(job_title,company,prediction,risk_score,risk_level,result_json,created_at) VALUES(?,?,?,?,?,?,?)",
         (title,company or "(not given)",res["prediction"],res["risk_score"],res["risk_level"],json.dumps(res),datetime.now(timezone.utc).isoformat())).lastrowid
def all_():
    with conn() as c:
        return [dict(r)|{"result":json.loads(r["result_json"])} for r in c.execute("SELECT * FROM analyses ORDER BY id DESC LIMIT 200")]
def delete(i):
    with conn() as c: return c.execute("DELETE FROM analyses WHERE id=?",(i,)).rowcount
