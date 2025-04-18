import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import os

# Set page configuration
st.set_page_config(
    page_title="RefStat - Domarstatistik",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for improved styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: 700;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #1E3A8A;
        margin-top: 2rem;
        margin-bottom: 1rem;
        font-weight: 600;
    }
    .stButton>button {
        background-color: #1E3A8A;
        color: white;
        font-weight: 600;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        border: none;
    }
    .stButton>button:hover {
        background-color: #3B82F6;
    }
    div[data-testid="stDataFrame"] {
        margin-top: 1rem;
        border-radius: 6px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .footer {
        text-align: center;
        margin-top: 3rem;
        font-size: 0.8rem;
        color: #6B7280;
    }
    .metric-card {
        background-color: #F3F4F6;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1E3A8A;
    }
    .metric-label {
        font-size: 1rem;
        color: #6B7280;
    }
    .warning {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 0.75rem;
        border-radius: 6px;
        margin-bottom: 1rem;
    }
    .success {
        background-color: #D1FAE5;
        color: #065F46;
        padding: 0.75rem;
        border-radius: 6px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Session state initialization
if "data" not in st.session_state:
    st.session_state["data"] = None
if "filtered_data" not in st.session_state:
    st.session_state["filtered_data"] = None
if "show_stats" not in st.session_state:
    st.session_state["show_stats"] = False
if "error" not in st.session_state:
    st.session_state["error"] = None

# Function to load data from a local file path
@st.cache_data
def load_data_from_path(file_path):
    try:
        df = pd.read_csv(file_path)
        # Convert Date column to datetime
        df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
        return df
    except Exception as e:
        st.session_state["error"] = f"Kunde inte ladda data: {str(e)}"
        return None

# Function to filter data by date range and other criteria
def filter_data_by_date(df, start_date, end_date, sport=None, district=None, min_matches=None):
    if df is None:
        return None
    
    try:
        filtered_df = df.copy()
        
        # Filter by date range
        filtered_df = filtered_df[(filtered_df["Date"] >= pd.to_datetime(start_date)) & 
                                  (filtered_df["Date"] <= pd.to_datetime(end_date))]
        
        # Apply additional filters if provided
        if sport and sport != "Alla":
            filtered_df = filtered_df[filtered_df["Sport"] == sport]
        
        if district and district != "Alla":
            filtered_df = filtered_df[filtered_df["District"] == district]
        
        # Group by referee and sum matches
        grouped = filtered_df.groupby("Domare")["Matcher"].sum().reset_index()
        
        # Apply minimum matches filter if provided
        if min_matches and min_matches > 0:
            grouped = grouped[grouped["Matcher"] >= min_matches]
        
        # Sort by matches descending
        grouped = grouped.sort_values(by="Matcher", ascending=False).reset_index(drop=True)
        
        return grouped, filtered_df
    except Exception as e:
        st.session_state["error"] = f"Fel vid filtrering av data: {str(e)}"
        return None, None

# Function to generate referee statistics
def generate_referee_stats(filtered_df):
    if filtered_df is None or filtered_df.empty:
        return None
    
    stats = {}
    
    # Total matches in the period
    stats["total_matches"] = filtered_df["Matcher"].sum()
    
    # Total unique referees
    stats["total_referees"] = filtered_df["Domare"].nunique()
    
    # Average matches per referee
    stats["avg_matches"] = stats["total_matches"] / stats["total_referees"] if stats["total_referees"] > 0 else 0
    
    # Most active referee
    most_active = filtered_df.groupby("Domare")["Matcher"].sum().sort_values(ascending=False)
    stats["most_active"] = most_active.index[0] if len(most_active) > 0 else "N/A"
    stats["most_active_count"] = most_active.iloc[0] if len(most_active) > 0 else 0
    
    return stats

# Function to create visualizations
def create_visualizations(result_df, filtered_raw_df):
    visualizations = {}
    
    if result_df is None or result_df.empty:
        return visualizations
    
    # 1. Top referees bar chart
    top_n = min(10, len(result_df))
    top_referees = result_df.head(top_n)
    fig_top = px.bar(
        top_referees,
        x="Domare",
        y="Matcher",
        title=f"Topp {top_n} Domare efter Antal Matcher",
        labels={"Domare": "Domare", "Matcher": "Antal Matcher"},
        color="Matcher",
        color_continuous_scale="Blues",
    )
    fig_top.update_layout(
        xaxis_title="Domare",
        yaxis_title="Antal Matcher",
        xaxis={'categoryorder':'total descending'},
        plot_bgcolor="white",
        font=dict(family="Arial", size=12),
    )
    visualizations["top_referees"] = fig_top
    
    # 2. Distribution of matches histogram
    fig_dist = px.histogram(
        result_df,
        x="Matcher",
        nbins=20,
        title="Fördelning av Matcher per Domare",
        labels={"Matcher": "Antal Matcher", "count": "Antal Domare"},
        color_discrete_sequence=["#1E3A8A"],
    )
    fig_dist.update_layout(
        xaxis_title="Antal Matcher",
        yaxis_title="Antal Domare",
        plot_bgcolor="white",
        bargap=0.1,
    )
    visualizations["match_distribution"] = fig_dist
    
    # 3. Matches over time (if raw data is available)
    if filtered_raw_df is not None and not filtered_raw_df.empty and "Date" in filtered_raw_df.columns:
        # Aggregate matches by date
        matches_by_date = filtered_raw_df.groupby(filtered_raw_df["Date"].dt.date)["Matcher"].sum().reset_index()
        fig_time = px.line(
            matches_by_date,
            x="Date",
            y="Matcher",
            title="Matcher över Tid",
            labels={"Date": "Datum", "Matcher": "Antal Matcher"},
            markers=True,
        )
        fig_time.update_layout(
            xaxis_title="Datum",
            yaxis_title="Antal Matcher",
            plot_bgcolor="white",
        )
        visualizations["matches_over_time"] = fig_time
    
    return visualizations

# Main application layout
def main():
    # Header with logo (emoji as placeholder)
    st.markdown('<div class="main-header">🏆 RefStat - Domarstatistik</div>', unsafe_allow_html=True)
    
    # Sidebar for controls
    with st.sidebar:
        st.markdown("### Inställningar")
        
        # File upload option
        uploaded_file = st.file_uploader("Ladda upp CSV-fil", type=["csv"])
        
        # Or use default file
        use_default = st.checkbox("Använd standardfil", value=True)
        
        if uploaded_file is not None:
            # User uploaded a file
            st.session_state["data"] = pd.read_csv(uploaded_file)
            st.session_state["data"]["Date"] = pd.to_datetime(st.session_state["data"]["Date"], errors='coerce')
        elif use_default:
            # Use the default file
            file_path = "vsibf.csv"
            if os.path.exists(file_path):
                st.session_state["data"] = load_data_from_path(file_path)
            else:
                st.warning(f"Standardfilen '{file_path}' hittades inte.")
                st.session_state["data"] = None
    
    # Display error if any
    if st.session_state["error"]:
        st.markdown(f'<div class="warning">{st.session_state["error"]}</div>', unsafe_allow_html=True)
        st.session_state["error"] = None  # Clear error after displaying
    
    # Main content area
    if st.session_state["data"] is not None:
        data = st.session_state["data"]
        
        # Find the min and max dates in the dataset
        min_date = data["Date"].min().date()
        max_date = data["Date"].max().date()
        
        # Create columns for filters
        col1, col2 = st.columns(2)
        
        with col1:
            # If Sport column exists in the dataset
            if "Sport" in data.columns:
                sports = ["Alla"] + sorted(data["Sport"].unique().tolist())
                sport = st.selectbox("Idrott", sports, index=0)
            else:
                sport = "Innebandy"  # Default value
                st.selectbox("Idrott", ["Innebandy"], index=0)
            
            # Date range selection
            start_date = st.date_input(
                "Från", 
                value=min_date,
                min_value=min_date,
                max_value=max_date
            )
        
        with col2:
            # If District column exists in the dataset
            if "District" in data.columns:
                districts = ["Alla"] + sorted(data["District"].unique().tolist())
                district = st.selectbox("Förbund", districts, index=0)
            else:
                district = "Västsvenska"  # Default value
                st.selectbox("Förbund", ["Västsvenska"], index=0)
            
            # End date selection
            end_date = st.date_input(
                "Till", 
                value=max_date,
                min_value=min_date,
                max_value=max_date
            )
        
        # Additional filters
        col3, col4 = st.columns(2)
        
        with col3:
            min_matches = st.number_input(
                "Minst antal matcher", 
                min_value=0, 
                value=0, 
                help="Filtrera domare med minst detta antal matcher"
            )
        
        with col4:
            display_top_n = st.slider(
                "Visa topp domare", 
                min_value=5, 
                max_value=50, 
                value=20,
                help="Antal domare att visa i statistiken"
            )
        
        # Action buttons
        col_btn1, col_btn2 = st.columns([1, 1])
        
        with col_btn1:
            if st.button("Visa Statistik", use_container_width=True):
                if start_date > end_date:
                    st.markdown('<div class="warning">Startdatum måste vara före eller samma som slutdatum.</div>', unsafe_allow_html=True)
                else:
                    # Filter and process the data
                    result, filtered_raw = filter_data_by_date(
                        data, 
                        start_date, 
                        end_date, 
                        sport=sport if sport != "Alla" else None,
                        district=district if district != "Alla" else None,
                        min_matches=min_matches
                    )
                    
                    st.session_state["filtered_data"] = result
                    st.session_state["filtered_raw"] = filtered_raw
                    st.session_state["show_stats"] = True
        
        with col_btn2:
            if st.button("Återställ Filter", use_container_width=True):
                st.session_state["show_stats"] = False
                st.session_state["filtered_data"] = None
                st.session_state["filtered_raw"] = None
                st.experimental_rerun()
        
        # Display results if available
        if st.session_state["show_stats"] and st.session_state["filtered_data"] is not None:
            result = st.session_state["filtered_data"]
            filtered_raw = st.session_state["filtered_raw"]
            
            # Success message
            period_text = f"{start_date.strftime('%Y-%m-%d')} till {end_date.strftime('%Y-%m-%d')}"
            st.markdown(f'<div class="success">Visar statistik för perioden {period_text}</div>', unsafe_allow_html=True)
            
            # Generate statistics
            stats = generate_referee_stats(result)
            
            if stats:
                # Display key metrics in cards
                metric_cols = st.columns(4)
                
                with metric_cols[0]:
                    st.markdown(f'''
                    <div class="metric-card">
                        <div class="metric-value">{stats["total_matches"]}</div>
                        <div class="metric-label">Totalt antal matcher</div>
                    </div>
                    ''', unsafe_allow_html=True)
                
                with metric_cols[1]:
                    st.markdown(f'''
                    <div class="metric-card">
                        <div class="metric-value">{stats["total_referees"]}</div>
                        <div class="metric-label">Antal domare</div>
                    </div>
                    ''', unsafe_allow_html=True)
                
                with metric_cols[2]:
                    st.markdown(f'''
                    <div class="metric-card">
                        <div class="metric-value">{stats["avg_matches"]:.1f}</div>
                        <div class="metric-label">Genomsnitt matcher/domare</div>
                    </div>
                    ''', unsafe_allow_html=True)
                
                with metric_cols[3]:
                    st.markdown(f'''
                    <div class="metric-card">
                        <div class="metric-value">{stats["most_active_count"]}</div>
                        <div class="metric-label">Matcher (mest aktiv domare)</div>
                    </div>
                    ''', unsafe_allow_html=True)
            
            # Create visualizations
            visualizations = create_visualizations(result, filtered_raw)
            
            # Display visualizations in tabs
            if visualizations:
                viz_tabs = st.tabs(["Topplista", "Fördelning", "Över Tid"])
                
                with viz_tabs[0]:
                    if "top_referees" in visualizations:
                        st.plotly_chart(visualizations["top_referees"], use_container_width=True)
                
                with viz_tabs[1]:
                    if "match_distribution" in visualizations:
                        st.plotly_chart(visualizations["match_distribution"], use_container_width=True)
                
                with viz_tabs[2]:
                    if "matches_over_time" in visualizations:
                        st.plotly_chart(visualizations["matches_over_time"], use_container_width=True)
                    else:
                        st.info("Tidsdata är inte tillgänglig för visualisering.")
            
            # Display the results table with pagination
            st.markdown('<div class="sub-header">Domarstatistik</div>', unsafe_allow_html=True)
            
            # Limit to top N if there are many results
            if len(result) > display_top_n:
                st.info(f"Visar topp {display_top_n} av {len(result)} domare baserat på antal matcher")
                result = result.head(display_top_n)
            
            # Add rank column
            result.insert(0, "Rank", range(1, len(result) + 1))
            
            # Display the dataframe
            st.dataframe(
                result,
                column_config={
                    "Rank": st.column_config.NumberColumn("Rank", format="%d"),
                    "Domare": st.column_config.TextColumn("Domare"),
                    "Matcher": st.column_config.NumberColumn("Matcher", format="%d"),
                },
                hide_index=True,
                use_container_width=True,
            )
            
            # Download options
            col_dl1, col_dl2 = st.columns(2)
            
            with col_dl1:
                csv = result.to_csv(index=False)
                st.download_button(
                    label="Ladda ner som CSV",
                    data=csv,
                    file_name=f"domarstatistik_{start_date}_till_{end_date}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            
            with col_dl2:
                # Format as Excel
                excel_buffer = pd.ExcelWriter(f"domarstatistik_{start_date}_till_{end_date}.xlsx")
                result.to_excel(excel_buffer, index=False)
                st.download_button(
                    label="Ladda ner som Excel",
                    data=excel_buffer,
                    file_name=f"domarstatistik_{start_date}_till_{end_date}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
    
    else:
        # No data available, show instructions
        st.info("""
        Ingen data tillgänglig. Vänligen:
        1. Ladda upp en CSV-fil med domarstatistik, eller
        2. Sätt 'Använd standardfil' och kontrollera att 'vsibf.csv' finns tillgänglig
        
        CSV-filen bör innehålla kolumnerna: Date, Domare, Matcher (och eventuellt Sport, District)
        """)
    
    # Footer
    st.markdown('<div class="footer">© 2025 RefStat - Domarstatistik</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
