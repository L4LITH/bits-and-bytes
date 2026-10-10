# 🩺 Family Health Vault

**Hackathon:** Bits and Bytes (24-hour hackathon) · **Track:** HealthTech
**Problem statement:** Lost in Transit: Fragmented Medical Records and Repeated Care Across Providers
**Built by:** NULL POINTERS

🔗 **Live app:** https://bits-and-bytes.streamlit.app
🎥 **Demo video:** [Watch the demo](demo/demo.mp4)

**Judge login:** username `demo`, password `demo1234` (contains simulated data only)

---

## The problem

Patients with long-term conditions see many doctors, labs and pharmacies. Their records end up scattered across paper prescriptions, PDFs and chat photos. When they change doctors or reach an emergency room, the new clinician starts from scratch. This leads to repeated tests, overlapping or interacting medicines, and no secure, simple way to share history.

## Our solution

Family Health Vault is a web app where one person can keep the medical records of their whole family in one place:

1. **Upload** a photo or PDF of a prescription or lab report.
2. **AI extraction** (Google Gemini) reads it and fills in the date, doctor, diagnosis, medicines (with active ingredient) and lab values.
3. **Human review:** the user checks and corrects the extracted data before it is saved, since AI can misread documents.
4. **Timeline:** all records for each family member in one chronological view, with the original document attached.
5. **Safety alerts** are generated automatically from the stored data.
6. **Doctor summary:** a one-page PDF to hand to a clinician.

## Features

- Login and signup with per-user data separation (salted PBKDF2 password hashing, ownership checks on every data access)
- Family members with relation, add / edit / delete
- Upload images or PDFs, with review-and-edit before saving
- Original documents stored and viewable or downloadable from the timeline
- **Duplicate medicine detection** by active ingredient, so two brands of the same drug from different doctors are flagged (for example Glucophage and Glycomet are both metformin)
- **Drug interaction checks** (starter rule set, for example warfarin + ibuprofen)
- **Repeated test detection** (the same test within 30 days)
- Lab trend charts (for example HbA1c over time)
- Downloadable one-page doctor summary (PDF)
- Input validation, retry handling for API failures, and warnings for non-medical uploads

## Tech stack and disclosures

| Purpose | Tool |
|---|---|
| App framework / UI | Streamlit |
| AI document extraction | Google Gemini API (`google-genai`) |
| Database | SQLite |
| Data handling | pandas |
| PDF generation | fpdf2 |
| Config | python-dotenv |
| Hosting | Streamlit Community Cloud |

All data in the demo is simulated. No real patient information is used.

## Run it locally

```bash
git clone https://github.com/l4lith/bits-and-bytes.git
cd bits-and-bytes
pip install -r requirements.txt
```

Create a file named `.env` in the project folder:

```
GEMINI_API_KEY=your_key_here
```

Get a free key from Google AI Studio. Then run:

```bash
streamlit run app.py
```

The database (`health.db`) is created automatically on first run, and the demo account is seeded with three sample family members.

## Project structure

```
app.py        Streamlit UI (login, tabs, forms)
db.py         SQLite schema, queries, authentication, ownership checks
extract.py    Gemini document extraction with retry handling
alerts.py     Duplicate, interaction and repeated-test checks
summary.py    Doctor summary PDF generator
seed.py       Demo data
```

## Limitations

- The interaction list is a small starter rule set, not a full clinical database.
- AI-extracted data can contain errors, which is why every record is reviewed before saving.
- Alerts are for awareness only and are **not medical advice**.
- SQLite on the free hosting tier can reset when the app restarts. The demo account is re-created automatically, but other accounts may be lost.
- Allergies are not captured yet.
- Sessions are not persistent, so a page refresh requires logging in again.

## Future scope

- Integrate a clinical drug database (RxNorm / DrugBank) for complete interaction checks
- Time-limited, revocable secure share links for doctors
- Hosted database (Postgres / Supabase) and a managed auth provider
- Allergy tracking and medication reminders
- Support for regional languages and handwritten prescriptions at scale
- Installable PWA / mobile app
- Integration with national health record standards (for example ABDM)