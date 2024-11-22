from dash import Dash, dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc

# Initialize app with suppressed callback exceptions
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY], suppress_callback_exceptions=True)
server = app.server

# Sidebar navigation
sidebar = dbc.Nav(
    [
        dbc.NavLink("Chat", href="#", id="chat-link", active=False, style={"color": "white", "fontWeight": "bold"}),
        dbc.NavLink("Documentation", href="#", id="docs-link", active=False, style={"color": "white", "fontWeight": "bold"}),
    ],
    vertical=True,
    pills=True,
    className="bg-primary text-white",
    style={"height": "100vh", "padding": "1rem"}
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
                        style={"width": "250px", "height": "125px", "marginRight": "30px", "marginBottom": "10px",
                               "marginTop": "10px"}  # Image size and margin
                    ),
                    html.H1("GraphRAG Chat", className="d-inline align-middle", style={"marginBottom": "10px",
                                                                                       "marginTop": "10px",
                                                                                       "marginRight": "30px"})  # Title next to image
                ],
                style={"display": "flex", "alignItems": "center"}  # Flexbox to align horizontally
            ), 
            style={"display": "flex", "justifyContent": "center", "height": "auto"} 
        )
    ),

    # Chat history
    dbc.Row(dbc.Col(html.Div(id="chat-history", className="p-3 border rounded bg-light",
                             style={"height": "350px", "overflowY": "scroll"}))),

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
], style={"height": "100vh", "display": "flex", "flexDirection": "column"})

# Documentation layout
docs_layout = html.Div([
    html.H2("Documentation Section", className="text-center my-5"),
    html.P("Here you can include links or explanations about CDPKit, usage examples, and more.", 
           className="lead"),
    html.Ul([
        html.Li(html.A("CDPKit GitHub Repository", href="https://github.com/example", target="_blank")),
        html.Li(html.A("CDPKit API Documentation", href="https://docs.example.com", target="_blank")),
    ]),
])

# Main layout with sidebar and default content set to the chat layout
app.layout = html.Div([
    dbc.Row([
        # Sidebar with fixed width for large screens, collapses on small screens
        dbc.Col(sidebar, width=2, lg=2, style={"transition": "width 0.3s ease"}),
        dbc.Col(html.Div(id="main-content", children=chat_layout), width=10, lg=10),
    ], style={"display": "flex", "flexDirection": "row", "width": "100%", "height": "100vh"}),
], style={"height": "100vh", "width": "100%", "display": "flex", "flexDirection": "row"})


# Callback to update the main content and manage active state for sidebar tabs
@app.callback(
    [Output("main-content", "children"),
     Output("chat-link", "active"),
     Output("docs-link", "active")],
    [Input("chat-link", "n_clicks"), Input("docs-link", "n_clicks")],
    prevent_initial_call=True
)
def render_content(chat_clicks, docs_clicks):
    ctx = callback_context
    if not ctx.triggered:
        # Default to Chat page
        return chat_layout, True, False

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if triggered_id == "chat-link":
        return chat_layout, True, False
    elif triggered_id == "docs-link":
        return docs_layout, False, True

    return html.Div("404: Page not found"), False, False  # Fallback for unexpected navigation

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

    # Determine which button or input triggered the callback
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Initialize chat history if it's None
    if chat_history is None:
        chat_history = []

    if triggered_id == "send-button" or triggered_id == "query-input":
        if query:
            response = f"I have no access to the graph yet, I'm sorry :("
            new_message = html.Div([
                html.Div(f"{query}", className="text-end text-primary fw-bold mb-2"),
                html.Div(f"{response}", className="text-start text-primary fw-normal mb-3"),
            ])
            return chat_history + [new_message], ""  # Reset input field after sending the message

    elif triggered_id == "clear-button":
        return [], ""  # Clear chat history and input field

    elif triggered_id in ["example-1", "example-2", "example-3"]:
        # Example queries
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
        return chat_history + [new_message], query  # Show example query in the input field

    return chat_history, ""  # Default: return current state

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)
