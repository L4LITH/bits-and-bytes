from db import add_patient, add_record, list_patients

def seed_demo_data():
    if list_patients():          # only seed an empty database
        return

    # --- Patient 1: diabetes + hypertension, 3 doctors ---
    p1 = add_patient("Ravi Kumar", "1985-03-12","self")
    add_record(p1, {"date": "2025-01-10", "doctor": "Dr. Meera Iyer", "doc_type": "prescription",
        "diagnosis": "Type 2 Diabetes",
        "medicines": [{"name": "Glucophage", "generic": "metformin", "dose": "500 mg", "frequency": "twice daily"}],
        "labs": [{"test_name": "HbA1c", "value": "8.4", "unit": "%"},
                 {"test_name": "Fasting glucose", "value": "156", "unit": "mg/dL"}]})
    add_record(p1, {"date": "2025-06-15", "doctor": "Dr. Meera Iyer", "doc_type": "prescription",
        "diagnosis": "Type 2 Diabetes - follow up",
        "medicines": [{"name": "Glucophage", "generic": "metformin", "dose": "500 mg", "frequency": "twice daily"}],
        "labs": [{"test_name": "HbA1c", "value": "7.8", "unit": "%"}]})
    add_record(p1, {"date": "2025-08-03", "doctor": "Dr. Arjun Rao", "doc_type": "prescription",
        "diagnosis": "Hypertension",
        "medicines": [{"name": "Amlodac", "generic": "amlodipine", "dose": "5 mg", "frequency": "once daily"},
                      {"name": "Glycomet", "generic": "metformin", "dose": "500 mg", "frequency": "twice daily"}],
        "labs": []})
    add_record(p1, {"date": "2025-11-20", "doctor": "Sunrise Diagnostics", "doc_type": "lab_report",
        "diagnosis": None, "medicines": [],
        "labs": [{"test_name": "HbA1c", "value": "7.2", "unit": "%"}]})
    add_record(p1, {"date": "2025-11-28", "doctor": "City Lab", "doc_type": "lab_report",
        "diagnosis": None, "medicines": [],
        "labs": [{"test_name": "HbA1c", "value": "7.3", "unit": "%"}]})

    # --- Patient 2: heart rhythm + joint pain, two doctors ---
    p2 = add_patient("Anita Sharma", "1958-07-22","Mother")
    add_record(p2, {"date": "2025-03-02", "doctor": "Dr. Kapoor", "doc_type": "prescription",
        "diagnosis": "Atrial fibrillation",
        "medicines": [{"name": "Warfarin", "generic": "warfarin", "dose": "5 mg", "frequency": "once daily"}],
        "labs": [{"test_name": "INR", "value": "2.4", "unit": ""}]})
    add_record(p2, {"date": "2025-09-10", "doctor": "Dr. Nair", "doc_type": "prescription",
        "diagnosis": "Knee osteoarthritis",
        "medicines": [{"name": "Brufen", "generic": "ibuprofen", "dose": "400 mg", "frequency": "three times daily"}],
        "labs": []})

    # --- Patient 3: asthma ---
    p3 = add_patient("Karthik Rao", "2001-11-05","Brother")
    add_record(p3, {"date": "2025-04-18", "doctor": "Dr. Singh", "doc_type": "prescription",
        "diagnosis": "Asthma",
        "medicines": [{"name": "Asthalin", "generic": "salbutamol", "dose": "100 mcg", "frequency": "as needed"},
                      {"name": "Montair", "generic": "montelukast", "dose": "10 mg", "frequency": "at night"}],
        "labs": []})