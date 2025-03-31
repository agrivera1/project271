import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import psycopg2
import io
import base64
import chardet  #Auto-detect file encoding

# Register import page
dash.register_page(__name__, path="/import")

# PostgreSQL database connection config
DB_CONFIG = {
    "dbname": '271',
    "user": 'postgres',
    "password": '123456',
    "host": 'localhost',
    "port": '5434'
}

# Function to Detect Encoding
def detect_encoding(file_bytes):
    """Detects the encoding of a file to prevent decoding errors."""
    result = chardet.detect(file_bytes)
    return result["encoding"]

# Function to create a table dynamically in PostgreSQL
def create_table_in_db(df, table_name):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        column_defs = ", ".join([f'"{col}" TEXT' for col in df.columns])
        create_query = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({column_defs});'
        cur.execute(create_query)
        conn.commit()
        cur.close()
        conn.close()
        return f"✅ Table '{table_name}' created successfully!"
    except Exception as e:
        return f"⚠️ Error creating table: {e}"

# Function to insert data into PostgreSQL
def insert_data_to_db(df, table_name):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        columns = ", ".join([f'"{col}"' for col in df.columns])
        values_placeholder = ", ".join(["%s"] * len(df.columns))
        insert_query = f'INSERT INTO "{table_name}" ({columns}) VALUES ({values_placeholder})'
        for _, row in df.iterrows():
            cur.execute(insert_query, tuple(row))
        conn.commit()
        cur.close()
        conn.close()
        return f"✅ Data successfully inserted into '{table_name}'!"
    except Exception as e:
        return f"⚠️ Error inserting data: {e}"

# Layout of import page
def layout():
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2("Import Data to Database", className="text-left text-white"),
                dcc.Upload(
                    id="upload-data",
                    children=html.Div(["📂 Drag and Drop or Select a File"]),
                    style={
                        "width": "100%",
                        "height": "60px",
                        "lineHeight": "60px",
                        "borderWidth": "2px",
                        "borderStyle": "dashed",
                        "borderRadius": "5px",
                        "textAlign": "center",
                        "margin": "10px",
                        "backgroundColor": "#222",
                        "color": "white"
                    },
                    multiple=False
                ),
                html.Div(id="selected-file", className="mt-2 text-info"),  # Show file name
                dcc.Input(
                    id="table-name-input",
                    type="text",
                    placeholder="Enter Table Name",
                    className="mb-3 form-control"
                ),
                html.Button("Upload", id="upload-btn", className="btn btn-primary mt-2"),
                html.Div(id="upload-status", className="mt-3 text-white"),
                html.Hr(),
                html.H4("Preview Data", className="text-white"),
                dash_table.DataTable(
                    id="preview-table",
                    style_table={"overflowX": "auto"},
                    style_data={  # Set text color to black
                        "color": "black",
                        "backgroundColor": "white"
                    },
                    style_header={  # Ensure headers remain readable
                        "color": "black",
                        "backgroundColor": "#f8f9fa",
                        "fontWeight": "bold"
                    }
                )
            ], width=12)
        ])
    ], fluid=True)

# Callback to Show Selected File Name
@dash.callback(
    Output("selected-file", "children"),
    Input("upload-data", "filename"),
    prevent_initial_call=True
)
def show_selected_file(filename):
    """Displays the selected file name before uploading."""
    if filename:
        return f"📂 Selected File: {filename}"
    return ""

# Callback for handling file upload and table creation
@dash.callback(
    Output("preview-table", "data"),
    Output("preview-table", "columns"),
    Output("upload-status", "children"),
    Input("upload-btn", "n_clicks"),
    State("upload-data", "contents"),
    State("upload-data", "filename"),
    State("table-name-input", "value"),
    prevent_initial_call=True
)
def handle_upload(n_clicks, file_contents, filename, table_name):
    if not file_contents or not filename:
        return [], [], "⚠️ No file uploaded."

    if not table_name:
        return [], [], "⚠️ Please enter a table name."

    # Read file content
    content_type, content_string = file_contents.split(",")
    decoded_bytes = base64.b64decode(content_string)

    try:
        encoding = detect_encoding(decoded_bytes)  # Detect encoding
        print(f"🔍 Detected Encoding: {encoding}")

        decoded = io.BytesIO(decoded_bytes)

        if filename.endswith(".csv"):
            df = pd.read_csv(decoded, encoding=encoding, on_bad_lines="skip")
        elif filename.endswith(".xlsx"):
            df = pd.read_excel(decoded, engine="openpyxl")
        else:
            return [], [], "⚠️ Unsupported file format. Please upload CSV or Excel."

        # Remove special characters
        df.columns = [col.strip().replace(" ", "_").replace("/", "_") for col in df.columns]

        # Remove empty columns
        df.dropna(axis=1, how="all", inplace=True)

        # Convert all data to string type (prevents numeric errors)
        df = df.astype(str)

        # Create Table
        create_message = create_table_in_db(df, table_name)

        # Insert data into PostgreSQL
        insert_message = insert_data_to_db(df, table_name)

        # Convert to dash table format
        return df.to_dict("records"), [{"name": i, "id": i} for i in df.columns], f"{create_message} {insert_message}"

    except Exception as e:
        return [], [], f"⚠️ Error processing file: {e}"
