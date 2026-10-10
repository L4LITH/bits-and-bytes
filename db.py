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
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, dob TEXT, relation TEXT);
    CREATE TABLE IF NOT EXISTS records (
        id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id INTEGER,
        date TEXT, doctor TEXT, doc_type TEXT, diagnosis TEXT, raw_json TEXT,
        file_name TEXT, file_type TEXT, file_data BLOB);
    CREATE TABLE IF NOT EXISTS medicines (
        id INTEGER PRIMARY KEY AUTOINCREMENT, record_id INTEGER,
        name TEXT, generic TEXT, dose TEXT, frequency TEXT);
    CREATE TABLE IF NOT EXISTS lab_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT, record_id INTEGER,
        test_name TEXT, value TEXT, unit TEXT);
    """)
    conn.commit(); conn.close()

def add_record(patient_id, data, file=None):
    """file = (file_name, mime_type, bytes) or None"""
    fname, ftype, fdata = file if file else (None, None, None)
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO records (patient_id, date, doctor, doc_type, diagnosis, raw_json, file_name, file_type, file_data) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (patient_id, data.get("date"), data.get("doctor"), data.get("doc_type"),
        data.get("diagnosis"), json.dumps(data), fname, ftype, fdata))
    rid = cur.lastrowid
    # ... your existing medicines and labs loops continue here ...
    for m in data.get("medicines", []):
        conn.execute(
            "INSERT INTO medicines (record_id, name, generic, dose, frequency) VALUES (?,?,?,?,?)",
            (rid, m.get("name"), m.get("generic"), m.get("dose"), m.get("frequency")))
    for t in data.get("labs", []):
        conn.execute("INSERT INTO lab_results (record_id, test_name, value, unit) VALUES (?,?,?,?)",
                     (rid, t.get("test_name"), t.get("value"), t.get("unit")))
    conn.commit(); conn.close()

def get_timeline(patient_id, newest_first=True):
    conn = get_conn()
    order = "DESC" if newest_first else "ASC"
    rows = conn.execute(
        "SELECT id, patient_id, date, doctor, doc_type, diagnosis, file_name, file_type "
        f"FROM records WHERE patient_id=? ORDER BY date {order}", (patient_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_patient(name, dob, relation=None):
    conn = get_conn()
    cur = conn.execute("INSERT INTO patients (name, dob, relation) VALUES (?,?,?)",
                       (name, dob, relation))
    pid = cur.lastrowid
    conn.commit(); conn.close()
    return pid

def list_patients():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM patients ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_record_details(record_id):
    conn = get_conn()
    meds = conn.execute(
        "SELECT name, generic, dose, frequency FROM medicines WHERE record_id=?", (record_id,)
    ).fetchall()
    labs = conn.execute(
        "SELECT test_name, value, unit FROM lab_results WHERE record_id=?", (record_id,)
    ).fetchall()
    conn.close()
    return [dict(m) for m in meds], [dict(l) for l in labs]

def get_file(record_id):
    conn = get_conn()
    r = conn.execute("SELECT file_name, file_type, file_data FROM records WHERE id=?",
                     (record_id,)).fetchone()
    conn.close()
    return (r["file_name"], r["file_type"], r["file_data"]) if r else (None, None, None)

def update_patient(pid, name, dob, relation):
    conn = get_conn()
    conn.execute("UPDATE patients SET name=?, dob=?, relation=? WHERE id=?",
                 (name, dob, relation, pid))
    conn.commit(); conn.close()

def delete_patient(pid):
    conn = get_conn()
    ids = [r["id"] for r in conn.execute("SELECT id FROM records WHERE patient_id=?", (pid,))]
    for rid in ids:
        conn.execute("DELETE FROM medicines WHERE record_id=?", (rid,))
        conn.execute("DELETE FROM lab_results WHERE record_id=?", (rid,))
    conn.execute("DELETE FROM records WHERE patient_id=?", (pid,))
    conn.execute("DELETE FROM patients WHERE id=?", (pid,))
    conn.commit(); conn.close()

if __name__ == "__main__":
    init_db()
    print("Database ready!")