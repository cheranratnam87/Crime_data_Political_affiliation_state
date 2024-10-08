import streamlit as st
import pandas as pd
import plotly.express as px

# Political affiliation dictionary for filtering
political_affiliation = {
    'Republican': ['AL', 'AK', 'AR', 'FL', 'GA', 'ID', 'IN', 'IA', 'KS', 'KY', 'LA', 'MO', 'MS', 'MT', 'NE', 'ND', 'OK', 'SC', 'SD', 'TN', 'TX', 'UT', 'WV', 'WY'],
    'Democratic': ['CA', 'CO', 'CT', 'DE', 'HI', 'IL', 'ME', 'MD', 'MA', 'MI', 'MN', 'NV', 'NJ', 'NM', 'NY', 'NC', 'OR', 'PA', 'RI', 'VA', 'VT', 'WA', 'WI']
}

# Load the dataset from your GitHub URL using pandas
github_url = 'https://raw.githubusercontent.com/cheranratnam87/Crime_data_Political_affiliation_state/refs/heads/master/estimated_crimes_1979_2023.csv'
df = pd.read_csv(github_url, delimiter=',')

# Set page configuration
st.set_page_config(page_title="Crime Statistics Dashboard", layout="wide")

# Title and description
st.title("US Crime Statistics Dashboard")

# Add the tagline with hyperlinks
st.markdown("""
**Data set obtained from [Federal Bureau of Investigation Crime Data Explorer - Summary Reporting System (SRS)](https://cde.ucr.cjis.gov/LATEST/webapp/#/pages/downloads) |**
**Dashboard Created by [Cheran Ratnam](https://cheranratnam.com/about/) |**
**[LinkedIn](https://www.linkedin.com/in/cheranratnam/)**
""")

# Sidebar filters
st.sidebar.header("Filters")

# Year range slider
min_year = int(df['year'].min())
max_year = int(df['year'].max())
selected_year_range = st.sidebar.slider("Select Year Range", min_value=min_year, max_value=max_year, value=(min_year, max_year))

# Filter by Political Affiliation
selected_affiliation = st.sidebar.radio("Select Political Affiliation", options=["All", "Republican", "Democratic"], index=0)

# Filter states based on political affiliation
if selected_affiliation == "Republican":
    filtered_states = political_affiliation['Republican']
elif selected_affiliation == "Democratic":
    filtered_states = political_affiliation['Democratic']
else:
    filtered_states = df['state_abbr'].dropna().unique()  # All states

# "Select All" functionality for State filter
states = df[df['state_abbr'].isin(filtered_states)]['state_abbr'].dropna().unique()
all_states_selected = st.sidebar.checkbox("Select All States", value=True)

if all_states_selected:
    selected_state = states.tolist()
else:
    selected_state = st.sidebar.multiselect("Select State(s)", options=sorted(states), default=states)

# "Select All" functionality for Crime Type filter
crime_columns = ['violent_crime', 'homicide', 'rape_legacy', 'rape_revised', 'robbery', 'aggravated_assault',
                 'property_crime', 'burglary', 'larceny', 'motor_vehicle_theft']
all_crimes_selected = st.sidebar.checkbox("Select All Crime Types", value=True)

if all_crimes_selected:
    selected_crimes = crime_columns
else:
    selected_crimes = st.sidebar.multiselect("Select Crime Types", options=crime_columns, default=crime_columns)

# Select specific crime for the map and trend visualization
selected_specific_crime = st.sidebar.selectbox("Select Specific Crime for Map", options=crime_columns, index=0)

# Filter the data based on the selected year range and state
filtered_df = df[(df['year'] >= selected_year_range[0]) & (df['year'] <= selected_year_range[1]) & (df['state_abbr'].isin(selected_state))]

# Ensure the population and selected crime columns are numeric, coerce non-numeric values to NaN
filtered_df['population'] = pd.to_numeric(filtered_df['population'], errors='coerce')
filtered_df[selected_specific_crime] = pd.to_numeric(filtered_df[selected_specific_crime], errors='coerce')

# Drop rows with missing values in these columns
filtered_df = filtered_df.dropna(subset=['population', selected_specific_crime])

# Ensure filtered data is not empty
if not filtered_df.empty:
    # First visual: Top 10 States for Selected Crime Type by default
    st.subheader(f"Top 10 States for {selected_specific_crime.title().replace('_', ' ')} in {selected_year_range[0]} - {selected_year_range[1]}")

    # Group data by state and aggregate the values for the selected crime type
    top_10_states = filtered_df[['state_abbr', selected_specific_crime]].groupby('state_abbr').sum()

    # Sort values and get the top 10 states
    top_10_states = top_10_states.sort_values(by=selected_specific_crime, ascending=False).head(10)

    # Round the numbers for better readability
    top_10_states[selected_specific_crime] = top_10_states[selected_specific_crime].round(0).astype(int)

    # Display bar chart for the top 10 states
    st.bar_chart(top_10_states)

    # Second visual: Interactive map (Optimized map for color and performance)
    st.subheader(f"{selected_specific_crime.title().replace('_', ' ')} Rate per Capita by State for {selected_year_range[0]} - {selected_year_range[1]}")

    # Add a new column for political affiliation
    filtered_df['political_affiliation'] = filtered_df['state_abbr'].apply(
        lambda x: 'Republican' if x in political_affiliation['Republican'] else 'Democratic')

    # Calculate crime rate per capita (crime rate) for the selected specific crime
    filtered_df['crime_rate'] = filtered_df[selected_specific_crime] / filtered_df['population']

    # Assign numeric values to political affiliations for the color mapping
    filtered_df['affiliation_numeric'] = filtered_df['political_affiliation'].apply(lambda x: 1 if x == 'Republican' else 0)

    # Create color scale based on political affiliation and crime rate intensity
    fig = px.choropleth(
        filtered_df,
        locations='state_abbr',
        locationmode="USA-states",
        color='crime_rate',  # Color intensity based on crime rate
        hover_name='state_name',
        hover_data={'crime_rate': True, 'political_affiliation': True},
        labels={'crime_rate': f"{selected_specific_crime.title().replace('_', ' ')} Rate"},
        scope="usa",
        color_continuous_scale=[[0, 'blue'], [1, 'red']]  # Use blue for Democratic, red for Republican
    )

    fig.update_layout(
        title_text=f"{selected_specific_crime.title().replace('_', ' ')} Rate per Capita by State",
        geo=dict(showcoastlines=True, coastlinecolor="Black"),
        coloraxis_showscale=True
    )

    st.plotly_chart(fig)

    # Third visual: Crime trends over the years for selected crime type and states
    st.subheader(f"{selected_specific_crime.title().replace('_', ' ')} Over the Years for Selected States and Year Range")

    # Group data by year and state for the selected crime type
    crime_trend = filtered_df[['year', 'state_abbr', selected_specific_crime]].groupby(['year', 'state_abbr']).sum().reset_index()

    # Pivot the data to make the years the index and states the columns, and fill missing values with 0
    crime_trend_pivot = crime_trend.pivot(index='year', columns='state_abbr', values=selected_specific_crime).fillna(0)

    # Reindex the pivoted data to ensure all years in the selected range are included, even if some have no data
    full_year_range = pd.Index(range(selected_year_range[0], selected_year_range[1] + 1))
    crime_trend_pivot = crime_trend_pivot.reindex(full_year_range, fill_value=0)

    # Plot the line chart with consistent x-axis (years)
    st.line_chart(crime_trend_pivot)

    # Fourth visual: Selected crime per capita over the years by political affiliation
    st.subheader(f"Selected Crime Trend Per Capita by Political Affiliation Over the Years")

    # Add a new column for political affiliation
    df['political_affiliation'] = df['state_abbr'].apply(
        lambda x: 'Republican' if x in political_affiliation['Republican'] else ('Democratic' if x in political_affiliation['Democratic'] else 'Other'))

    # Filter for selected year range
    filtered_political_df = df[(df['year'] >= selected_year_range[0]) & (df['year'] <= selected_year_range[1])]

    # Ensure columns are numeric and handle NaN values
    filtered_political_df['population'] = pd.to_numeric(filtered_political_df['population'], errors='coerce').fillna(0)
    filtered_political_df[selected_specific_crime] = pd.to_numeric(filtered_political_df[selected_specific_crime], errors='coerce').fillna(0)

    # Avoid division by zero
    filtered_political_df['population'].replace(0, float('nan'), inplace=True)

    # Calculate crime rate per capita for the selected specific crime
    filtered_political_df['specific_crime_rate'] = filtered_political_df[selected_specific_crime] / filtered_political_df['population']

    # Drop any rows where specific_crime_rate is NaN to avoid issues during plotting
    filtered_political_df = filtered_political_df.dropna(subset=['specific_crime_rate'])

    # Group by year and political affiliation, summing the crime rates
    specific_crime_trend = filtered_political_df[['year', 'political_affiliation', 'specific_crime_rate']].groupby(['year', 'political_affiliation']).sum().reset_index()

    # Create a line chart showing the trend of the selected specific crime per capita
    st.line_chart(specific_crime_trend.pivot(index='year', columns='political_affiliation', values='specific_crime_rate'))

else:
    st.write("No data available for the selected filters.")
