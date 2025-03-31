import dash
from dash import dcc, html, Input, Output, no_update
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
from sqlalchemy import create_engine, text

#  Mapbox Access Token
MAPBOX_ACCESS_TOKEN = "pk.eyJ1IjoiZnJpdG8yMSIsImEiOiJjbTdocGVwc20wbHlzMnNwdmR4bW95NTM3In0.AEzYYt_SvQfxU7C1TG33ZQ"
px.set_mapbox_access_token(MAPBOX_ACCESS_TOKEN)

# PostgreSQL database connection config
DB_CONFIG = {
    "dbname": '271',
    "user": 'postgres',
    "password": '123456',
    "host": 'localhost',
    "port": '5434'
}
DB_URI = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"

# Fetch Data
def fetch_store_data():
    """Fetches store locations from PostgreSQL, ensuring proper data formatting."""
    try:
        engine = create_engine(DB_URI)
        with engine.connect() as conn:
            query = text("""
                SELECT store_name, 
                       NULLIF(REGEXP_REPLACE(store_latitude, '[^0-9.-]', '', 'g'), '')::FLOAT AS store_latitude, 
                       NULLIF(REGEXP_REPLACE(store_longitude, '[^0-9.-]', '', 'g'), '')::FLOAT AS store_longitude, 
                       '7eleven' AS store_type
                FROM "7eleven"
                UNION ALL
                SELECT store_name, 
                       NULLIF(REGEXP_REPLACE(store_latitude, '[^0-9.-]', '', 'g'), '')::FLOAT AS store_latitude, 
                       NULLIF(REGEXP_REPLACE(store_longitude, '[^0-9.-]', '', 'g'), '')::FLOAT AS store_longitude, 
                       'Jollibee' AS store_type
                FROM "Jollibee";
            """)
            df = pd.read_sql(query, con=conn)

        # Remove invalid coordinates
        df.dropna(subset=["store_latitude", "store_longitude"], inplace=True)
        return df
    except Exception as e:
        print(f"⚠️ Store Data Fetch Error: {e}")
        return pd.DataFrame(columns=["store_name", "store_latitude", "store_longitude", "store_type"])

# Fetch Pop Rank
def fetch_population_rankings():
    """Fetches population rankings from PostgreSQL."""
    try:
        engine = create_engine(DB_URI)
        with engine.connect() as conn:
            # Fetch regions
            query_regions = text("""
                SELECT adm1_en AS region, SUM(f_total + m_total) AS population
                FROM admpop_gen2020
                GROUP BY adm1_en
                ORDER BY population DESC;
            """)
            regions = pd.read_sql(query_regions, con=conn)

            # Fetch NCR Cities
            query_ncr = text("""
                SELECT adm3_en AS city, SUM(f_total + m_total) AS population
                FROM admpop_gen2020
                WHERE adm1_code = 'PH1300000000'
                GROUP BY adm3_en
                ORDER BY population DESC
                LIMIT 20;
            """)
            ncr = pd.read_sql(query_ncr, con=conn)

            # Fetch Cities Outside NCR (Ensuring "CITY" in Name)
            query_cities = text("""
                SELECT adm3_en AS city, SUM(f_total + m_total) AS population
                FROM admpop_gen2020
                WHERE adm1_code != 'PH1300000000' 
                AND adm3_en LIKE '%CITY%'
                GROUP BY adm3_en
                ORDER BY population DESC
                LIMIT 20;
            """)
            cities = pd.read_sql(query_cities, con=conn)

            # Fetch Municipalities (Excluding Cities)
            query_municipalities = text("""
                SELECT adm3_en AS municipality, SUM(f_total + m_total) AS population
                FROM admpop_gen2020
                WHERE adm1_code != 'PH1300000000' 
                AND adm3_en NOT LIKE '%CITY%'
                GROUP BY adm3_en
                ORDER BY population DESC
                LIMIT 20;
            """)
            municipalities = pd.read_sql(query_municipalities, con=conn)
        for df in [regions, ncr, cities, municipalities]:
            df["population"] = df["population"].astype(int).apply(lambda x: f"{x:,}")
        return regions.to_dict("records"), ncr.to_dict("records"), cities.to_dict("records"), municipalities.to_dict("records")
    except Exception as e:
        print(f"⚠️ Population Rankings Error: {e}")
        return [], [], [], []  # Return empty lists on error

# Initialize dashboard
dash.register_page(__name__, path="/dashboard")

# dashboard Layout
layout = dbc.Container([
    # ✅ dashboard Overview
    dbc.Row([
        dbc.Col(html.H4("📊 Dashboard Overview", className="text-white mt-3 text-left"), width=12)
    ]),
    dbc.Row([
        dbc.Col(html.P(
            "The Dashboard provides an interactive visualization and statistical summary of store locations and population rankings in the Philippines.",
            className="text-white text-left"
        ), width=12)
    ]),
    dbc.Row([dbc.Col(html.H3("📍 Store Locations (7-Eleven & Jollibee)", className="text-white mt-3"), width=12)]),
    #Map Section
    dbc.Row([dbc.Col([dcc.Loading(dcc.Graph(id="map-plot", config={"scrollZoom": True}), type="circle")], width=12)]),
    #Rankings Section
    dbc.Row([dbc.Col(html.H4("📌 Population Rankings", className="text-white mt-4"), width=12)]),
    #Regions & NCR Cities List
    dbc.Row([
        dbc.Col([html.H5("🌍 Philippine Regions by Population", className="text-white"), html.Div(id="regions-list")], width=6),
        dbc.Col([html.H5("🏢 NCR Cities by Population", className="text-white"), html.Div(id="ncr-list")], width=6),
    ]),
    #Cities & Municipalities Tables
    dbc.Row([
        dbc.Col([html.H5("🏙️ Top 20 Cities (Outside NCR)", className="text-white"), html.Div(id="cities-table")], width=6),
        dbc.Col([html.H5("🏡 Top 20 Municipalities", className="text-white"), html.Div(id="municipalities-table")], width=6),
    ]),
], fluid=True)

# Callback to Update Map and Rankings
@dash.callback(
    Output("map-plot", "figure"),
    Output("regions-list", "children"),
    Output("ncr-list", "children"),
    Output("cities-table", "children"),
    Output("municipalities-table", "children"),
    Input("url", "pathname")
)
def update_dashboard(_):
    """Fetches store data and population rankings, then updates the dashboard."""
    df_stores = fetch_store_data()
    regions, ncr, cities, municipalities = fetch_population_rankings()

    #Set default map view
    default_lat = 14.5826  # Centered at Rizal Park
    default_lon = 120.9787
    default_zoom = 5

    if df_stores.empty:
        fig = px.scatter_mapbox(lat=[default_lat], lon=[default_lon], zoom=default_zoom,
                                title="📍 No Store Data Available - Defaulting to Philippines",
                                mapbox_style="carto-positron")
    else:
        fig = px.scatter_mapbox(df_stores, lat="store_latitude", lon="store_longitude", color="store_type",
                                hover_name="store_name", zoom=default_zoom, title="📍 Store Locations in the Philippines",
                                center={"lat": default_lat, "lon": default_lon}, mapbox_style="carto-positron")

    #Generate Lists & Tables
    generate_list = lambda data, label: html.Ul([html.Li(f"{idx+1}. {entry[label]} - {entry['population']}") for idx, entry in enumerate(data)])

    return fig, generate_list(regions, "region"), generate_list(ncr, "city"), generate_list(cities, "city"), generate_list(municipalities, "municipality")
