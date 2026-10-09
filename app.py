from db import init_db, add_patient, add_record, get_timeline, list_patients, get_record_details
import streamlit as st
import pandas as pd
from db import init_db, add_patient, add_record, get_timeline, list_patients
from extract import extract_record

init_db()
st.title("Health Records")

# ---- Sidebar: choose or create a patient ----
with st.sidebar:
    st.header("Patient")
    new_name = st.text_input("New patient name")
    if st.button("Add patient") and new_name:
        add_patient(new_name, None)
        st.rerun()
    patients = list_patients()
    if not patients:
        st.info("Add a patient to begin.")
        st.stop()
    patient = st.selectbox("Select patient", patients, format_func=lambda p: p["name"])
    pid = patient["id"]

# ---- Upload and extract ----
st.subheader("Upload a document")
file = st.file_uploader("Prescription or lab report", type=["png", "jpg", "jpeg"])
if file and st.button("Extract"):
    with st.spinner("Reading document..."):
        try:
            st.session_state["draft"] = extract_record(file.getvalue(), file.type)
        except Exception as e:
            print(e)
            st.error("Could not read the document. Please try again.")

# ---- Review and save ----
if "draft" in st.session_state:
    d = st.session_state["draft"]
    st.subheader("Review before saving")
    date = st.text_input("Date (YYYY-MM-DD)", d.get("date") or "")
    doctor = st.text_input("Doctor", d.get("doctor") or "")
    diagnosis = st.text_input("Diagnosis", d.get("diagnosis") or "")
    meds = st.data_editor(
        pd.DataFrame(d.get("medicines") or [], columns=["name", "dose", "frequency"]),
        num_rows="dynamic",
    )
    if st.button("Save to records"):
        record = {
            "date": date or None,
            "doctor": doctor or None,
            "doc_type": d.get("doc_type"),
            "diagnosis": diagnosis or None,
            "medicines": meds.fillna("").to_dict("records"),
            "labs": d.get("labs") or [],
        }
        add_record(pid, record)
        del st.session_state["draft"]
        st.success("Saved!")

# ---- Timeline ----
st.subheader("Timeline")
newest_first = st.radio("Order", ["Newest first", "Oldest first"], horizontal=True) == "Newest first"

for rec in get_timeline(pid, newest_first):
    title = f"{rec['date'] or 'No date'} - {rec['doctor'] or 'Unknown doctor'}"
    with st.expander(title):
        st.write("**Type:**", rec["doc_type"] or "Not recorded")
        st.write("**Diagnosis:**", rec["diagnosis"] or "Not recorded")

        meds, labs = get_record_details(rec["id"])
        if meds:
            st.write("**Medicines**")
            st.dataframe(pd.DataFrame(meds), hide_index=True)
        if labs:
            st.write("**Lab results**")
            st.dataframe(pd.DataFrame(labs), hide_index=True)
        if not meds and not labs:
            st.caption("No medicines or lab results in this record.")