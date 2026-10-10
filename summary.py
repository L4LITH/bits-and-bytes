from datetime import date
from fpdf import FPDF


def _t(s):
    """The built-in PDF font only supports basic Latin characters, so replace others with '?'."""
    return str(s if s is not None else "").encode("latin-1", "replace").decode("latin-1")


def _age(dob):
    try:
        b = date.fromisoformat(dob)
    except (TypeError, ValueError):
        return None
    t = date.today()
    return t.year - b.year - ((t.month, t.day) < (b.month, b.day))


def build_summary_pdf(patient, records, meds, labs, alerts):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    def heading(text):
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, _t(text), new_x="LMARGIN", new_y="NEXT")

    def line(text):
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 6, _t(text), new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Patient Health Summary", new_x="LMARGIN", new_y="NEXT")

    age = _age(patient.get("dob"))
    line(f"Name: {patient['name']}   Relation: {patient.get('relation') or 'N/A'}")
    line(f"Date of birth: {patient.get('dob') or 'Not recorded'}"
         + (f"   Age: {age}" if age is not None else ""))
    line(f"Generated on: {date.today().isoformat()}")

    heading("Conditions on record")
    seen = set()
    for r in records:
        d = r.get("diagnosis")
        if d and d not in seen:
            seen.add(d)
            line(f"- {d} ({r.get('date') or 'no date'}, {r.get('doctor') or 'unknown doctor'})")
    if not seen:
        line("None recorded.")

    heading("Medicines on record (latest entry for each drug)")
    latest = {}
    for m in meds:                       # meds are sorted oldest to newest, so later entries win
        k = (m.get("generic") or m.get("name") or "").lower()
        if k:
            latest[k] = m
    for m in latest.values():
        gen = f" [{m['generic']}]" if m.get("generic") else ""
        line(f"- {m['name']}{gen} {m.get('dose') or ''} {m.get('frequency') or ''} "
             f"- {m.get('doctor') or 'unknown'}, {m.get('date') or 'no date'}")
    if not latest:
        line("None recorded.")

    heading("Latest lab results")
    latest_lab = {}
    for l in labs:
        if l.get("test_name"):
            latest_lab[l["test_name"].lower()] = l
    for l in latest_lab.values():
        line(f"- {l['test_name']}: {l.get('value') or ''} {l.get('unit') or ''} ({l.get('date') or 'no date'})")
    if not latest_lab:
        line("None recorded.")

    heading("Automated safety flags")
    for a in alerts:
        line(f"- {a['title']}: {a['detail']}")
    if not alerts:
        line("No issues found.")

    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 5, "Generated from patient-uploaded records. AI-extracted data may contain errors "
                         "and automated flags are not medical advice. Please verify with original documents.",
                   new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())