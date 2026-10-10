from alerts import run_alerts
from db import get_patient_medicines, get_patient_labs
from seed import seed_demo_data
import streamlit as st
import pandas as pd
from summary import build_summary_pdf
from extract import extract_record
from db import (init_db, add_patient, add_record, get_timeline, list_patients,get_record_details, get_file, update_patient, delete_patient,create_user,verify_user)

init_db()
seed_demo_data()
if "user_id" not in st.session_state:
    st.title("Health Records")
    st.caption("Demo project using simulated data. Do not upload real medical records. "
           "AI-extracted data can contain errors, so please review before saving.")
    login_tab, signup_tab = st.tabs(["Log in", "Sign up"])
    with login_tab:
        u = st.text_input("Username", key="li_u")
        p = st.text_input("Password", type="password", key="li_p")
        if st.button("Log in"):
            found = verify_user(u, p)
            if found:
                st.session_state["user_id"] = found
                st.session_state["username"] = u.strip().lower()
                st.rerun()
            else:
                st.error("Wrong username or password.")
    with signup_tab:
        nu = st.text_input("Choose a username (min 3 characters)", key="su_u")
        np_ = st.text_input("Choose a password (min 6 characters)", type="password", key="su_p")
        if st.button("Create account"):
            created = create_user(nu, np_)
            if created:
                st.session_state["user_id"] = created
                st.session_state["username"] = nu.strip().lower()
                st.rerun()
            else:
                st.error("Username taken, or username/password too short.")
    st.info("Judges: log in with username `demo`, password `demo1234`.")
    st.stop()

uid = st.session_state["user_id"]
st.title("Health Records")

# ---- Sidebar: choose or create a patient ----
RELATIONS = ["Self", "Spouse", "Father", "Mother", "Son", "Daughter", "Brother", "Sister", "Other"]

with st.sidebar:
    st.header("Family members")
    st.caption(f"Logged in as **{st.session_state['username']}**")
    if st.button("Log out"):
        st.session_state.clear()
        st.rerun()

    with st.expander("Add member"):
        n = st.text_input("Name", key="new_name")
        r = st.selectbox("Relation", RELATIONS, key="new_rel")
        d = st.text_input("Date of birth (YYYY-MM-DD)", key="new_dob")
        if st.button("Add member"):
            if n.strip():
                add_patient(n.strip(), d or None, r, uid)
                st.rerun()
            else:
                st.error("Please enter a name.")

    patients = list_patients(uid)
    if not patients:
        st.info("Add a family member to begin.")
        st.stop()

    patient = st.selectbox(
        "Select member", patients,
        format_func=lambda p: f"{p['name']} ({p['relation'] or 'N/A'})")
    pid = patient["id"]

    with st.expander("Edit or remove this member"):
        en = st.text_input("Name", patient["name"], key=f"en{pid}")
        ed = st.text_input("Date of birth", patient["dob"] or "", key=f"ed{pid}")
        cur_rel = patient["relation"] if patient["relation"] in RELATIONS else "Other"
        er = st.selectbox("Relation", RELATIONS, index=RELATIONS.index(cur_rel), key=f"er{pid}")
        if st.button("Save changes", key=f"sv{pid}"):
            if en.strip():
                update_patient(pid, en.strip(), ed or None, er, uid)
                st.rerun()
            else:
                st.error("Name cannot be empty.")
        confirm = st.checkbox("Yes, delete this member and all their records", key=f"cf{pid}")
        if st.button("Delete member", key=f"dl{pid}") and confirm:
            delete_patient(pid, uid)
            st.rerun()

# ---- Upload and extract ----
st.subheader("Upload a document")
file = st.file_uploader("Prescription or lab report", type=["png", "jpg", "jpeg", "pdf"])
if file and st.button("Extract"):
    with st.spinner("Reading document..."):
        try:
            st.session_state["draft"] = extract_record(file.getvalue(), file.type)
            st.session_state["draft_file"] = (file.name, file.type, file.getvalue())
        except Exception as e:
            print(e)
            st.error("Could not read the document. Please try again.")

# ---- Review and save ----
if "draft" in st.session_state:
    d = st.session_state["draft"]
    st.subheader("Review before saving")

    # Change 4: warning for non-medical uploads
    if not (d.get("medicines") or d.get("labs") or d.get("diagnosis")):
        st.warning("Little or no medical information was found in this file. "
                   "Check that it is a prescription or lab report before saving.")

    date = st.text_input("Date (YYYY-MM-DD)", d.get("date") or "")
    doctor = st.text_input("Doctor", d.get("doctor") or "")
    diagnosis = st.text_input("Diagnosis", d.get("diagnosis") or "")
    meds = st.data_editor(
        pd.DataFrame(d.get("medicines") or [], columns=["name", "generic", "dose", "frequency"]),
        num_rows="dynamic",
    )

    if st.button("Save to records"):
        # Change 5: date validation
        from datetime import date as _d
        if date:
            try:
                _d.fromisoformat(date)
            except ValueError:
                st.error("Date must be in YYYY-MM-DD format, for example 2025-06-15.")
                st.stop()

        record = {
            "date": date or None,
            "doctor": doctor or None,
            "doc_type": d.get("doc_type"),
            "diagnosis": diagnosis or None,
            "medicines": meds.fillna("").to_dict("records"),
            "labs": d.get("labs") or [],
        }
        add_record(pid, record, st.session_state.get("draft_file"))
        del st.session_state["draft"]
        st.session_state.pop("draft_file", None)
        st.success("Saved!")

    # Change 6: discard button (same indentation as the Save button)
    if st.button("Discard draft"):
        del st.session_state["draft"]
        st.session_state.pop("draft_file", None)
        st.rerun()
    

# ---- Safety alerts ----
st.subheader("Safety alerts")
found = run_alerts(get_patient_medicines(pid, uid), get_patient_labs(pid, uid))
if not found:
    st.success("No issues found in this member's records.")
for a in found:
    box = st.error if a["level"] == "high" else st.warning
    box(f"**{a['title']}**\n\n{a['detail']}")
st.caption("Automated checks for awareness only, not medical advice. "
           "Please confirm with a doctor or pharmacist.")

# ---- Lab trends ----
st.subheader("Lab trends")
labs_all = get_patient_labs(pid, uid)
df_labs = pd.DataFrame(labs_all)

if df_labs.empty:
    st.caption("No lab results yet for this member.")
else:
    df_labs["num"] = pd.to_numeric(df_labs["value"], errors="coerce")
    df_labs = df_labs.dropna(subset=["num", "date"])
    tests = sorted(df_labs["test_name"].dropna().unique())
    if not tests:
        st.caption("No numeric lab values with dates to chart yet.")
    else:
        chosen = st.selectbox("Test", tests)
        one = df_labs[df_labs["test_name"] == chosen].sort_values("date")
        unit = one["unit"].iloc[0] or ""
        st.line_chart(one.set_index("date")["num"])
        st.caption(f"{chosen} over time ({unit})")
        st.dataframe(one[["date", "value", "unit", "doctor"]], hide_index=True)

# ---- Doctor summary ----
st.subheader("Doctor summary")
pdf_bytes = build_summary_pdf(
    patient,
    get_timeline(pid),
    get_patient_medicines(pid, uid),
    get_patient_labs(pid, uid),
    found,
)
st.download_button("Download doctor summary (PDF)", pdf_bytes,
                   file_name=f"{patient['name'].replace(' ', '_')}_summary.pdf",
                   mime="application/pdf")

# ---- Timeline ----
st.subheader("Timeline")
newest_first = st.radio("Order", ["Newest first", "Oldest first"], horizontal=True) == "Newest first"

for rec in get_timeline(pid, newest_first):
    title = f"{rec['date'] or 'No date'} - {rec['doctor'] or 'Unknown doctor'}"
    with st.expander(title):
        st.write("**Type:**", rec["doc_type"] or "Not recorded")
        st.write("**Diagnosis:**", rec["diagnosis"] or "Not recorded")
        if rec["file_name"]:
            fname, ftype, fdata = get_file(rec["id"], uid)
            if ftype and ftype.startswith("image/"):
                st.image(fdata, caption=fname)
            st.download_button("Download original", fdata, file_name=fname,mime=ftype, key=f"dl_file_{rec['id']}")

        meds, labs = get_record_details(rec["id"], uid)
        if meds:
            st.write("**Medicines**")
            st.dataframe(pd.DataFrame(meds), hide_index=True)
        if labs:
            st.write("**Lab results**")
            st.dataframe(pd.DataFrame(labs), hide_index=True)
        if not meds and not labs:
            st.caption("No medicines or lab results in this record.")