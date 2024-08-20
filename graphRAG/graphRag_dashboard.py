import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import os
import json
import torch
from typing import List, Dict, Any
from graphRAG import question_rag

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

app.layout = dbc.Container([
    html.H1("Ask me anything about the CDPKit"),
    dbc.Input(id="query-input", placeholder="Enter your query here...", type="text", className="mb-3"),
    dbc.Button("Submit Query", id="submit-button", n_clicks=0, className="mb-3"),
    html.Div(id="output-area")
])

@app.callback(
    Output("output-area", "children"),
    Input("submit-button", "n_clicks"),
    State("query-input", "value")
)
def process_query(n_clicks: int, query: str) -> Any:
    """
    Process the user query and return the response from the model.

    Args:
        n_clicks (int): Number of times the submit button has been clicked.
        query (str): User query.

    Returns:
        Any: HTML Div containing the response or a message prompting the user to submit a query.
    """
    if n_clicks > 0 and query:
        final_response = question_rag(query)
        return html.Div([
            html.H5("Query Response"),
            html.P(final_response)
        ])
    return "Submit a query ."

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)
