import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import psycopg2
import io
import base64

# Register Download Page
dash.register_page(__name__, path="/download")

# PostgreSQL database connection config
DB_CONFIG = {
     "dbname": '271',
    "user": 'postgres',
    "password": '123456',
    "host": 'localhost',
    "port": '5434'
}

# Function to Fetch Tables from PostgreSQL
def get_table_names():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public';")
        tables = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()
        return tables
    except Exception as e:
        return [f"⚠️ Error fetching tables: {e}"]

# Fetch data from a selected table
def fetch_table_data(table_name):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        df = pd.read_sql(f'SELECT * FROM "{table_name}"', conn)
        conn.close()
        return df
    except Exception as e:
        return f"⚠️ Error fetching data: {e}"

# Download page layout
def layout():
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2("Download Data from Database", className="text-left text-white"),
                dcc.Dropdown(
                    id="table-dropdown",
                    options=[{"label": table, "value": table} for table in get_table_names()],
                    placeholder="Select a Table",
                    className="mb-3",
                    style={
                        "color": "black",  # Text inside the dropdown menu will be black
                        "backgroundColor": "white"
                    }
                ),
                html.Button("Download as CSV", id="download-csv-btn", className="btn btn-primary mt-2"),
                html.Button("Download as Excel", id="download-excel-btn", className="btn btn-success mt-2 ms-2"),
                dcc.Download(id="download-file"),
                html.Div(id="download-status", className="mt-3 text-white")
            ], width=12)
        ])
    ], fluid=True)

# Callback for downloading data
@dash.callback(
    Output("download-file", "data"),
    Output("download-status", "children"),
    Input("download-csv-btn", "n_clicks"),
    Input("download-excel-btn", "n_clicks"),
    State("table-dropdown", "value"),
    prevent_initial_call=True
)
def download_data(n_csv, n_excel, table_name):
    if not table_name:
        return None, "⚠️ Please select a table."

    df = fetch_table_data(table_name)
    if isinstance(df, str):  # Error handling
        return None, df

    trigger_id = dash.ctx.triggered_id
    if trigger_id == "download-csv-btn":
        file_content = df.to_csv(index=False).encode("utf-8")
        file_name = f"{table_name}.csv"
        mime_type = "text/csv"

    elif trigger_id == "download-excel-btn":
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Sheet1")
        file_content = output.getvalue()
        file_name = f"{table_name}.xlsx"
        mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return dcc.send_bytes(file_content, file_name), f"✅ {file_name} is ready for download!"
