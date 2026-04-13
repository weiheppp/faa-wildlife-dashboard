import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Page Configuration
st.set_page_config(page_title="FAA Wildlife Strike Explorer", layout="wide")

# 1. Data Loading and Caching
@st.cache_data
def load_data():
    try:
        # Load Data
        df = pd.read_csv('wildlife_strikes.csv', encoding='latin-1')
        
        # Standardize column names
        df.columns = df.columns.str.strip().str.upper().str.replace(' ', '_')
        
        # Extract date and year
        df['INCIDENT_DATE'] = pd.to_datetime(df['INCIDENT_DATE'], errors='coerce')
        df['YEAR'] = df['INCIDENT_DATE'].dt.year
        
        # Fill missing columns to prevent errors
        if 'COST_REPAIRS' not in df.columns: df['COST_REPAIRS'] = 0
        if 'PHASE_OF_FLIGHT' not in df.columns: df['PHASE_OF_FLIGHT'] = 'Unknown'
        if 'HEIGHT' not in df.columns: df['HEIGHT'] = 0
        if 'DAMAGE' not in df.columns: df['DAMAGE'] = 'None'
        if 'SPECIES' not in df.columns: df['SPECIES'] = 'Unknown Bird'
        if 'AIRPORT' not in df.columns: df['AIRPORT'] = 'Unknown Airport'
        
        return df
    except Exception as e:
        st.error(f"Error processing data. Please check your CSV file. Error details: {e}")
        return pd.DataFrame()

df = load_data()

if not df.empty:
    # --- Sidebar (Dynamic Queries) ---
    st.sidebar.header("Data Exploration Filters")
    
    min_year = int(df['YEAR'].min()) if pd.notna(df['YEAR'].min()) else 2020
    max_year = int(df['YEAR'].max()) if pd.notna(df['YEAR'].max()) else 2024
    
    year_range = st.sidebar.slider("Select Year Range", min_year, max_year, (min_year, max_year))
    
    phases = st.sidebar.multiselect("Select Phase of Flight", 
        options=df['PHASE_OF_FLIGHT'].unique(), 
        default=df['PHASE_OF_FLIGHT'].unique()
    )
    
    filtered_df = df[
        (df['YEAR'] >= year_range[0]) & 
        (df['YEAR'] <= year_range[1]) &
        (df['PHASE_OF_FLIGHT'].isin(phases))
    ]
    
    # --- Main Interface ---
    st.title("✈️ FAA Wildlife Strike Interactive Dashboard")
    st.markdown("This application explores bird strike incidents and their economic impact on U.S. aviation safety.")
    
    # Key Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Strikes", f"{len(filtered_df):,}")
    with col2:
        total_cost = filtered_df['COST_REPAIRS'].sum()
        st.metric("Total Repair Cost", f"${total_cost:,.0f}")
    with col3:
        damage_rate = (len(filtered_df[filtered_df['DAMAGE'] != 'None']) / len(filtered_df)) * 100 if len(filtered_df) > 0 else 0
        st.metric("Damage Rate", f"{damage_rate:.1f}%")
        
    # Chart 1: Time Trend
    st.subheader("📊 Annual Strike Trend Analysis")
    trend_data = filtered_df.groupby('YEAR').size().reset_index(name='Count')
    fig_line = px.line(trend_data, x='YEAR', y='Count', title="Annual Incident Frequency in Selected Range", labels={'Count': 'Number of Strikes', 'YEAR': 'Year'}, template="plotly_white")
    st.plotly_chart(fig_line, use_container_width=True)

    # Chart 2 & 3
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("🦜 Top Wildlife Species Involved")
        species_data = filtered_df['SPECIES'].value_counts().head(10).reset_index()
        fig_bar = px.bar(species_data, x='count', y='SPECIES', orientation='h', title="Top 10 Strike Species", labels={'count': 'Occurrences', 'SPECIES': 'Species'})
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with col_right:
        st.subheader("💰 Repair Cost vs. Flight Height")
        fig_scatter = px.scatter(filtered_df, x='HEIGHT', y='COST_REPAIRS', color='PHASE_OF_FLIGHT', title="Height vs. Cost", labels={'HEIGHT': 'Height (feet)', 'COST_REPAIRS': 'Repair Cost ($)'})
        st.plotly_chart(fig_scatter, use_container_width=True)
        
    # --- Write-up Section ---
    st.divider()
    with st.expander("📝 View Assignment Write-up", expanded=False):
        st.markdown("""
        ### 1. Compelling Question
        This visualization aims to answer: **Which flight phases and wildlife species cause the most severe economic damage to US civil aviation?** By analyzing the relationship between flight height, phase of flight, and repair costs, airlines can better identify high-risk operational periods.

        ### 2. Design Rationale
        - **Visual Encodings**: A scatter plot is used to map costs, visually highlighting extreme loss events. Colors differentiate the phase of flight, making it easier to observe safety distribution across various altitudes.
        - **Interactive Techniques**: **Dynamic filtering (Year/Phase)** is introduced, allowing users to drill down from macro trends to specific scenarios. 
        - **Alternatives Considered**: A static heatmap was considered initially, but due to the large geographical span and strong temporal attributes of the data, Plotly interactive charts were chosen to support panning and precise data reading on demand.

        ### 3. Sources and References
        - Data Source: [FAA Wildlife Strike Database](https://wildlife.faa.gov/)
        - Technical Reference: [Streamlit Documentation](https://docs.streamlit.io)

        ### 4. Development Summary
        - **Total Time Spent**: Approximately 8 hours.
        - **Most Time-Consuming Aspect**: Data cleaning and format standardization.
        """)
else:
    st.warning("Waiting for data to load...")
