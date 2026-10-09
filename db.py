import sqlite3, json

DB = "health.db"

def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row   # rows behave like dictionaries
    return conn

def init_db():
    conn = get_conn()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, dob TEXT);
    CREATE TABLE IF NOT EXISTS records (
        id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id INTEGER,
        date TEXT, doctor TEXT, doc_type TEXT, diagnosis TEXT, raw_json TEXT);
    CREATE TABLE IF NOT EXISTS medicines (
        id INTEGER PRIMARY KEY AUTOINCREMENT, record_id INTEGER,
        name TEXT, dose TEXT, frequency TEXT);
    CREATE TABLE IF NOT EXISTS lab_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT, record_id INTEGER,
        test_name TEXT, value TEXT, unit TEXT);
    """)
    conn.commit(); conn.close()

def add_record(patient_id, data):
    """data = the dictionary Gemini returned"""
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO records (patient_id, date, doctor, doc_type, diagnosis, raw_json) VALUES (?,?,?,?,?,?)",
        (patient_id, data.get("date"), data.get("doctor"), data.get("doc_type"),
         data.get("diagnosis"), json.dumps(data)))
    rid = cur.lastrowid
    for m in data.get("medicines", []):
        conn.execute("INSERT INTO medicines (record_id, name, dose, frequency) VALUES (?,?,?,?)",
                     (rid, m.get("name"), m.get("dose"), m.get("frequency")))
    for t in data.get("labs", []):
        conn.execute("INSERT INTO lab_results (record_id, test_name, value, unit) VALUES (?,?,?,?)",
                     (rid, t.get("test_name"), t.get("value"), t.get("unit")))
    conn.commit(); conn.close()

def get_timeline(patient_id, newest_first=True):
    conn = get_conn()
    order = "DESC" if newest_first else "ASC"
    rows = conn.execute(
        f"SELECT * FROM records WHERE patient_id=? ORDER BY date {order}", (patient_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_patient(name, dob):
    conn = get_conn()
    cur = conn.execute("INSERT INTO patients (name, dob) VALUES (?,?)", (name, dob))
    pid = cur.lastrowid
    conn.commit(); conn.close()
    return pid

if __name__ == "__main__":
    init_db()
    print("Database ready!")