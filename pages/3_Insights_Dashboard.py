import streamlit as st
import pandas as pd
import plotly.express as px

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
        st.error("❌ Could not detect header row containing 'Company'")
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
# COLUMN AUTO-DETECTION
# -------------------------------------------------

def find_col(keys):
    for c in df.columns:
        for k in keys:
            if k in c:
                return c
    return None


COL_SECTOR = find_col(["sector", "industry"])
COL_CITY = find_col(["city", "location"])
COL_FOUNDING_YEAR = find_col(["founding_year", "founded", "year"])
COL_FUNDING_LEVEL = find_col(["funding_level", "stage"])
COL_FOUNDER_TYPE = find_col(["founder_type", "gender", "type"])

# -------------------------------------------------
# PAGE HEADER
# -------------------------------------------------

st.title("📊 Insights Dashboard")
st.caption("Ecosystem-level startup intelligence")
st.divider()

# -------------------------------------------------
# PIE — SECTOR DISTRIBUTION
# -------------------------------------------------

if COL_SECTOR:
    counts = df[COL_SECTOR].value_counts()
    top = counts.head(10)
    others = counts.iloc[10:].sum()

    pie_data = top.copy()
    if others > 0:
        pie_data["Others"] = others

    pie_df = pie_data.reset_index()
    pie_df.columns = ["Sector", "Count"]

    fig = px.pie(
        pie_df,
        names="Sector",
        values="Count",
        title="Startup Distribution by Sector (Top 10 + Others)"
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("⬇️ Use the camera icon to download")
else:
    st.warning("⚠️ Sector column not found")

st.divider()

# -------------------------------------------------
# LINE — FOUNDING YEAR
# -------------------------------------------------

if COL_FOUNDING_YEAR:
    ydf = df.copy()
    ydf["_year"] = pd.to_numeric(ydf[COL_FOUNDING_YEAR], errors="coerce")

    ydf = (
        ydf[ydf["_year"].notna()]
        .groupby("_year")
        .size()
        .reset_index(name="Companies")
        .sort_values("_year")
    )

    ydf = ydf[(ydf["_year"] >= 2000) & (ydf["_year"] <= pd.Timestamp.now().year)]

    fig = px.line(
        ydf,
        x="_year",
        y="Companies",
        title="Companies by Founding Year"
    )

    fig.update_traces(line=dict(width=3))
    fig.update_layout(template="simple_white")
    fig.update_xaxes(tickmode="linear", dtick=1)

    st.plotly_chart(fig, use_container_width=True)
    st.caption("⬇️ Use the camera icon to download")
else:
    st.warning("⚠️ Founding Year column not found")

st.divider()

# -------------------------------------------------
# BAR — FUNDING STAGE
# -------------------------------------------------

if COL_FUNDING_LEVEL:

    def normalize_stage(v):
        if pd.isna(v):
            return "Unfunded"
        v = str(v).lower()
        if "boot" in v or "self" in v:
            return "Bootstrapped"
        if "pre" in v and "seed" in v:
            return "Pre-Seed"
        if "seed" in v:
            return "Seed"
        if "series a" in v:
            return "Series A"
        if "series b" in v:
            return "Series B"
        if "angel" in v:
            return "Angel"
        return "Others"

    sdf = df.copy()
    sdf["_stage"] = sdf[COL_FUNDING_LEVEL].apply(normalize_stage)
    counts = sdf["_stage"].value_counts()

    top = counts.head(6)
    others = counts.iloc[6:].sum()

    final = top.copy()
    if others > 0:
        final["Others"] += others if "Others" in final else others

    plot_df = final.reset_index()
    plot_df.columns = ["Funding Stage", "Count"]

    fig = px.bar(
        plot_df,
        x="Funding Stage",
        y="Count",
        title="Startup Distribution by Funding Stage"
    )

    st.plotly_chart(fig, use_container_width=True)
    st.caption("⬇️ Use the camera icon to download")
else:
    st.warning("⚠️ Funding Stage column not found")

st.divider()

# -------------------------------------------------
# BAR — FOUNDER GENDER
# -------------------------------------------------

if COL_FOUNDER_TYPE:

    def normalize_gender(v):
        if pd.isna(v):
            return "Unknown"
        v = str(v).lower()
        if "mix" in v or "both" in v or "diverse" in v:
            return "Mixed"
        if "female" in v:
            return "Female"
        if "male" in v:
            return "Male"
        return "Unknown"

    gdf = df.copy()
    gdf["_gender"] = gdf[COL_FOUNDER_TYPE].apply(normalize_gender)

    gcounts = gdf["_gender"].value_counts().reset_index()
    gcounts.columns = ["Founder Gender", "Count"]

    fig = px.bar(
        gcounts,
        x="Founder Gender",
        y="Count",
        title="Startup Distribution by Founder Gender"
    )

    st.plotly_chart(fig, use_container_width=True)
    st.caption("⬇️ Use the camera icon to download")
else:
    st.warning("⚠️ Founder Type column not found")

st.divider()

# -------------------------------------------------
# INDIA MAP — CITY
# -------------------------------------------------

if COL_CITY:

    def normalize_city(c):
        if pd.isna(c):
            return None
        c = str(c).lower()
        mapping = {
            "bangalore": "Bengaluru", "bengaluru": "Bengaluru",
            "delhi": "Delhi", "new delhi": "Delhi", "delhi ncr": "Delhi",
            "mumbai": "Mumbai", "bombay": "Mumbai",
            "chennai": "Chennai", "madras": "Chennai",
            "kolkata": "Kolkata", "calcutta": "Kolkata",
            "pune": "Pune", "poona": "Pune",
            "gurgaon": "Gurugram", "gurugram": "Gurugram"
        }
        for k in mapping:
            if k in c:
                return mapping[k]
        return c.title()

    cdf = df.copy()
    cdf["_city"] = cdf[COL_CITY].apply(normalize_city)

    city_counts = cdf["_city"].value_counts().reset_index()
    city_counts.columns = ["City", "Count"]

    city_latlon = {
        "Delhi": (28.61, 77.20),
        "Mumbai": (19.07, 72.87),
        "Bengaluru": (12.97, 77.59),
        "Chennai": (13.08, 80.27),
        "Hyderabad": (17.38, 78.48),
        "Pune": (18.52, 73.85),
        "Kolkata": (22.57, 88.36),
        "Gurugram": (28.45, 77.02),
    }

    city_counts["lat"] = city_counts["City"].map(lambda x: city_latlon.get(x, (None, None))[0])
    city_counts["lon"] = city_counts["City"].map(lambda x: city_latlon.get(x, (None, None))[1])
    city_map = city_counts.dropna()

    fig = px.scatter_geo(
        city_map,
        lat="lat",
        lon="lon",
        size="Count",
        hover_name="City",
        scope="asia",
        title="Startup Distribution Across India"
    )

    fig.update_geos(
        center=dict(lat=22.97, lon=78.65),
        projection_scale=4.5,
        showcountries=True,
        showland=True
    )

    st.plotly_chart(fig, use_container_width=True)
    st.caption("⬇️ Use the camera icon to download")
else:
    st.warning("⚠️ City column not found")
