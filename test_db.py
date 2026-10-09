from db import init_db, add_patient, add_record, get_timeline

init_db()

pid = add_patient("Ravi Kumar", "1985-03-12")

fake_record = {
    "date": "2025-06-15",
    "doctor": "Dr. Meera Iyer",
    "doc_type": "prescription",
    "diagnosis": "Type 2 Diabetes",
    "medicines": [
        {"name": "Metformin", "dose": "500 mg", "frequency": "twice daily"}
    ],
    "labs": [
        {"test_name": "HbA1c", "value": "7.8", "unit": "%"}
    ]
}

add_record(pid, fake_record)

for rec in get_timeline(pid):
    print(rec["date"], "|", rec["doctor"], "|", rec["diagnosis"])

from db import get_conn
conn = get_conn()
print([dict(r) for r in conn.execute("SELECT * FROM medicines")])
print([dict(r) for r in conn.execute("SELECT * FROM lab_results")])
conn.close() 