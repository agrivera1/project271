import dash
from dash import dcc, html, Input, Output, State, no_update
from flask import Flask
import dash_bootstrap_components as dbc
import psycopg2
import os
import datetime
import pytz  # Import timezone for Philippine Time

# PostgreSQL database connection config
DB_CONFIG = {
    "dbname": '271',
    "user": 'postgres',
    "password": '123456',
    "host": 'localhost',
    "port": '5434'
}

# Function to Connect to PostgreSQL
def connect_db():
    return psycopg2.connect(**DB_CONFIG)

# Flask Server
server = Flask(__name__)

# Ensure Dash detects `pages/`
PAGES_PATH = os.path.join(os.path.dirname(__file__), "pages")

# Initialize Dash app with multi-page support
app = dash.Dash(
    __name__,
    server=server,
    use_pages=True,
    pages_folder=PAGES_PATH,
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True  # ✅ Prevents missing component errors
)
app.title = "Dash Auth System"

# Sidebar layout function
def get_sidebar():
    """Returns the sidebar layout when authenticated."""
    return dbc.Col([
        html.Div([
            html.H4("Navigation", className="text-white mt-4 ms-3"),
            dbc.Nav([
                dbc.NavLink("Dashboard", href="/dashboard", active="exact", className="text-white ms-3 mt-2"),
                dbc.NavLink("Import", href="/import", active="exact", className="text-white ms-3 mt-2"),
                dbc.NavLink("Download", href="/download", active="exact", className="text-white ms-3 mt-2"),
                dbc.NavLink("Logout", href="/", active="exact", className="text-danger ms-3 mt-2"),
            ], vertical=True, pills=True),

            #Live Clock at bottom of sidebar
            html.Div([
                html.P("🕒 Philippine Time:", className="text-white mt-4 ms-3"),
                html.H5(id="clock", className="text-white ms-3"),  # Dynamic clock
                dcc.Interval(id="clock-interval", interval=1000, n_intervals=0),  # Updates every second
            ], style={"position": "absolute", "bottom": "20px", "left": "20px"})  # ⬅ Position at Lower Left
        ], className="bg-dark p-3", style={"height": "100vh", "width": "200px", "position": "fixed"})  
    ], width=2, className="p-0")

# Define the app layout
app.layout = html.Div([
    dcc.Location(id="url", refresh=True),  
    dcc.Store(id="session-store", storage_type="local", data={"authenticated": False}),  

    dbc.Container([
        dbc.Row([
            dbc.Col(id="sidebar-col", width=2, className="p-0 d-none"),  #Sidebar initially hidden
            dbc.Col([dash.page_container], id="content-col", width=10)  #Content takes full width when sidebar is hidden
        ], className="gx-0")  
    ], fluid=True)
])

# Login callback with sidebar fix
@app.callback(
    [
        Output("session-store", "data"),
        Output("url", "pathname"),
        Output("login-output", "children"),
    ],
    [Input("login-btn", "n_clicks")],
    [
        State("username", "value"),
        State("password", "value"),
        State("session-store", "data"),
    ],
    prevent_initial_call=True
)
def handle_login(login_clicks, username, password, session_data):
    """Handles login and ensures sidebar appears immediately."""
    
    if not username or not password:
        return session_data, no_update, "⚠️ Please enter both username and password."

    if username == "admin" and password == "123456":
        session_data["authenticated"] = True
        return session_data, "/dashboard", ""  #Redirect to dashboard immediately

    return session_data, no_update, "❌ Invalid username or password."

# Show/Hide sidebar dynamically
@app.callback(
    [
        Output("sidebar-col", "children"),
        Output("sidebar-col", "className"),
        Output("sidebar-col", "width"),
        Output("content-col", "width"),
    ],
    [Input("url", "pathname"), Input("session-store", "data")],
)
def toggle_sidebar(pathname, session_data):
    """Shows sidebar only if the user is authenticated."""
    is_authenticated = session_data.get("authenticated", False)

    if is_authenticated and pathname in ["/dashboard", "/import", "/download"]:
        return get_sidebar(), "p-0", 2, 10  #Sidebar visible immediately
    return None, "p-0 d-none", 0, 12  #No sidebar, full width content

# Live clock callback
@app.callback(
    Output("clock", "children"),
    Input("clock-interval", "n_intervals")
)
def update_clock(n):
    """Updates the clock every second with Philippine Time."""
    philippine_tz = pytz.timezone("Asia/Manila")
    current_time = datetime.datetime.now(philippine_tz).strftime("%I:%M:%S %p")  # 12-hour format
    return current_time

if __name__ == "__main__":
    app.run_server(debug=True)
