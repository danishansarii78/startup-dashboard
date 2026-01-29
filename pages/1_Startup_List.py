import streamlit as st
import pandas as pd
import re

st.set_page_config(layout="wide")

# -------------------------------------------------
# DATA LOADER
# -------------------------------------------------

@st.cache_data
def load_data():
    raw_df = pd.read_excel("data/startups.xlsx", header=None)

    header_row = None
    for i in range(len(raw_df)):
        if "company" in raw_df.iloc[i].astype(str).str.lower().values:
            header_row = i
            break

    if header_row is None:
        st.error("❌ Could not detect header row")
        st.stop()

    df = pd.read_excel("data/startups.xlsx", header=header_row)

    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("-", "_")
        .str.replace("(", "")
        .str.replace(")", "")
    )

    return df


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
COL_SECTOR = find_col(["sector", "industry"])
COL_CITY = find_col(["city"])
COL_TIER = find_col(["tier"])
COL_FUNDING_LEVEL = find_col(["funding_level", "stage"])
COL_FUNDING = find_col(["funding_received", "amount"])
COL_HOT = find_col(["hot"])
COL_KEYWORDS = find_col(["key"])

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


df["_funding_numeric"] = (
    df[COL_FUNDING].apply(parse_funding)
    if COL_FUNDING else None
)

# -------------------------------------------------
# SIDEBAR FILTERS
# -------------------------------------------------

st.sidebar.header("🔍 Filters")

sector_filter = st.sidebar.multiselect(
    "Sector",
    sorted(df[COL_SECTOR].dropna().unique())
) if COL_SECTOR else []

city_filter = st.sidebar.multiselect(
    "City",
    sorted(df[COL_CITY].dropna().unique())
) if COL_CITY else []

tier_filter = st.sidebar.multiselect(
    "Tier",
    sorted(df[COL_TIER].dropna().unique())
) if COL_TIER else []

hot_filter = st.sidebar.multiselect(
    "Hot Startup",
    sorted(df[COL_HOT].dropna().unique())
) if COL_HOT else []

keyword = st.sidebar.text_input("Keyword Search")

# -------------------------------------------------
# FUNDING CONTROLS (FIXED)
# -------------------------------------------------

st.sidebar.divider()
st.sidebar.markdown("## 💰 Funding Received")

include_unfunded = st.sidebar.checkbox(
    "Include startups with no disclosed funding",
    value=True,
    key="include_unfunded"
)

unfunded_only = st.sidebar.checkbox(
    "Show unfunded startups only",
    value=False,
    key="unfunded_only"
)

if unfunded_only:
    include_unfunded = True

numeric_funding = df["_funding_numeric"].dropna()
funding_range = None

if not numeric_funding.empty and not unfunded_only:
    min_f, max_f = int(numeric_funding.min()), int(numeric_funding.max())

    if min_f < max_f:
        funding_range = st.sidebar.slider(
            "Funding Amount ($)",
            min_f,
            max_f,
            (min_f, max_f),
            step=max(10_000, int((max_f - min_f) / 100)),
            key="funding_slider"
        )
else:
    st.sidebar.info("No numeric funding data")

# -------------------------------------------------
# APPLY FILTERS
# -------------------------------------------------

filtered_df = df.copy()

if sector_filter:
    filtered_df = filtered_df[filtered_df[COL_SECTOR].isin(sector_filter)]

if city_filter:
    filtered_df = filtered_df[filtered_df[COL_CITY].isin(city_filter)]

if tier_filter:
    filtered_df = filtered_df[filtered_df[COL_TIER].isin(tier_filter)]

if hot_filter:
    filtered_df = filtered_df[filtered_df[COL_HOT].isin(hot_filter)]

if keyword and COL_KEYWORDS:
    filtered_df = filtered_df[
        filtered_df[COL_KEYWORDS]
        .astype(str)
        .str.contains(keyword, case=False, na=False)
    ]

# ---------------- FUNDING FILTER LOGIC ----------------

if st.session_state.get("unfunded_only"):
    filtered_df = filtered_df[filtered_df["_funding_numeric"].isna()]

elif funding_range:
    if st.session_state.get("include_unfunded"):
        filtered_df = filtered_df[
            (filtered_df["_funding_numeric"].isna()) |
            (
                (filtered_df["_funding_numeric"] >= funding_range[0]) &
                (filtered_df["_funding_numeric"] <= funding_range[1])
            )
        ]
    else:
        filtered_df = filtered_df[
            (filtered_df["_funding_numeric"].notna()) &
            (filtered_df["_funding_numeric"] >= funding_range[0]) &
            (filtered_df["_funding_numeric"] <= funding_range[1])
        ]

# -------------------------------------------------
# TABLE
# -------------------------------------------------

st.title("📋 Startup Explorer")
st.subheader(f"Showing {len(filtered_df)} startups")

display_cols = [
    COL_COMPANY, COL_SECTOR, COL_CITY,
    COL_TIER, COL_FUNDING_LEVEL, COL_FUNDING, COL_HOT
]
display_cols = [c for c in display_cols if c]

st.dataframe(
    filtered_df[display_cols],
    use_container_width=True,
    height=500
)

# -------------------------------------------------
# LINK TO PROFILE PAGE
# -------------------------------------------------

st.divider()
st.subheader("📌 View Startup Profile")

selected_company = st.selectbox(
    "Select a startup",
    sorted(filtered_df[COL_COMPANY].dropna().unique())
)

if st.button("➡ Open Startup Profile"):
    st.session_state["selected_startup"] = selected_company
    st.switch_page("pages/2_Startup_Profile.py")
