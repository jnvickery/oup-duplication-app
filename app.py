import pandas as pd
import plotly.express as px
import streamlit as st

processed_data = "oup_upso_processed.csv"

st.set_page_config(page_title="OUP-UPSO duplication in TRLN", layout="wide")


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
            "print_ncsu": int,
            "print_duke": int,
            "print_nccu": int,
            "print_unc": int,
            "online_ncsu": int,
            "online_duke": int,
            "online_nccu": int,
            "online_unc": int,
            "TRLN_dup_pct": float,
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
    # df.filter(like="print_", axis=1)
    return df


all_df = load_data()

st.header("OUP-UPSO duplication in TRLN")

row0_0, row0_1, row0_2 = st.columns([1, 3, 1])

with row0_1:
    # slider to select upload year parameters
    min_year = min(all_df["upload_year"])
    max_year = max(all_df["upload_year"])

    year = st.slider(
        "**What upload years to include**",
        min_value=min_year,
        max_value=max_year,
        value=(2015, max_year),
    )

    # filter data to include selected upload years
    df = all_df.loc[all_df["upload_year"].between(year[0], year[1], inclusive="both")]

    # select box for school
    school_list = ["TRLN", "duke", "nccu", "ncsu", "unc"]

    def upper_school(school):
        return school.upper()

    school = st.selectbox(
        label="**Select a school or all TRLN**",
        options=school_list,
        index=0,
        format_func=upper_school,
    )

try:
    # first row of barcharts
    row1_1, row1_2 = st.columns(2)

    # barchart of upload year by dup flag for school
    with row1_1:
        year_by_dup = pd.crosstab(df["upload_year"], df[f"{school}_dup_flag"])
        year_by_dup.rename(columns={0: "No", 1: "Yes"}, inplace=True)
        year_by_dup.reset_index(inplace=True)
        fig = px.bar(
            year_by_dup,
            x="upload_year",
            y=["No", "Yes"],
            title=f"Duplicates by year for {school.upper()}",
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
            title="TRLN duplicate percentage by year",
            color="TRLN_dup_pct",
        )
        st.plotly_chart(fig1, theme="streamlit", use_container_width=True)

    # second row of charts
    row2_1, row2_2 = st.columns(2)

    with row2_1:
        # Top 10 modules with most dups
        top_dup_modules = (
            df.groupby("module")[f"{school}_dup_flag"]
            .sum()
            .to_frame("Number of duplicates")
            .sort_values(by="Number of duplicates", ascending=False)
            .reset_index()
        )
        fig3 = px.bar(
            top_dup_modules.head(10),
            x="Number of duplicates",
            y="module",
            orientation="h",
            title=f"Top 10 modules with the most duplication for {school.upper()}",
        )
        fig3.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig3, theme="streamlit", use_container_width=True)

    with row2_2:
        # Top 10 press with most dups
        top_dup_press = (
            df.groupby("press")[f"{school}_dup_flag"]
            .sum()
            .to_frame("Number of duplicates")
            .sort_values(by="Number of duplicates", ascending=False)
            .reset_index()
        )
        fig4 = px.bar(
            top_dup_press.head(10),
            x="Number of duplicates",
            y="press",
            orientation="h",
            title=f"Top 10 presses with the most duplication for {school.upper()}",
        )
        fig4.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig4, theme="streamlit", use_container_width=True)

    # third row of barcharts
    row3_1, row3_2 = st.columns(2)
    with row3_1:
        if school == "TRLN":
            dups = df.loc[df["TRLN_dup_flag"] == 1].copy()
            cols2keep = [
                "upload_year",
                "print_duke",
                "print_nccu",
                "print_ncsu",
                "print_unc",
                "online_duke",
                "online_nccu",
                "online_ncsu",
                "online_unc",
            ]
            dups = dups[cols2keep]
            dups["print_total"] = dups.filter(regex="print_").sum(axis=1)
            dups["ebook_total"] = dups.filter(regex="online_").sum(axis=1)
            dups.loc[
                (dups["print_total"] > 0) & (dups["ebook_total"] > 1), "dup_format"
            ] = "Print + Ebook"
            dups.loc[
                (dups["print_total"] >= 1) & (dups["ebook_total"] <= 4), "dup_format"
            ] = "Print"
            dups.loc[
                (dups["print_total"] == 0) & (dups["ebook_total"] >= 4), "dup_format"
            ] = "Ebook"
        else:
            dups = (
                df[["upload_year", f"print_{school}", f"online_{school}"]]
                .loc[df[f"{school}_dup_flag"] == 1]
                .copy()
            )
            dups.loc[
                (dups[f"online_{school}"] > 1) & (dups[f"print_{school}"] > 0),
                "dup_format",
            ] = "Print + Ebook"
            dups.loc[
                (dups[f"online_{school}"] == 1) & (dups[f"print_{school}"] > 0),
                "dup_format",
            ] = "Print"
            dups.loc[
                (dups[f"online_{school}"] > 1) & (dups[f"print_{school}"] == 0),
                "dup_format",
            ] = "Ebook"

        dups_bar = (
            dups.groupby(["upload_year", "dup_format"]).size().to_frame().reset_index()
        )
        dups_bar.rename(columns={0: "Count"}, inplace=True)
        fig5 = px.bar(
            dups_bar,
            x="upload_year",
            y="Count",
            color="dup_format",
            title=f"Duplicates by format and year for {school.upper()}",
            barmode="group",
        )
        st.plotly_chart(fig5, theme="streamlit", use_container_width=True)

    with row3_2:
        if school == "TRLN":
            no_copies = df[cols2keep]
            no_copies["print_total"] = no_copies.filter(regex="print_").sum(axis=1)
            no_copies["ebook_total"] = no_copies.filter(regex="online_").sum(axis=1)
            no_copies = no_copies.loc[
                (no_copies["print_total"] == 0) & (no_copies["ebook_total"] == 0)
            ]
        else:
            no_copies = df.loc[
                (df[f"print_{school}"] == 0) & (df[f"online_{school}"] == 0)
            ].copy()
        no_copies = no_copies["upload_year"].value_counts().to_frame().reset_index()
        no_copies.columns = ["upload_year", "num_missing"]
        fig6 = px.bar(
            no_copies,
            x="upload_year",
            y="num_missing",
            title=f"Number of titles missing per upload year for {school.upper()}",
        )
        st.plotly_chart(fig6, theme="streamlit", use_container_width=True)
except ValueError:
    st.subheader(
        (
            f"{school.upper()} does not have enough "
            f"data for {year[0]} to {year[1]} to show graphs. "
            "Select a wider year range."
        )
    )

# Data table and download option
st.subheader(
    "Dataset with duplicate flags and percent duplication per title across schools."
)


@st.experimental_memo
def convert_df(df):
    return df.to_csv(index=False).encode("utf-8")


csv = convert_df(all_df)
st.download_button(
    "Download all data as csv",
    csv,
    "TRLN_OUP_duplication.csv",
    "text/csv",
    key="download-csv",
)

# format dataframe for display
# map "Yes" to 1 and "No" to 0 for dup flag columns
dup_flag_cols = df.filter(regex="_dup_flag")
dup_flag_cols = dup_flag_cols.applymap(lambda x: "Yes" if x == 1 else "No")
df[dup_flag_cols.columns] = dup_flag_cols

# add percent sign to TRLN_dup_pct
df["TRLN_dup_pct"] = (df["TRLN_dup_pct"] * 100).map("{:,.0f}%".format)

# rename columns for clarity
display_df = df.rename(
    columns={
        "title": "Title",
        "module": "OUP Module",
        "print_pubdate": "Print pub. year",
        "isbn": "ISBN",
        "eisbn": "EISBN",
        "press": "Press",
        "online_ncsu": "Online records NCSU",
        "print_ncsu": "Print records NCSU",
        "online_duke": "Online records Duke",
        "print_duke": "Print records Duke",
        "online_unc": "Online records UNC",
        "print_unc": "Print records UNC",
        "online_nccu": "Online records NCCU",
        "print_nccu": "Print records NCCU",
        "duke_dup_flag": "Dups at Duke",
        "ncsu_dup_flag": "Dups at NCSU",
        "unc_dup_flag": "Dups at UNC",
        "nccu_dup_flag": "Dups at NCCU",
        "TRLN_dup_pct": "Pct of TRLN with dups",
        "TRLN_dup_flag": "Dups in TRLN",
        "upload_year": "OUP upload year",
    }
)

st.dataframe(display_df)
