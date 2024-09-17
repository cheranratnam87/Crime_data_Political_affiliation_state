import streamlit as st
import pandas as pd
import requests
from io import StringIO

# Political affiliation dictionary for filtering
political_affiliation = {
    'Republican': ['AL', 'AK', 'AR', 'FL', 'GA', 'ID', 'IN', 'IA', 'KS', 'KY', 'LA', 'MO', 'MS', 'MT', 'NE', 'ND', 'OK', 'SC', 'SD', 'TN', 'TX', 'UT', 'WV', 'WY'],
    'Democratic': ['CA', 'CO', 'CT', 'DE', 'HI', 'IL', 'ME', 'MD', 'MA', 'MI', 'MN', 'NV', 'NJ', 'NM', 'NY', 'NC', 'OR', 'PA', 'RI', 'VA', 'VT', 'WA', 'WI']
}

# Load the dataset from the signed URL
url = 'https://cde.ucr.cjis.gov/LATEST/s3/signedurl?key=additional-datasets/srs/estimated_crimes_1979_2022.csv'
response = requests.get(url)

if response.status_code == 200:
    # Extract the actual CSV download URL from the response
    data = response.json()
    csv_url = list(data.values())[0]
    
    # Now fetch the CSV file using the signed URL
    csv_response = requests.get(csv_url)
    
    # Check if the request was successful
    if csv_response.status_code == 200:
        # Use StringIO to read the CSV content directly into pandas
        csv_data = StringIO(csv_response.text)
        df = pd.read_csv(csv_data)
        
        # Set page configuration
        st.set_page_config(page_title="Crime Statistics Dashboard", layout="wide")

        # Title and description
        st.title("US Crime Statistics Dashboard")
        st.write("""
        This dashboard shows crime statistics across different states and years. You can filter by year, state, and crime categories.
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

        # Filter the data based on the selected year range and state
        filtered_df = df[(df['year'] >= selected_year_range[0]) & (df['year'] <= selected_year_range[1]) & (df['state_abbr'].isin(selected_state))]

        # Ensure filtered data is not empty
        if not filtered_df.empty:
            # Show Top 10 States for Violent Crimes by default
            if all_states_selected and all_crimes_selected:
                st.subheader(f"Top 10 States for Violent Crimes in {selected_year_range[0]} - {selected_year_range[1]}")
                top_10_states = filtered_df[['state_abbr', 'violent_crime']].groupby('state_abbr').sum().sort_values(by='violent_crime', ascending=False).head(10)
                st.bar_chart(top_10_states)

            else:
                # Show all states based on filters without limiting to top 10
                st.subheader(f"Crime Data for Selected Year Range and States")
                crime_data = filtered_df[['state_abbr', 'state_name', 'population'] + selected_crimes]
                st.bar_chart(crime_data.set_index('state_abbr')[selected_crimes])

            # Second visual: Violent crimes over the years for selected filters
            st.subheader(f"Violent Crimes Over the Years for Selected States and Year Range")
            violent_crime_trend = filtered_df[['year', 'state_abbr', 'violent_crime']].groupby(['year', 'state_abbr']).sum().reset_index()
            st.line_chart(violent_crime_trend.pivot(index='year', columns='state_abbr', values='violent_crime'))

            # Third visual: Violent crimes over the years by political affiliation (Proportional to Population)
            st.subheader(f"Violent Crimes Per Capita Over the Years by Political Affiliation")

            # Add a new column for political affiliation
            df['political_affiliation'] = df['state_abbr'].apply(
                lambda x: 'Republican' if x in political_affiliation['Republican'] else ('Democratic' if x in political_affiliation['Democratic'] else 'Other'))

            # Filter for selected year range
            filtered_political_df = df[(df['year'] >= selected_year_range[0]) & (df['year'] <= selected_year_range[1])]

            # Calculate crime per capita (crime rate)
            filtered_political_df['crime_rate'] = filtered_political_df['violent_crime'] / filtered_political_df['population']

            # Group by year and political affiliation, summing the crime rates
            political_crime_trend = filtered_political_df[['year', 'political_affiliation', 'crime_rate']].groupby(['year', 'political_affiliation']).sum().reset_index()

            # Create a line chart showing crime rate by political affiliation
            st.line_chart(political_crime_trend.pivot(index='year', columns='political_affiliation', values='crime_rate'))

        else:
            st.write("No data available for the selected filters.")
    else:
        st.write(f"Failed to retrieve the CSV file. Status code: {csv_response.status_code}")
else:
    st.write(f"Failed to retrieve the file. Status code: {response.status_code}")
