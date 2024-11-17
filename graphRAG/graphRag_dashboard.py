import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from typing import Any
from graphRAG import question_rag, get_pipelines

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server
model_cypher = "codellama/CodeLlama-13b-Instruct-hf"
model_answer = "Qwen/Qwen2.5-7B-Instruct"
# pipe_cypher, pipe_answer = get_pipelines(model_cypher=model_cypher, model_answer=model_answer)

app.layout = dbc.Container([
    dbc.Row(dbc.Col(html.H1("CDPKit GraphRAG", className="text-center my-5"))),
    
    dbc.Row([
        dbc.Col(dcc.Input(id="query-input", placeholder="Enter your query here...", type="text", className="mb-3 p-4 border rounded", style={ "width": "100%", "height": "auto"}), width=9),
        dbc.Col(dbc.Button("Submit", id="submit-button", n_clicks=0, color="primary", className="mb-3 p-4", style={"width": "100%", "height": "auto"}))
    ], className="mb-3"),

    dbc.Row(dbc.Col(dbc.Spinner(html.Div(id="output-area", className="p-3 border rounded", style={"height": "auto"}), color="primary"))),


    html.Div([
    html.P("Example Querys:", className="fw-bold mt-4"),
    html.Ul([
        html.Li(dbc.Button("What methods does the class AtomBondMapping have?", id="example-1", color="link", n_clicks=0, className="p-0")),
        html.Li(dbc.Button("What type is parameter feature of function perceiveExtendedType?", id="example-2", color="link", n_clicks=0, className="p-0")),
        html.Li(dbc.Button("What can you tell me about the class InteractionType?", id="example-3", color="link", n_clicks=0, className="p-0")),
    ])
    ]),
], fluid=True)

@app.callback(
    Output("output-area", "children"),
    Input("submit-button", "n_clicks"),
    Input("query-input", "n_submit"),
    State("query-input", "value")
)

def process_query(n_clicks: int, n_submit, query: str) -> Any:
    """
    Process the user query and return the response from the model.

    Args:
        n_clicks (int): Number of times the submit button has been clicked.
        query (str): User query.

    Returns:
        Any: HTML Div containing the response or a message prompting the user to submit a query.
    """
    if (n_clicks or n_submit) and query:
        # final_response = question_rag(query, pipe_cypher=pipe_cypher, pipe_answer=pipe_answer)
        return dbc.Card(
            dbc.CardBody([
                html.H5("Generated Answer:", className="card-title"),
                # html.P(final_response, className="card-text")
                html.P("This is just a dummy response.", className="card-text")
            ]),
            color="light", outline=True
        )
    return dbc.Card(
            dbc.CardBody([
                html.P("Submit your query to see an answer.", className="card-text text-muted")
            ]),
            color="light", outline=True
        )

# classname is deprecated, look up class_name instead? 

@app.callback(
    Output("query-input", "value"),
    [Input("example-1", "n_clicks"), Input("example-2", "n_clicks"), Input("example-3", "n_clicks")],
    prevent_initial_call=True
)
def populate_example(n1, n2, n3):
    ctx = dash.callback_context
    if not ctx.triggered:
        return ""
    else:
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if button_id == "example-1":
            return "What methods does the class AtomBondMapping have?"
        elif button_id == "example-2":
            return "What type is parameter feature of function perceiveExtendedType?"
        elif button_id == "example-3":
            return "What can you tell me about the class InteractionType?"

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)
