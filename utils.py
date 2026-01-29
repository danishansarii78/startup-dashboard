import streamlit as st
import pandas as pd
import os

CACHE_FILE = "data/startups.parquet"
SOURCE_FILE = "data/startups.xlsx"

@st.cache_data(ttl=3600, show_spinner=False)
def load_data():
    """
    Fast loader:
    1) Load from Parquet if exists
    2) Else convert Excel -> Parquet safely
    """

    # ------------------ FAST PATH ------------------
    if os.path.exists(CACHE_FILE):
        try:
            return pd.read_parquet(CACHE_FILE)
        except Exception:
            os.remove(CACHE_FILE)

    # ------------------ FALLBACK -------------------
    if not os.path.exists(SOURCE_FILE):
        st.error(f"❌ Source file not found: {SOURCE_FILE}")
        st.stop()

    with st.status("⚙️ Initial Setup: Optimizing data for speed...", expanded=True) as status:
        st.write("Scanning header row...")

        raw_head = pd.read_excel(SOURCE_FILE, header=None, nrows=50)
        header_row = None

        for i in range(len(raw_head)):
            if "company" in raw_head.iloc[i].astype(str).str.lower().values:
                header_row = i
                break

        if header_row is None:
            status.update(label="❌ Header not found", state="error")
            st.stop()

        st.write("Loading full Excel...")
        df = pd.read_excel(SOURCE_FILE, header=header_row)

        # ---------------- CLEAN COLUMNS ----------------
        df.columns = (
            df.columns.astype(str)
            .str.strip()
            .str.lower()
            .str.replace(" ", "_")
            .str.replace("-", "_")
            .str.replace("(", "")
            .str.replace(")", "")
        )

        st.write("Normalizing data types...")

        # Remove poison values that crash Arrow
        df = df.replace(["-", "—", "None", "nan", "NaN"], "")
        df = df.fillna("").astype(str)

        st.write("Saving fast cache...")
        df.to_parquet(CACHE_FILE, engine="pyarrow", index=False)

        status.update(label="✅ Data Optimized & Cached!", state="complete", expanded=False)

    return df
