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

        # Filter the data based on the selected year range and state
        filtered_df = df[(df['year'] >= selected_year_range[0]) & (df['year'] <= selected_year_range[1]) & (df['state_abbr'].isin(filtered_states))]

        # Ensure filtered data is not empty
        if not filtered_df.empty:
            # First visual: Top 10 States for Violent Crimes (Original visual)
            st.subheader(f"Top 10 States for Violent Crimes in {selected_year_range[0]} - {selected_year_range[1]}")
            top_10_states = filtered_df[['state_abbr', 'violent_crime']].groupby('state_abbr').sum().sort_values(by='violent_crime', ascending=False).head(10)
            st.bar_chart(top_10_states)

            # Add a new column for political affiliation
            filtered_df['political_affiliation'] = filtered_df['state_abbr'].apply(
                lambda x: 'Republican' if x in political_affiliation['Republican'] else ('Democratic' if x in political_affiliation['Democratic'] else 'Other'))

            # Calculate crime rate per capita (crime rate)
            filtered_df['crime_rate'] = filtered_df['violent_crime'] / filtered_df['population']

            # Second visual: Interactive choropleth map (New visual)
            st.subheader(f"Crime Rate per Capita by State for {selected_year_range[0]} - {selected_year_range[1]}")

            fig = px.choropleth(
                filtered_df,
                locations='state_abbr',
                locationmode="USA-states",
                color='crime_rate',
                hover_name='state_name',
                hover_data={'population': True, 'violent_crime': True},
                color_continuous_scale="Reds",
                labels={'crime_rate': 'Crime Rate per Capita'},
                scope="usa"
            )

            fig.update_layout(
                title_text='Crime Rate per Capita by State',
                geo=dict(showcoastlines=True, coastlinecolor="Black")
            )

            st.plotly_chart(fig)

            # Third visual: Violent crimes over the years for selected filters (Proportional to population)
            st.subheader(f"Violent Crimes Per Capita Over the Years for Selected States and Year Range")
            violent_crime_trend = filtered_df[['year', 'state_abbr', 'crime_rate']].groupby(['year', 'state_abbr']).sum().reset_index()
            st.line_chart(violent_crime_trend.pivot(index='year', columns='state_abbr', values='crime_rate'))

            # Fourth visual: Violent crimes over the years by political affiliation (Proportional to Population) (Original visual)
            st.subheader(f"Violent Crimes Per Capita Over the Years by Political Affiliation")

            # Group by year and political affiliation, summing the crime rates
            political_crime_trend = filtered_df[['year', 'political_affiliation', 'crime_rate']].groupby(['year', 'political_affiliation']).sum().reset_index()

            # Create a line chart showing crime rate by political affiliation
            st.line_chart(political_crime_trend.pivot(index='year', columns='political_affiliation', values='crime_rate'))

        else:
            st.write("No data available for the selected filters.")
    else:
        st.write(f"Failed to retrieve the CSV file. Status code: {csv_response.status_code}")
else:
    st.write(f"Failed to retrieve the file. Status code: {response.status_code}")
