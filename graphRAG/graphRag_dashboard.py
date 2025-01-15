from dash import Dash, dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
from typing import List, Dict, Any
from graphRAG import question_rag


# Initialize app with suppressed callback exceptions
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY], suppress_callback_exceptions=True)
server = app.server

# Navbar
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Chat", href="/", id="chat-link", active=True, style={"fontWeight": "bold"})),
        dbc.NavItem(dbc.NavLink("About", href="/about", id="about-link", active=False, style={"fontWeight": "bold"})),
    ],
    brand=html.Div(
        [
            html.Span("CDPKit GraphRAG", className="navbar-brand mb-0 h1"),
        ],
        style={"display": "flex", "alignItems": "center"}
    ),
    brand_href="/",
    color="primary",
    dark=True,
    fluid=True
)

# Chat layout
chat_layout = html.Div([
    dbc.Row(
        dbc.Col(
            html.Div(
                [
                    html.Img(
                        src="https://cdpkit.org/_static/logo.svg",  # Replace with your image URL
                        alt="CDPKit Icon",
                        style={"width": "175px", "height": "85px", "marginRight": "30px", "marginBottom": "15px",
                                "marginTop": "15px"}  # Image size and margin
                    ),
                    html.H1("GraphRAG Chat", className="d-inline align-middle", style={"marginBottom": "15px",
                                                                                       "marginRight": "30px", 
                                                                                       "marginTop": "15px", 
                                                                                       "fontSize": "2rem"})  # Title next to image
                ],
                style={"display": "flex", "alignItems": "center"}  # Flexbox to align horizontally
            ),
            style={"display": "flex", "justifyContent": "center", "height": "100px"}
        )
    ),

    # Chat history
    dbc.Row(dbc.Col(html.Div(id="chat-history", className="p-3 border rounded bg-light",
                             style={"height": "300px", "overflowY": "scroll"}))),

    # Input, send button, and clear button
    dbc.Row([
        dbc.Col(dcc.Input(id="query-input", placeholder="Type your message...", type="text",
                          className="form-control", style={"width": "100%"}), width=8),
        dbc.Col(dbc.Button("Send", id="send-button", n_clicks=0, color="primary",
                           className="btn-block"), width=2),
        dbc.Col(dbc.Button("Clear", id="clear-button", n_clicks=0, color="secondary",
                           className="btn-block"), width=2),
    ], className="mt-3"),

    # Example queries
    html.Div([
        html.P("Example Queries:", className="fw-bold mt-4"),
        dbc.Row([
            dbc.Col(dbc.Button("What methods does the class AtomBondMapping have?", id="example-1",
                               color="primary", className="m-1", n_clicks=0)),
            dbc.Col(dbc.Button("What type is parameter feature of function perceiveExtendedType?", id="example-2",
                               color="primary", className="m-1", n_clicks=0)),
            dbc.Col(dbc.Button("What can you tell me about the class InteractionType?", id="example-3",
                               color="primary", className="m-1", n_clicks=0)),
        ])
    ], style={"marginBottom": "20px"}),
], style={"height": "100vh", "display": "flex", "flexDirection": "column", "padding": "5px"})

# Documentation layout
docs_layout = html.Div([
    html.H2("About the CDPKit GraphRAG", className="text-center my-5", style={"fontSize": "2rem"}),
    html.P("Here you can include links or explanations about CDPKit, usage examples, and more.",
           className="lead", style={"marginTop": "20px"}),
    html.Ul([
        html.Li(html.A("CDPKit Documentation", href="https://cdpkit.org/", target="_blank")),
        html.Li(html.A("CDPKit API Documentation", href="https://docs.example.com", target="_blank")),
    ]),
])

# Main layout
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),  # Tracks the current URL
    navbar,  # Navbar at the top
    html.Div(id="page-content")  # Placeholder for dynamic content
])

# Callback to render content based on URL
@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname")
)
def display_page(pathname):
    if pathname == "/about":
        return docs_layout
    # Default to Chat layout
    return chat_layout

# Callback to manage active navbar links
@app.callback(
    [Output("chat-link", "active"),
     Output("about-link", "active")],
    Input("url", "pathname")
)

def update_active_links(pathname):
    return pathname == "/", pathname == "/about"


# Chat interactions callback
@app.callback(
    [Output("chat-history", "children"), Output("query-input", "value")],
    [
        Input("send-button", "n_clicks"),
        Input("clear-button", "n_clicks"),
        Input("example-1", "n_clicks"),
        Input("example-2", "n_clicks"),
        Input("example-3", "n_clicks"),
        Input("query-input", "n_submit"),
    ],
    [State("query-input", "value"), State("chat-history", "children")],
    prevent_initial_call=True
)
def handle_chat_interactions(send_clicks, clear_clicks, ex1_clicks, ex2_clicks, ex3_clicks, n_submit, query, chat_history):
    ctx = callback_context
    if not ctx.triggered:
        return chat_history, ""

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if chat_history is None:
        chat_history = []

    if triggered_id == "send-button" or triggered_id == "query-input":
        if query:
            response = f"I have no access to the graph yet, I'm sorry :("
            new_message = html.Div([
                html.Div(f"{query}", className="text-end text-primary fw-bold mb-2"),
                html.Div(f"{response}", className="text-start text-primary fw-normal mb-3"),
            ])
            return chat_history + [new_message], ""

    elif triggered_id == "clear-button":
        return [], ""

    elif triggered_id in ["example-1", "example-2", "example-3"]:
        example_queries = {
            "example-1": "What methods does the class AtomBondMapping have?",
            "example-2": "What type is parameter feature of function perceiveExtendedType?",
            "example-3": "What can you tell me about the class InteractionType?",
        }
        query = example_queries.get(triggered_id, "")
        response = f"I have no access to the graph yet, I'm sorry :("
        new_message = html.Div([
            html.Div(f"{query}", className="text-end text-primary fw-bold mb-2"),
            html.Div(f"{response}", className="text-start text-primary fw-normal mb-3"),
        ])
        return chat_history + [new_message], query

    return chat_history, ""

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)
