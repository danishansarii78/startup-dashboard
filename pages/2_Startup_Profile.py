import streamlit as st
import pandas as pd
import re
import plotly.express as px
from utils import load_data

st.set_page_config(layout="wide")

# -------------------------------------------------
# DATA LOADER
# -------------------------------------------------

df = load_data()

# -------------------------------------------------
# COLUMN DETECTION
# -------------------------------------------------

def find_col(keys):
    for c in df.columns:
        for k in keys:
            if k in c:
                return c
    return None


COL_COMPANY = find_col(["company"])
COL_SECTOR = find_col(["sector"])
COL_CITY = find_col(["city"])
COL_FUNDING_LEVEL = find_col(["funding_level", "stage"])
COL_FUNDING = find_col(["funding_received"])
COL_HOT = find_col(["hot"])
COL_DESCRIPTION = find_col(["description"])
COL_FOUNDER = find_col(["founder"])
COL_EMAIL = find_col(["email"])
COL_PHONE = find_col(["contact", "phone"])

# -------------------------------------------------
# FUNDING PARSER
# -------------------------------------------------

def parse_funding(val):
    if pd.isna(val):
        return None
    v = str(val).lower()
    num = re.findall(r"[\d.]+", v)
    if not num:
        return None
    num = float(num[0])
    if "cr" in v:
        return num * 10_000_000
    if "m" in v:
        return num * 1_000_000
    if "k" in v:
        return num * 1_000
    return num


df["_funding_numeric"] = df[COL_FUNDING].apply(parse_funding) if COL_FUNDING else None

# -------------------------------------------------
# STARTUP SELECTION (LINKED)
# -------------------------------------------------

default_startup = st.session_state.get("selected_startup")

startup_list = sorted(df[COL_COMPANY].dropna().unique())

startup_name = st.selectbox(
    "Select Startup",
    startup_list,
    index=startup_list.index(default_startup)
    if default_startup in startup_list else 0
)

st.session_state["selected_startup"] = startup_name

startup = df[df[COL_COMPANY] == startup_name].iloc[0]

# -------------------------------------------------
# PROFILE VIEW
# -------------------------------------------------

st.title("🏢 Startup Profile")

c1, c2, c3 = st.columns(3)

with c1:
    st.metric("Sector", startup[COL_SECTOR])
    st.metric("City", startup[COL_CITY])

with c2:
    st.metric("Funding Stage", startup[COL_FUNDING_LEVEL])
    st.metric("Hot Startup", startup[COL_HOT])

with c3:
    if pd.notna(startup["_funding_numeric"]):
        st.metric(
            "Funding Raised",
            f"$ {startup['_funding_numeric']/1_000_000:.2f}M"
        )
    else:
        st.metric("Funding Raised", "Not disclosed")

# -------------------------------------------------
# FOUNDERS
# -------------------------------------------------

st.subheader("👤 Founders & Contact")

if COL_FOUNDER and pd.notna(startup[COL_FOUNDER]):
    st.write(f"**Founders:** {startup[COL_FOUNDER]}")

if COL_EMAIL and pd.notna(startup[COL_EMAIL]):
    st.write(f"📧 {startup[COL_EMAIL]}")

if COL_PHONE and pd.notna(startup[COL_PHONE]):
    st.write(f"📞 {startup[COL_PHONE]}")

# -------------------------------------------------
# DESCRIPTION
# -------------------------------------------------

if COL_DESCRIPTION and pd.notna(startup[COL_DESCRIPTION]):
    st.subheader("📝 Company Description")
    st.write(startup[COL_DESCRIPTION])
