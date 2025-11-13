# diamond_ui.py
"""
TaskMindAI Excel Cleaner (SaaS demo gating)
- 3 free demos per email, then show payment required flow.
- Stores demo counts in demo_usage.json (server-side file).
- For production: replace demo tracking with DB + email verification.
"""

import os
import io
import json
import time
from datetime import datetime
from typing import Dict

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# ---------- CONFIG ----------
st.set_page_config(page_title="TaskMindAI — Excel Cleaner (SaaS Demo)",
                   layout="centered", page_icon="🔷")

PAYMENT_LINK = os.getenv("TASKMIND_PAYMENT_LINK", "https://rzp.io/rzp/taskmindai-payment")
DEMO_STORAGE = os.getenv("DEMO_USAGE_FILE", "demo_usage.json")
MAX_FREE_DEMOS = int(os.getenv("MAX_FREE_DEMOS", "3"))
PREVIEW_ROWS = int(os.getenv("PREVIEW_ROWS", "8"))

# make demo storage file if missing
if not os.path.exists(DEMO_STORAGE):
    try:
        with open(DEMO_STORAGE, "w") as f:
            json.dump({}, f)
    except Exception:
        # ignore write errors for now (permissions)
        pass


# ---------- demo storage helpers ----------
def load_demo_usage() -> Dict[str, Dict]:
    try:
        with open(DEMO_STORAGE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def save_demo_usage(record: Dict[str, Dict]):
    tmp = DEMO_STORAGE + ".tmp"
    try:
        with open(tmp, "w") as f:
            json.dump(record, f, indent=2)
        os.replace(tmp, DEMO_STORAGE)
    except Exception:
        # fallback: best-effort, not fatal for demo
        with open(DEMO_STORAGE, "w") as f:
            json.dump(record, f, indent=2)


def get_user_record(email: str) -> Dict:
    users = load_demo_usage()
    return users.get(email.lower(), {"count": 0, "last_used": None})


def increment_demo(email: str, increment: int = 1) -> int:
    email = email.lower()
    users = load_demo_usage()
    rec = users.get(email, {"count": 0, "last_used": None})
    rec["count"] = int(rec.get("count", 0)) + increment
    rec["last_used"] = datetime.utcnow().isoformat()
    users[email] = rec
    save_demo_usage(users)
    return rec["count"]


# ---------- helpers ----------
def read_file_to_df(uploaded_file) -> pd.DataFrame:
    if uploaded_file is None:
        return pd.DataFrame()
    name = uploaded_file.name.lower()
    try:
        if name.endswith(".csv"):
            return pd.read_csv(uploaded_file)
        else:
            return pd.read_excel(uploaded_file)
    except Exception:
        uploaded_file.seek(0)
        return pd.read_csv(uploaded_file, encoding="latin1", on_bad_lines="skip")


def make_sample_file() -> bytes:
    rows = [
        ["Name", "Email", "Join Date", "Salary", "Department"],
        ["zaid khan", "zaidkhan@", "01/02/25", "50000", "Sales"],
        ["Ahmed", "ahmed123", "2025-2-1", "₹45,000", "Sales"],
        ["Sarah", "sarah.k@", "Feb 2 2025", "48 000", "Marketing"],
        ["Imran", "imran@taskmindai.r", "02-02-25", "₹60,000", "Tech"],
    ]
    df = pd.DataFrame(rows[1:], columns=rows[0])
    bio = io.BytesIO()
    df.to_excel(bio, index=False)
    return bio.getvalue()


def download_button_bytes(data_bytes: bytes, filename: str, label: str):
    st.download_button(label, data=data_bytes, file_name=filename)


def open_payment_in_new_tab(link: str):
    safe = link.replace("'", "\\'")
    js = f"window.open('{safe}', '_blank')"
    components.html(f"<script>{js}</script>", height=0)


# ---------- UI ----------
st.title("TaskMindAI — Excel Cleaner (SaaS demo)")
st.write("Try 3 demos free. After that a quick setup fee unlocks more runs and features.")
st.markdown("---")

col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("Your account / demo usage")
    email = st.text_input("Enter your email (we use this to track demo usage)", placeholder="you@company.com").strip().lower()
    if not email:
        st.info("Enter an email to start demo runs. Demos are counted per email address.")
    else:
        rec = get_user_record(email)
        used = rec.get("count", 0)
        st.success(f"Free demos used: {used} / {MAX_FREE_DEMOS}")
        if used >= MAX_FREE_DEMOS:
            st.warning("You have exhausted your free demos. Please pay to continue using the demo or contact us.")
            if st.button("Pay now to unlock (₹10,000)"):
                open_payment_in_new_tab(PAYMENT_LINK)
        else:
            st.write("You still have free demos left. Good. Use them wisely.")

    st.markdown("### Upload / Sample")
    uploaded = st.file_uploader("Upload file (.csv, .xlsx)", type=["csv", "xlsx"], accept_multiple_files=False)

    # Sample generator increments demo when downloaded
    if st.button("Generate & download sample (consumes 1 demo)"):
        if not email:
            st.error("Please enter your email before generating the sample.")
        else:
            rec = get_user_record(email)
            if rec["count"] >= MAX_FREE_DEMOS:
                st.error("No free demos left. Please pay to continue.")
            else:
                sample_bytes = make_sample_file()
                download_button_bytes(sample_bytes, f"taskmind_sample_{datetime.utcnow().strftime('%Y%m%d')}.xlsx", "Download sample file")
                new_count = increment_demo(email)
                st.success(f"Sample generated. Free demos used: {new_count}/{MAX_FREE_DEMOS}")

    st.markdown("### Cleaning options")
    remove_duplicates = st.checkbox("Remove duplicate full rows", value=True)
    normalize_emails = st.checkbox("Normalize emails (trim / lowercase)", value=True)
    normalize_phones = st.checkbox("Normalize phone numbers", value=True)
    normalize_currency = st.checkbox("Normalize currency/salary to numeric", value=True)
    parse_dates = st.checkbox("Parse date columns (join_date → yyyy-mm-dd)", value=True)

    st.markdown("---")
    st.write("Want unlimited runs, SSO, team seats, custom mapping? Pay to upgrade and we'll set it up.")
    if st.button("Pay for setup & upgrade"):
        open_payment_in_new_tab(PAYMENT_LINK)

with col2:
    st.subheader("Preview & Run")
    df = read_file_to_df(uploaded) if uploaded is not None else pd.DataFrame()
    if df.empty:
        st.info("No file loaded. Upload a file or generate the sample.")
    else:
        st.write(f"Previewing first {PREVIEW_ROWS} rows")
        st.dataframe(df.head(PREVIEW_ROWS), use_container_width=True)

    if not df.empty and st.button("Run quick clean & download (consumes 1 demo)"):
        if not email:
            st.error("Enter your email before running a demo.")
        else:
            rec = get_user_record(email)
            if rec["count"] >= MAX_FREE_DEMOS:
                st.error("No free demos left. Please pay to continue.")
            else:
                st.info("Running quick cleaning...")
                work = df.copy()
                work.columns = [str(c).strip() for c in work.columns]

                if remove_duplicates:
                    work = work.drop_duplicates()

                if normalize_emails:
                    for col in work.columns:
                        if "email" in col.lower():
                            work[col] = work[col].astype(str).str.strip().str.lower()

                if normalize_phones:
                    for col in work.columns:
                        if any(k in col.lower() for k in ("phone", "mobile", "contact")):
                            work[col] = work[col].astype(str).str.replace(r"\D+", "", regex=True)
                            work[col] = work[col].apply(lambda x: x[-10:] if len(x) > 10 else x)

                if normalize_currency:
                    for col in work.columns:
                        if any(k in col.lower() for k in ("salary", "amount", "amt", "price")):
                            work[col + "_numeric"] = pd.to_numeric(
                                work[col].astype(str).str.replace(r"[^\d.-]", "", regex=True).str.replace(r"\s+", "", regex=True),
                                errors="coerce"
                            )

                if parse_dates:
                    for col in work.columns:
                        if any(k in col.lower() for k in ("date", "join", "joined", "dob")):
                            work[col + "_iso"] = pd.to_datetime(work[col], errors="coerce").dt.strftime("%Y-%m-%d")

                st.success("Cleaning complete — preview below")
                st.dataframe(work.head(PREVIEW_ROWS), use_container_width=True)

                buf = io.BytesIO()
                work.to_excel(buf, index=False)
                buf.seek(0)

                download_button_bytes(buf.read(), f"cleaned_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.xlsx", "Download cleaned .xlsx")

                new_count = increment_demo(email)
                st.success(f"Demo consumed. Free demos used: {new_count}/{MAX_FREE_DEMOS}")
                if new_count >= MAX_FREE_DEMOS:
                    st.warning("You reached the free demo limit. To continue pay below.")
                    if st.button("Pay now to unlock more runs"):
                        open_payment_in_new_tab(PAYMENT_LINK)

st.markdown("---")
st.caption("Demo usage is tracked by email in demo_usage.json on the server. For prod use a proper DB and a verified signup flow.")
