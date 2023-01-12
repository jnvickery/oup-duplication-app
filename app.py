import pandas as pd
import plotly.express as px
import streamlit as st

processed_data = "oup_upso_processed.csv"

st.set_page_config(layout="wide", page_title="OUP-UPSO duplication in TRLN")


@st.experimental_singleton
def load_data():
    df = pd.read_csv(
        processed_data,
        index_col="doi",
        dtype={
            "oa": str,
            "discontinued": str,
            "print_pubdate": int,
            "isbn": str,
            "eisbn": str,
        },
    )
    df["upload_year"] = pd.to_datetime(df["upload_date"]).dt.year
    drop_cols = [
        "oa",
        "discontinued",
        "upload_date",
        "authors",
        "sub_discipline",
        "link",
    ]
    df.drop(columns=drop_cols, inplace=True)
    return df


df = load_data()

st.header("OUP-UPSO duplication in TRLN")

# slider to select upload year parameters
min_year = min(df["upload_year"])
max_year = max(df["upload_year"])

year = st.slider(
    "**What upload years to include**",
    min_value=min_year,
    max_value=max_year,
    value=(2015, max_year),
)

# year = st.select_slider(
#     "**What upload years to include**",
#     options=list(df["upload_year"].unique()),
#     value=(2015, max_year),
# )

# filter data to include selected upload years
df = df.loc[df["upload_year"].between(year[0], year[1], inclusive="both")]

# first row of barcharts
row1_1, row1_2 = st.columns(2)

# barchart of upload year by TRLN dup flag
with row1_1:
    year_by_dup = pd.crosstab(df["upload_year"], df["TRLN_dup_flag"])
    year_by_dup.rename(columns={0: "No", 1: "Yes"}, inplace=True)
    year_by_dup.reset_index(inplace=True)
    fig = px.bar(
        year_by_dup,
        x="upload_year",
        y=["No", "Yes"],
        title="Dups by Year",
        barmode="group",
    )
    st.plotly_chart(fig, theme="streamlit", use_container_width=True)

# barchart of upload year by TRLN dup pct
with row1_2:
    year_by_dup_pct = pd.DataFrame(
        df[["upload_year", "TRLN_dup_pct"]].value_counts().reset_index()
    )
    year_by_dup_pct.rename(columns={0: "Count"}, inplace=True)
    year_by_dup_pct.sort_values(by=["upload_year", "TRLN_dup_pct"])
    year_by_dup_pct["TRLN_dup_pct"] = year_by_dup_pct["TRLN_dup_pct"].astype(str)
    fig1 = px.bar(
        year_by_dup_pct,
        x="upload_year",
        y="Count",
        title="Dup pct by Year",
        color="TRLN_dup_pct",
    )
    st.plotly_chart(fig1, theme="streamlit", use_container_width=True)

# Top 10 modules with most dups
top_dup_modules = (
    df.groupby("module")["TRLN_dup_flag"]
    .sum()
    .to_frame("Number of dups")
    .sort_values(by="Number of dups", ascending=False)
    .reset_index()
)
fig3 = px.bar(
    top_dup_modules.head(10),
    x="Number of dups",
    y="module",
    orientation="h",
    title="Top 10 modules with the most duplication",
)
fig3.update_layout(yaxis=dict(autorange="reversed"))
st.plotly_chart(fig3, theme="streamlit", use_container_width=True)

# Top 10 press with most dups
top_dup_press = (
    df.groupby("press")["TRLN_dup_flag"]
    .sum()
    .to_frame("Number of dups")
    .sort_values(by="Number of dups", ascending=False)
    .reset_index()
)
fig4 = px.bar(
    top_dup_press.head(10),
    x="Number of dups",
    y="press",
    orientation="h",
    title="Top 10 presses with the most duplication",
)
fig4.update_layout(yaxis=dict(autorange="reversed"))
st.plotly_chart(fig4, theme="streamlit", use_container_width=True)

# Data table and download option
st.subheader(
    "Dataset with duplicate flags and perent duplication per title across schools."
)


@st.experimental_memo
def convert_df(df):
    return df.to_csv(index=False).encode("utf-8")


csv = convert_df(df)
st.download_button(
    "Download data as csv",
    csv,
    "TRLN_OUP_duplication.csv",
    "text/csv",
    key="download-csv",
)
st.dataframe(df)
