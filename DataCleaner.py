# import streamlit as st
# import pandas as pd

# st.title("Data Cleaning and Representation")
# uploaded_file = st.file_uploader("Upload file",type=["csv", "xlsx", "json"])

# if uploaded_file:
#     file_type = uploaded_file.name.split(".")[-1]

#     if file_type == "csv":
#         df = pd.read_csv(uploaded_file)

#     elif file_type == "xlsx":
#         df = pd.read_excel(uploaded_file)

#     elif file_type == "json":
#         df = pd.read_json(uploaded_file)

#     else:
#         st.error("Unsupported file type")

#     # Clean text columns
#     df["Name"] = df["Name"].str.strip().str.lower()
#     df["City"] = df["City"].str.strip().str.lower()

#     # Replace 'unknown' with NaN
#     df.replace("unknown", pd.NA, inplace=True)

#     # Convert numeric columns
#     df["Age"] = pd.to_numeric(df["Age"], errors="coerce")
#     df["Salary"] = pd.to_numeric(df["Salary"], errors="coerce")

#     # Remove duplicates
#     df = df.drop_duplicates()

#     # Fill missing values
#     df = df.fillna("Unknown")

#     # Show cleaned data
#     st.subheader("Cleaned Data")
#     st.dataframe(df)



# 2
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("Smart Data Cleaner & Analyzer")

# Upload file
uploaded_file = st.file_uploader("Upload file", type=["csv", "xlsx", "json"])

if uploaded_file:
    # Detect file type
    file_type = uploaded_file.name.split(".")[-1]

    # Read file
    if file_type == "csv":
        df = pd.read_csv(uploaded_file)
    elif file_type == "xlsx":
        df = pd.read_excel(uploaded_file)
    elif file_type == "json":
        df = pd.read_json(uploaded_file)
    else:
        st.error("Unsupported file type")
        st.stop()

    st.subheader("Original Data")
    st.dataframe(df)

    # -----------------------------
    # 🧹 CLEANING SECTION
    # -----------------------------

    st.subheader("🧹 Data Cleaning Options")

    # Remove duplicates
    if st.checkbox("Remove duplicate rows"):
        df = df.drop_duplicates()

    # Handle missing values
    missing_option = st.selectbox(
        "Handle missing values",
        ["Do nothing", "Fill with mean", "Fill with median", "Fill with mode", "Drop rows"]
    )

    if missing_option != "Do nothing":
        for col in df.columns:
            if df[col].dtype in ["float64", "int64"]:
                if missing_option == "Fill with mean":
                    df[col].fillna(df[col].mean(), inplace=True)
                elif missing_option == "Fill with median":
                    df[col].fillna(df[col].median(), inplace=True)
                elif missing_option == "Fill with mode":
                    df[col].fillna(df[col].mode()[0], inplace=True)
            else:
                df[col].fillna("Unknown", inplace=True)

        if missing_option == "Drop rows":
            df = df.dropna()

    
 # ANALYSIS SECTION
    

    st.subheader("📊 Data Summary")
    st.write(df.describe())

    st.subheader("❗ Missing Values")
    st.write(df.isnull().sum())

    
    # VISUALIZATION
    st.subheader("📈 Visualization")

    numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns.tolist()

    if numeric_cols:
        selected_col = st.selectbox("Select column to plot", numeric_cols)

        fig, ax = plt.subplots()
        ax.hist(df[selected_col].dropna())
        ax.set_title(f"Distribution of {selected_col}")

        st.pyplot(fig)

    # -----------------------------
    # 📥 DOWNLOAD
    # -----------------------------

    st.subheader("📥 Download Cleaned Data")

    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download CSV",
        csv,
        "cleaned_data.csv",
        "text/csv"
    )

    st.subheader("✅ Cleaned Data")
    st.dataframe(df)