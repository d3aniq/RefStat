import streamlit as st
import pandas as pd
from datetime import datetime

# Function to load data from a local file path
def load_data_from_path(file_path):
    return pd.read_csv(file_path)

# Function to filter data by date range
def filter_data_by_date(df, start_date, end_date):
    # Convert "Date" to datetime for filtering
    filtered_df = df.copy()
    filtered_df["DateTemp"] = pd.to_datetime(filtered_df["Date"])  # Temporary column for filtering
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    # Filter rows between the given dates
    filtered_df = filtered_df[(filtered_df["DateTemp"] >= start_date) & (filtered_df["DateTemp"] <= end_date)]
    filtered_df.drop(columns=["DateTemp"], inplace=True)  # Drop temporary column

    # Group by referee and sum matches
    grouped = filtered_df.groupby("Domare")["Matcher"].sum().reset_index()

    # Sort by matches descending
    grouped = grouped.sort_values(by="Matcher", ascending=False).reset_index(drop=True)

    return grouped

# Streamlit App
st.title("RefStat")

# Initialize session state for data
if "data" not in st.session_state:
    st.session_state["data"] = None

# File path for the CSV file
file_path = "referee_match_data_230811_241212.csv"

# Auto-load data if not already loaded
if st.session_state["data"] is None:
    try:
        data = load_data_from_path(file_path)
        st.session_state["data"] = data
    except Exception as e:
        st.error(f"Failed to auto-load data: {e}")

# Display loaded data if available
if st.session_state["data"] is not None:
    # Find the min and max dates in the dataset
    min_date = pd.to_datetime(st.session_state["data"]["Date"]).min()
    max_date = pd.to_datetime(st.session_state["data"]["Date"]).max()

    # Display dropdowns and date inputs
    sport = st.selectbox("Idrott", ["Innebandy"], index=0)
    district = st.selectbox("Förbund", ["Västsvenska"], index=0)

    # Restrict date selection to the dataset's range
    start_date = st.date_input("Från", value=min_date, min_value=min_date, max_value=max_date)
    end_date = st.date_input("Till", value=max_date, min_value=min_date, max_value=max_date)

    if st.button("Visa Statistik"):
        if start_date > end_date:
            st.error("Start date must be before or equal to end date.")
        else:
            # Filter and process the data
            result = filter_data_by_date(st.session_state["data"], start_date, end_date)

            result.index = result.index + 1

            # Display the results
            st.write("### Domarstatistik")
            st.dataframe(result)

            # Option to download the result as CSV
            csv = result.to_csv(index=False)
            # st.download_button(
            #     label="Ladda ner som CSV",
            #     data=csv,
            #     file_name="filtered_referee_statistics.csv",
            #     mime="text/csv",
            # )
else:
    st.info("Please check the file path and reload the app.")
