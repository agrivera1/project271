import dash
from dash import dcc, html
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/")  # Default home page

layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H2("Login", className="text-center mb-4 text-white"),
                    dbc.Input(
                        id="username",
                        type="text",
                        placeholder="Enter Username",
                        className="mb-3",
                        style={"color": "white", "backgroundColor": "#333", "border": "1px solid #555"}
                    ),
                    dbc.Input(
                        id="password",
                        type="password",
                        placeholder="Enter Password",
                        className="mb-3",
                        style={"color": "white", "backgroundColor": "#333", "border": "1px solid #555"}
                    ),
                    dbc.Button("Login", id="login-btn", color="primary", className="mt-2 w-100", n_clicks=0),

                    #Fixed Space for Error Message
                    html.Div(
                        id="login-output",
                        className="mt-3 text-center text-warning",
                        style={"minHeight": "25px"}  #Reserved space for messages
                    ),
                ])
            ], style={
                "width": "400px",  #Fixed Width
                "height": "400px",  #Fixed Height
                "margin": "auto",
                "backgroundColor": "#222",
                "color": "white",
                "padding": "20px",
                "borderRadius": "10px",
                "boxShadow": "0px 4px 10px rgba(255, 255, 255, 0.1)"
            })
        ], width=6, className="d-flex justify-content-center")  #Center content
    ], className="justify-content-center align-items-center vh-100")  #Full Vertical Centering
], fluid=True)
