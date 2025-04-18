import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime, timedelta
import io

# Set page configuration
st.set_page_config(
    page_title="RefStat - Domarstatistik",
    page_icon="🏆",
    layout="wide"
)

# Apply custom CSS for better styling
st.markdown("""
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3 {
        color: #1E3A8A;
    }
    .stButton>button {
        background-color: #1E3A8A;
        color: white;
        border-radius: 5px;
    }
    .stButton>button:hover {
        background-color: #2563EB;
    }
    </style>
    """, unsafe_allow_html=True)

# Function to load data from a local file path with error handling
@st.cache_data
def load_data_from_path(file_path):
    """Load and preprocess the CSV data file."""
    try:
        if not os.path.exists(file_path):
            st.error(f"File not found: {file_path}")
            return None
        
        df = pd.read_csv(file_path)
        
        # Data validation
        required_columns = ["Date", "Domare", "Matcher"]
        if not all(col in df.columns for col in required_columns):
            missing = [col for col in required_columns if col not in df.columns]
            st.error(f"Missing required columns: {', '.join(missing)}")
            return None
        
        # Convert Date to datetime once
        df["DateObj"] = pd.to_datetime(df["Date"], errors='coerce')
        
        # Check for invalid dates
        invalid_dates = df[df["DateObj"].isna()]
        if not invalid_dates.empty:
            st.warning(f"Found {len(invalid_dates)} rows with invalid dates. These will be excluded.")
            df = df.dropna(subset=["DateObj"])
            
        return df
    
    except pd.errors.ParserError:
        st.error("Failed to parse the CSV file. Please check the file format.")
        return None
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# Function to filter data by date range
def filter_data(df, start_date, end_date, selected_districts=None, selected_series=None):
    """Filter data based on date range and other criteria."""
    if df is None:
        return None
    
    filtered_df = df.copy()
    
    # Convert input dates to pandas datetime
    start_date_pd = pd.to_datetime(start_date)
    end_date_pd = pd.to_datetime(end_date)
    
    # Filter by date range
    filtered_df = filtered_df[(filtered_df["DateObj"] >= start_date_pd) & 
                             (filtered_df["DateObj"] <= end_date_pd)]
    
    # Filter by district if available and selected
    if "Förbund" in filtered_df.columns and selected_districts:
        if not isinstance(selected_districts, list):
            selected_districts = [selected_districts]
        filtered_df = filtered_df[filtered_df["Förbund"].isin(selected_districts)]
    
    # Filter by series if available and selected
    if "Serie" in filtered_df.columns and selected_series:
        if not isinstance(selected_series, list):
            selected_series = [selected_series]
        filtered_df = filtered_df[filtered_df["Serie"].isin(selected_series)]
    
    return filtered_df

# Function to generate referee statistics
def generate_referee_stats(filtered_df):
    """Generate statistics grouped by referee."""
    if filtered_df is None or filtered_df.empty:
        return None
    
    # Group by referee and sum matches
    grouped = filtered_df.groupby("Domare")["Matcher"].sum().reset_index()
    
    # Sort by matches descending
    grouped = grouped.sort_values(by="Matcher", ascending=False).reset_index(drop=True)
    
    # Add rank column
    grouped.index = grouped.index + 1
    grouped = grouped.rename_axis('Rank').reset_index()
    
    return grouped

# Function to create charts
def create_charts(stats_df, filtered_df):
    """Create visualizations for the data."""
    if stats_df is None or stats_df.empty:
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Top referees bar chart
        top_n = min(15, len(stats_df))
        fig1 = px.bar(
            stats_df.head(top_n),
            x="Domare",
            y="Matcher",
            title=f"Top {top_n} Referees by Number of Matches",
            labels={"Matcher": "Number of Matches", "Domare": "Referee"},
            color="Matcher",
            color_continuous_scale="Blues"
        )
        fig1.update_layout(xaxis={'categoryorder':'total descending'})
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Pie chart showing distribution
        fig2 = px.pie(
            stats_df.head(10),
            values="Matcher",
            names="Domare",
            title="Distribution of Matches Among Top 10 Referees",
            hole=0.4
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    # Time series analysis if we have at least 5 dates in the filtered data
    if "DateObj" in filtered_df.columns:
        date_counts = filtered_df.groupby(filtered_df["DateObj"].dt.date)["Matcher"].sum().reset_index()
        if len(date_counts) >= 5:
            fig3 = px.line(
                date_counts,
                x="DateObj",
                y="Matcher",
                title="Number of Matches Over Time",
                labels={"DateObj": "Date", "Matcher": "Total Matches"}
            )
            st.plotly_chart(fig3, use_container_width=True)

# Function to export data
def get_downloadable_data(stats_df, format_type="csv"):
    """Prepare data for download in various formats."""
    if stats_df is None or stats_df.empty:
        return None, None
    
    if format_type == "csv":
        buffer = io.StringIO()
        stats_df.to_csv(buffer, index=False)
        return buffer.getvalue(), "text/csv"
    elif format_type == "excel":
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            stats_df.to_excel(writer, sheet_name="RefStats", index=False)
        return buffer.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        return None, None

# Main Streamlit App
def main():
    st.title("🏆 RefStat - Domarstatistik")
    st.markdown("Analysera och visualisera domarstatistik för matcher")
    
    # Initialize session state for data
    if "data" not in st.session_state:
        st.session_state["data"] = None
    
    # File path for the CSV file
    file_path = "vsibf.csv"
    
    # Add file uploader option
    uploaded_file = st.file_uploader("Ladda upp egen CSV-fil (frivilligt)", type=["csv"])
    
    # Load data from uploaded file or default path
    if uploaded_file is not None:
        try:
            data = pd.read_csv(uploaded_file)
            if "Date" in data.columns and "Domare" in data.columns and "Matcher" in data.columns:
                st.session_state["data"] = data
                st.success("Data har laddats upp framgångsrikt!")
            else:
                st.error("Filen saknar nödvändiga kolumner (Date, Domare, Matcher).")
        except Exception as e:
            st.error(f"Fel vid uppladdning av fil: {e}")
    # Auto-load data if not already loaded
    elif st.session_state["data"] is None:
        data = load_data_from_path(file_path)
        if data is not None:
            st.session_state["data"] = data
            st.info(f"Standarddata laddad från {file_path}")
        else:
            st.error(f"Kunde inte ladda standarddata. Vänligen ladda upp en CSV-fil.")
    
    # Display filter options if data is available
    if st.session_state["data"] is not None:
        with st.expander("Filteralternativ", expanded=True):
            col1, col2 = st.columns(2)
            
            # Find the min and max dates in the dataset
            df = st.session_state["data"]
            min_date = df["DateObj"].min().date()
            max_date = df["DateObj"].max().date()
            
            # Display dropdowns and date inputs
            with col1:
                # Sport dropdown (could be dynamic if data contains multiple sports)
                available_sports = ["Innebandy"]
                if "Idrott" in df.columns:
                    available_sports = sorted(df["Idrott"].unique().tolist())
                sport = st.selectbox("Idrott", available_sports, index=0)
                
                # District dropdown (could be dynamic)
                available_districts = ["Västsvenska"]
                if "Förbund" in df.columns:
                    available_districts = sorted(df["Förbund"].unique().tolist())
                district = st.selectbox("Förbund", available_districts, index=0)
                
                # Add series filter if available
                series_filter = None
                if "Serie" in df.columns:
                    available_series = sorted(df["Serie"].unique().tolist())
                    series_filter = st.multiselect("Serie", available_series)
            
            with col2:
                # Date range selection
                start_date = st.date_input("Från", value=min_date, min_value=min_date, max_value=max_date)
                end_date = st.date_input("Till", value=max_date, min_value=min_date, max_value=max_date)
                
                # Quick date presets
                st.write("Snabbval för datumintervall:")
                date_col1, date_col2, date_col3 = st.columns(3)
                
                with date_col1:
                    if st.button("Senaste månaden"):
                        end_date = max_date
                        start_date = max_date - timedelta(days=30)
                        st.session_state["start_date"] = start_date
                        st.session_state["end_date"] = end_date
                        st.experimental_rerun()
                
                with date_col2:
                    if st.button("Senaste 3 månaderna"):
                        end_date = max_date
                        start_date = max_date - timedelta(days=90)
                        st.session_state["start_date"] = start_date
                        st.session_state["end_date"] = end_date
                        st.experimental_rerun()
                
                with date_col3:
                    if st.button("Allt"):
                        start_date = min_date
                        end_date = max_date
                        st.session_state["start_date"] = start_date
                        st.session_state["end_date"] = end_date
                        st.experimental_rerun()
        
        # Apply filters and display results
        if st.button("Visa Statistik", use_container_width=True):
            if start_date > end_date:
                st.error("Startdatum måste vara före eller samma som slutdatum.")
            else:
                with st.spinner("Bearbetar data..."):
                    # Filter and process the data
                    filtered_data = filter_data(
                        st.session_state["data"], 
                        start_date, 
                        end_date,
                        district,
                        series_filter
                    )
                    
                    if filtered_data is not None and not filtered_data.empty:
                        result = generate_referee_stats(filtered_data)
                        
                        if result is not None and not result.empty:
                            # Display the results
                            st.write(f"### Domarstatistik ({start_date} till {end_date})")
                            st.write(f"Totalt antal matcher i perioden: **{filtered_data['Matcher'].sum()}**")
                            st.write(f"Antal domare i perioden: **{len(result)}**")
                            
                            # Create tabs for different views
                            tab1, tab2 = st.tabs(["Tabell", "Visualiseringar"])
                            
                            with tab1:
                                st.dataframe(
                                    result, 
                                    column_config={
                                        "Rank": st.column_config.NumberColumn("Rank", format="%d"),
                                        "Domare": st.column_config.TextColumn("Domare"),
                                        "Matcher": st.column_config.ProgressColumn(
                                            "Antal Matcher",
                                            format="%d",
                                            min_value=0,
                                            max_value=result["Matcher"].max(),
                                        ),
                                    },
                                    use_container_width=True
                                )
                                
                                # Download options
                                col1, col2 = st.columns(2)
                                with col1:
                                    csv_data, csv_mime = get_downloadable_data(result, "csv")
                                    if csv_data:
                                        st.download_button(
                                            label="Ladda ner som CSV",
                                            data=csv_data,
                                            file_name=f"referee_statistics_{start_date}_to_{end_date}.csv",
                                            mime=csv_mime,
                                        )
                                
                                with col2:
                                    excel_data, excel_mime = get_downloadable_data(result, "excel")
                                    if excel_data:
                                        st.download_button(
                                            label="Ladda ner som Excel",
                                            data=excel_data,
                                            file_name=f"referee_statistics_{start_date}_to_{end_date}.xlsx",
                                            mime=excel_mime,
                                        )
                            
                            with tab2:
                                create_charts(result, filtered_data)
                        else:
                            st.warning("Ingen data hittades för de valda filtren.")
                    else:
                        st.warning("Ingen data hittades för de valda filtren.")
        
        # Add help section
        with st.expander("Hjälp & Information"):
            st.markdown("""
            ### Hur man använder RefStat
            
            1. **Filtrera data** - Använd filteralternativen för att välja önskat datum och andra kriterier
            2. **Visa statistik** - Klicka på knappen "Visa Statistik" för att se resultaten
            3. **Ladda ner data** - Använd nedladdningsknapparna för att exportera resultaten
            
            ### Kolumnförklaring
            
            - **Rank** - Domarens placering baserat på antal matcher
            - **Domare** - Domarens namn
            - **Matcher** - Totalt antal matcher som domaren har dömt under vald period
            
            ### Vanliga frågor
            
            - **Varför ser jag inga data?** - Kontrollera att CSV-filen är korrekt formaterad och att filtren inte är för begränsade
            - **Hur uppdaterar jag data?** - Ladda upp en ny CSV-fil med uppdaterad information
            """)

if __name__ == "__main__":
    main()
