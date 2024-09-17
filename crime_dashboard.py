import streamlit as st
import pandas as pd
import requests
from io import StringIO
import plotly.express as px

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
    
    if csv_response.status_code == 200:
        # Use StringIO to read the CSV content directly into pandas
        csv_data = StringIO(csv_response.text)
        df = pd.read_csv(csv_data)
        
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

        # Ensure filtered data is not empty
        if not filtered_df.empty:
            # First visual: Top 10 States for Violent Crimes by default
            st.subheader(f"Top 10 States for Violent Crimes in {selected_year_range[0]} - {selected_year_range[1]}")
            top_10_states = filtered_df[['state_abbr', 'violent_crime']].groupby('state_abbr').sum().sort_values(by='violent_crime', ascending=False).head(10)
            st.bar_chart(top_10_states)

            # Second visual: Interactive map (Map with colors based on crime rate and political affiliation)
            st.subheader(f"{selected_specific_crime.title().replace('_', ' ')} Rate per Capita by State for {selected_year_range[0]} - {selected_year_range[1]}")

            # Add a new column for political affiliation
            filtered_df['political_affiliation'] = filtered_df['state_abbr'].apply(
                lambda x: 'Republican' if x in political_affiliation['Republican'] else 'Democratic')

            # Calculate crime rate per capita (crime rate) for the selected specific crime
            filtered_df['crime_rate'] = filtered_df[selected_specific_crime] / filtered_df['population']

            # Define custom color scale based on political affiliation and crime rate
            def get_color_scale(row):
                # Crime rate as alpha value to intensify colors
                intensity = row["crime_rate"] / filtered_df["crime_rate"].max()
                if row['political_affiliation'] == 'Republican':
                    return f'rgba(255, 0, 0, {intensity})'  # Red for Republican
                else:
                    return f'rgba(0, 0, 255, {intensity})'  # Blue for Democratic

            # Apply the color scale function
            filtered_df['color'] = filtered_df.apply(get_color_scale, axis=1)

            fig = px.choropleth(
                filtered_df,
                locations='state_abbr',
                locationmode="USA-states",
                color='color',  # Use custom colors based on affiliation and intensity
                hover_name='state_name',
                hover_data={'crime_rate': True, 'political_affiliation': True},
                labels={'crime_rate': f"{selected_specific_crime.title().replace('_', ' ')} Rate"},
                scope="usa"
            )

            fig.update_traces(marker=dict(line=dict(color='black', width=0.5)))  # State boundaries

            fig.update_layout(
                title_text=f"{selected_specific_crime.title().replace('_', ' ')} Rate per Capita by State",
                geo=dict(showcoastlines=True, coastlinecolor="Black"),
                coloraxis_showscale=False  # Hide color scale legend since colors are defined in RGBA
            )

            st.plotly_chart(fig)

            # Third visual: Violent crimes over the years for selected filters
            st.subheader(f"Violent Crimes Over the Years for Selected States and Year Range")
            violent_crime_trend = filtered_df[['year', 'state_abbr', 'violent_crime']].groupby(['year', 'state_abbr']).sum().reset_index()
            st.line_chart(violent_crime_trend.pivot(index='year', columns='state_abbr', values='violent_crime'))

            # Fourth visual: Violent crimes over the years by political affiliation (Proportional to Population)
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

            # Fifth visual: Specific crime trend by political affiliation (Proportional to Population)
            st.subheader(f"Selected Crime Trend Per Capita by Political Affiliation Over the Years")

            # Calculate crime rate per capita for the selected specific crime
            filtered_political_df['specific_crime_rate'] = filtered_political_df[selected_specific_crime] / filtered_political_df['population']

            # Filter the political data for the selected crime
            specific_crime_trend = filtered_political_df[['year', 'political_affiliation', 'specific_crime_rate']].groupby(['year', 'political_affiliation']).sum().reset_index()

            # Create a line chart showing the trend of the selected specific crime per capita
            st.line_chart(specific_crime_trend.pivot(index='year', columns='political_affiliation', values='specific_crime_rate'))

        else:
            st.write("No data available for the selected filters.")
    else:
        st.write(f"Failed to retrieve the CSV file. Status code: {csv_response.status_code}")
else:
    st.write(f"Failed to retrieve the file. Status code: {response.status_code}")
