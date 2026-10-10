from alerts import run_alerts
from db import get_patient_medicines, get_patient_labs
from seed import seed_demo_data
import streamlit as st
import pandas as pd
from summary import build_summary_pdf
from extract import extract_record
from db import (init_db, add_patient, add_record, get_timeline, list_patients,get_record_details, get_file, update_patient, delete_patient,create_user,verify_user)

st.set_page_config(page_title="Family Health Vault", page_icon="🩺", layout="wide")

st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.block-container {padding-top: 2rem;}
[data-testid="stMetric"] {background: #F0F7F6; border-radius: 12px; padding: 12px 16px;}
</style>
""", unsafe_allow_html=True)

init_db()
seed_demo_data()
if "user_id" not in st.session_state:
    st.title("🩺 Family Health Vault")
    st.caption("One place for your family's prescriptions, lab reports and safety checks.")
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

# ---- Load this member's data once ----
records = get_timeline(pid)
meds_all = get_patient_medicines(pid, uid)
labs_all = get_patient_labs(pid, uid)
found = run_alerts(meds_all, labs_all)

# ---- Header and summary cards ----
st.title(f"🩺 {patient['name']}")
st.caption(f"{patient['relation'] or 'Family member'} · Demo project using simulated data. "
           "Do not upload real medical records. AI-extracted data can contain errors, so please review before saving.")

if st.session_state.pop("just_saved", False):
    st.success("Record saved!")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Records", len(records))
c2.metric("Medicines", len(meds_all))
c3.metric("Lab results", len(labs_all))
c4.metric("Safety alerts", len(found))

tab_up, tab_alert, tab_lab, tab_sum, tab_time = st.tabs(
    ["📤 Upload", "⚠️ Alerts", "📈 Lab trends", "📄 Doctor summary", "🗂️ Timeline"])

# ---- Upload tab ----
with tab_up:
    file = st.file_uploader("Prescription or lab report", type=["png", "jpg", "jpeg", "pdf"])
    if file and st.button("Extract", type="primary"):
        with st.spinner("Reading document..."):
            try:
                st.session_state["draft"] = extract_record(file.getvalue(), file.type)
                st.session_state["draft_file"] = (file.name, file.type, file.getvalue())
            except Exception as e:
                print(e)
                st.error("Could not read the document. Please try again.")

    if "draft" in st.session_state:
        d = st.session_state["draft"]
        st.subheader("Review before saving")
        if not (d.get("medicines") or d.get("labs") or d.get("diagnosis")):
            st.warning("Little or no medical information was found in this file. "
                       "Check that it is a prescription or lab report before saving.")

        col_a, col_b = st.columns(2)
        date = col_a.text_input("Date (YYYY-MM-DD)", d.get("date") or "")
        doctor = col_b.text_input("Doctor", d.get("doctor") or "")
        diagnosis = st.text_input("Diagnosis", d.get("diagnosis") or "")
        meds = st.data_editor(
            pd.DataFrame(d.get("medicines") or [], columns=["name", "generic", "dose", "frequency"]),
            num_rows="dynamic", use_container_width=True)

        b1, b2 = st.columns(2)
        save = b1.button("Save to records", type="primary")
        discard = b2.button("Discard draft")

        if save:
            from datetime import date as _d
            valid = True
            if date:
                try:
                    _d.fromisoformat(date)
                except ValueError:
                    valid = False
                    st.error("Date must be in YYYY-MM-DD format, for example 2025-06-15.")
            if valid:
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
                st.session_state["just_saved"] = True
                st.rerun()

        if discard:
            del st.session_state["draft"]
            st.session_state.pop("draft_file", None)
            st.rerun()

# ---- Alerts tab ----
with tab_alert:
    if not found:
        st.success("No issues found in this member's records.")
    for a in found:
        box = st.error if a["level"] == "high" else st.warning
        box(f"**{a['title']}**\n\n{a['detail']}")
    st.caption("Automated checks for awareness only, not medical advice. "
               "Please confirm with a doctor or pharmacist.")

# ---- Lab trends tab ----
with tab_lab:
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
            st.dataframe(one[["date", "value", "unit", "doctor"]], hide_index=True,
                         use_container_width=True)

# ---- Doctor summary tab ----
with tab_sum:
    st.write("A one-page PDF with conditions, medicines, latest labs and safety flags, "
             "ready to hand to a doctor.")
    pdf_bytes = build_summary_pdf(patient, records, meds_all, labs_all, found)
    st.download_button("Download doctor summary (PDF)", pdf_bytes,
                       file_name=f"{patient['name'].replace(' ', '_')}_summary.pdf",
                       mime="application/pdf", type="primary")

# ---- Timeline tab ----
with tab_time:
    newest_first = st.radio("Order", ["Newest first", "Oldest first"], horizontal=True) == "Newest first"
    for rec in get_timeline(pid, newest_first):
        title = f"{rec['date'] or 'No date'} · {rec['doctor'] or 'Unknown doctor'}"
        with st.expander(title):
            st.write("**Type:**", rec["doc_type"] or "Not recorded")
            st.write("**Diagnosis:**", rec["diagnosis"] or "Not recorded")

            if rec["file_name"]:
                fname, ftype, fdata = get_file(rec["id"], uid)
                if ftype and ftype.startswith("image/"):
                    st.image(fdata, caption=fname)
                st.download_button("Download original", fdata, file_name=fname,
                                   mime=ftype, key=f"dl_file_{rec['id']}")

            meds, labs = get_record_details(rec["id"], uid)
            if meds:
                st.write("**Medicines**")
                st.dataframe(pd.DataFrame(meds), hide_index=True)
            if labs:
                st.write("**Lab results**")
                st.dataframe(pd.DataFrame(labs), hide_index=True)
            if not meds and not labs:
                st.caption("No medicines or lab results in this record.")