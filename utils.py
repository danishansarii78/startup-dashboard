import streamlit as st
import pandas as pd
import os

CACHE_FILE = "data/startups.parquet"
SOURCE_FILE = "data/startups.xlsx"

@st.cache_data(ttl=3600, show_spinner=False)
def load_data():
    """
    Loads startup data efficiently.
    1. Checks for a cached Parquet file (fast).
    2. If missing, reads the Excel file (slow), finds the header, cleans it, and caches it.
    """
    # 1. Try loading from Parquet (Fast)
    if os.path.exists(CACHE_FILE):
        try:
            return pd.read_parquet(CACHE_FILE)
        except Exception:
            pass

    # 2. Fallback to Excel (Slow)
    if not os.path.exists(SOURCE_FILE):
        st.error(f"❌ Source file not found: {SOURCE_FILE}")
        st.stop()

    with st.status("⚙️ Initial Setup: Converting data for faster performance...", expanded=True) as status:
        st.write("Reading Excel file... (This only happens once)")
        # Optimization: Read only first 50 rows to locate header
        raw_df_head = pd.read_excel(SOURCE_FILE, header=None, nrows=50)

        header_row = None
        for i in range(len(raw_df_head)):
            row_vals = raw_df_head.iloc[i].astype(str).str.lower().values
            if "company" in row_vals:
                header_row = i
                break

        if header_row is None:
            status.update(label="❌ Error", state="error")
            st.error("Could not detect header row in the first 50 rows.")
            st.stop()

        st.write("Processing full dataset...")
        # Read full file with identified header
        df = pd.read_excel(SOURCE_FILE, header=header_row)

        # Clean columns
        df.columns = (
            df.columns.astype(str)
            .str.strip()
            .str.lower()
            .str.replace(" ", "_")
            .str.replace("-", "_")
            .str.replace("(", "")
            .str.replace(")", "")
        )

        st.write("Saving optimized cache...")
        # 3. Save to Parquet for future fast loads
        try:
            df.to_parquet(CACHE_FILE, index=False)
            status.update(label="✅ Optimization Complete!", state="complete", expanded=False)
        except Exception as e:
            st.error(f"Could not save parquet cache: {e}")

    return df
