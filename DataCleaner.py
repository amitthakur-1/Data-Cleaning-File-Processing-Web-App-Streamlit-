import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io

st.set_page_config(page_title="Smart Data Cleaner", layout="wide")
st.title("Smart data cleaner")
st.caption("Upload a CSV, XLSX, or JSON file to clean, analyze, and export.")

# ── Upload ────────────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader("Upload file", type=["csv", "xlsx", "json"])

if not uploaded_file:
    st.info("Upload a file above to get started.")
    st.stop()

# ── Read ──────────────────────────────────────────────────────────────────────
ext = uploaded_file.name.rsplit(".", 1)[-1].lower()
try:
    if ext == "csv":
        df = pd.read_csv(uploaded_file)
    elif ext == "xlsx":
        df = pd.read_excel(uploaded_file)
    elif ext == "json":
        df = pd.read_json(uploaded_file)
    else:
        st.error("Unsupported file type.")
        st.stop()
except Exception as e:
    st.error(f"Could not read file: {e}")
    st.stop()

# ── Overview metrics ──────────────────────────────────────────────────────────
st.subheader("File overview")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Rows", f"{len(df):,}")
c2.metric("Columns", len(df.columns))
c3.metric("Missing cells", int(df.isnull().sum().sum()))
c4.metric("Duplicate rows", int(df.duplicated().sum()))

with st.expander("Raw data preview", expanded=False):
    st.dataframe(df, use_container_width=True)

# ── Column type summary ───────────────────────────────────────────────────────
st.subheader("Column types detected")
num_cols  = df.select_dtypes(include=["number"]).columns.tolist()
text_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
dt_cols   = df.select_dtypes(include=["datetime"]).columns.tolist()

col_info = (
    [f"🔢 {c}" for c in num_cols]
    + [f"🔤 {c}" for c in text_cols]
    + [f"📅 {c}" for c in dt_cols]
)
st.write("  ·  ".join(col_info) if col_info else "No columns detected.")

# ── Cleaning options ──────────────────────────────────────────────────────────
st.subheader("Cleaning options")

with st.form("cleaning_form"):
    opt_strip    = st.checkbox("Strip whitespace from text columns", value=True)
    opt_dedup    = st.checkbox("Remove duplicate rows", value=True)
    opt_unknown  = st.checkbox('Replace "unknown" / "n/a" / "none" with NaN', value=True)
    opt_coerce   = st.checkbox("Force-convert columns to numeric where possible", value=True)
    opt_case     = st.selectbox(
        "Text case for string columns",
        ["lowercase", "Title Case", "UPPERCASE", "No change"],
    )
    opt_missing  = st.selectbox(
        "Handle missing values",
        [
            'Fill with "Unknown" (text) / 0 (numeric)',
            "Fill numeric with mean, text with mode",
            "Fill numeric with median, text with mode",
            "Drop rows with any null",
            "Leave as-is",
        ],
    )

    run = st.form_submit_button("Run cleaning", type="primary")

# ── Apply cleaning ────────────────────────────────────────────────────────────
if run:
    cleaned = df.copy()

    # Duplicate removal
    if opt_dedup:
        cleaned = cleaned.drop_duplicates()

    # Replace placeholder strings with NaN
    if opt_unknown:
        placeholders = {"unknown", "n/a", "na", "none", "null", "-", ""}
        cleaned.replace(
            {v: pd.NA for v in placeholders} | {v.upper(): pd.NA for v in placeholders},
            inplace=True,
        )

    # Strip whitespace
    if opt_strip:
        for col in cleaned.select_dtypes(include="object").columns:
            cleaned[col] = cleaned[col].astype(str).str.strip()
            cleaned[col] = cleaned[col].replace("nan", pd.NA)

    # Text case
    if opt_case != "No change":
        for col in cleaned.select_dtypes(include="object").columns:
            if opt_case == "lowercase":
                cleaned[col] = cleaned[col].str.lower()
            elif opt_case == "Title Case":
                cleaned[col] = cleaned[col].str.title()
            elif opt_case == "UPPERCASE":
                cleaned[col] = cleaned[col].str.upper()

    # Coerce numerics
    if opt_coerce:
        for col in cleaned.columns:
            if cleaned[col].dtype == object:
                trial = pd.to_numeric(cleaned[col], errors="coerce")
                if trial.notna().sum() > cleaned[col].notna().sum() * 0.5:
                    cleaned[col] = trial

    # Handle missing values
    if "Drop rows" in opt_missing:
        cleaned = cleaned.dropna()
    elif "Leave" not in opt_missing:
        for col in cleaned.columns:
            if cleaned[col].dtype in ["float64", "float32", "int64", "int32"]:
                if "mean" in opt_missing:
                    cleaned[col] = cleaned[col].fillna(cleaned[col].mean())
                elif "median" in opt_missing:
                    cleaned[col] = cleaned[col].fillna(cleaned[col].median())
                else:
                    cleaned[col] = cleaned[col].fillna(0)
            else:
                if "mode" in opt_missing and not cleaned[col].mode().empty:
                    cleaned[col] = cleaned[col].fillna(cleaned[col].mode()[0])
                else:
                    cleaned[col] = cleaned[col].fillna("Unknown")

    st.success(
        f"Cleaning complete — {len(cleaned):,} rows remaining "
        f"({len(df) - len(cleaned):,} removed). "
        f"{int(cleaned.isnull().sum().sum())} missing cells remain."
    )

    # ── Results tabs ──────────────────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs(["Cleaned data", "Summary stats", "Visualize"])

    with tab1:
        st.dataframe(cleaned, use_container_width=True)

    with tab2:
        st.write("**Descriptive statistics**")
        st.dataframe(cleaned.describe(include="all"), use_container_width=True)
        st.write("**Missing values per column**")
        mv = cleaned.isnull().sum().rename("missing").to_frame()
        mv["pct"] = (mv["missing"] / len(cleaned) * 100).round(1)
        st.dataframe(mv[mv["missing"] > 0], use_container_width=True)

    with tab3:
        num_cleaned = cleaned.select_dtypes(include="number").columns.tolist()
        if num_cleaned:
            col_pick = st.selectbox("Column to visualize", num_cleaned)
            chart_type = st.radio("Chart type", ["Histogram", "Box plot"], horizontal=True)

            fig, ax = plt.subplots(figsize=(8, 3.5))
            if chart_type == "Histogram":
                ax.hist(cleaned[col_pick].dropna(), bins=30, color="#7F77DD", edgecolor="white")
                ax.set_title(f"Distribution of {col_pick}")
            else:
                ax.boxplot(cleaned[col_pick].dropna(), vert=False, patch_artist=True,
                           boxprops=dict(facecolor="#AFA9EC", color="#534AB7"))
                ax.set_title(f"Box plot — {col_pick}")
            ax.set_xlabel(col_pick)
            st.pyplot(fig)
        else:
            st.info("No numeric columns available for visualization.")

    # ── Download ──────────────────────────────────────────────────────────────
    st.subheader("Download")
    csv_bytes = cleaned.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download cleaned CSV",
        data=csv_bytes,
        file_name="cleaned_data.csv",
        mime="text/csv",
    )

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        cleaned.to_excel(writer, index=False, sheet_name="Cleaned")
    st.download_button(
        label="Download cleaned XLSX",
        data=buf.getvalue(),
        file_name="cleaned_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
