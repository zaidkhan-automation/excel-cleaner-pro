# streamlit_app.py
# Streamlit UI for Excel Cleaner backend (assumes backend at http://localhost:8001)

import streamlit as st
import requests
import json
from io import BytesIO

BACKEND_URL = "http://localhost:8001/clean"
st.set_page_config(page_title="TaskMindAI — Excel Cleaner (UI)", layout="centered")

st.title("TaskMindAI — Excel Cleaner (Diamond UI)")
st.caption("Upload a messy Excel/CSV and get a cleaned file + summary. Backend must run on port 8001.")

uploaded = st.file_uploader("Choose an Excel/CSV file", type=["csv", "xls", "xlsx"])
out_format = st.selectbox("Output format", options=["xlsx", "csv"], index=0)
run = st.button("Run Cleaner")

if uploaded is None:
    st.info("Tip: generate a sample test file with make_test_file.py or upload your file.")
else:
    st.markdown(f"*Selected:* {uploaded.name} — {uploaded.size} bytes")

if run:
    if uploaded is None:
        st.error("Upload a file first.")
    else:
        try:
            st.info("Sending file to backend...")
            files = {"file": (uploaded.name, uploaded.getvalue(), uploaded.type or "application/octet-stream")}
            params = {"out_format": out_format}
            resp = requests.post(BACKEND_URL, files=files, params=params, timeout=60)
            if resp.status_code != 200:
                st.error(f"Backend returned {resp.status_code}: {resp.text}")
            else:
                # summary might be in header X-Cleaner-Summary
                summary_raw = resp.headers.get("X-Cleaner-Summary")
                summary = None
                if summary_raw:
                    try:
                        summary = json.loads(summary_raw)
                    except Exception:
                        summary = summary_raw

                st.success("Cleaning finished. Download below.")
                filename = resp.headers.get("Content-Disposition", f"attachment; filename=cleaned_{uploaded.name}")
                # try to extract filename
                if "filename=" in filename:
                    filename = filename.split("filename=")[-1].strip().strip('"')

                content = resp.content
                st.download_button("Download cleaned file", data=content, file_name=filename, mime="application/octet-stream")
                if summary:
                    st.subheader("Processing Summary")
                    st.json(summary)
        except requests.exceptions.RequestException as e:
            st.error(f"Request failed: {e}")
