"""Data management page (route "/data") — DB status panel and dataset explorer."""
import pandas as pd
import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table, Input, Output, State

from config import (
    BG_DARK, BORDER, CARD, TEXT, TEXT_2, TEXT_MUTED, ACCENT_G, WHITE,
    DB_BACKEND,
)
from components import _page_header
from bootstrap import repo


# ── Layout ────────────────────────────────────────────────────────────────
def layout():
    count    = repo.query("SELECT COUNT(*) AS n FROM purchases")[0]["n"]
    returned = repo.query("SELECT COUNT(*) AS n FROM purchases WHERE is_returned=1")[0]["n"]
    rate     = round(returned / count * 100, 1) if count else 0
    database_label = "Local SQLite" if DB_BACKEND == "sqlite" else "Environment-configured MySQL"
    connection_label = "data/loopless.db" if DB_BACKEND == "sqlite" else "Credentials loaded securely"

    return html.Div([
        _page_header("Data Management", "Database status and dataset explorer"),
        html.Div([
            dbc.Row([
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            html.H6("Database Status", className="fw-bold mb-3"),
                            dbc.ListGroup([
                                dbc.ListGroupItem([html.Strong("Status: "),
                                    dbc.Badge("Connected ✓", color="success")]),
                                dbc.ListGroupItem([html.Strong("Database: "), database_label]),
                                dbc.ListGroupItem([html.Strong("Connection: "), connection_label]),
                                dbc.ListGroupItem([html.Strong("Total Records: "), f"{count:,}"]),
                                dbc.ListGroupItem([html.Strong("Total Returns: "), f"{returned:,}"]),
                                dbc.ListGroupItem([html.Strong("Return Rate: "), f"{rate}%"]),
                            ], flush=True),
                        ]),
                    ),
                ], md=6),

                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            html.H6("Dataset Explorer", className="fw-bold mb-3"),

                            html.Label("Search by Product ID", className="small fw-semibold mb-1"),
                            html.Div([
                                dcc.Input(
                                    id="data-search-id",
                                    placeholder="e.g. FB000001",
                                    type="text",
                                    debounce=False,
                                    style={
                                        "flex": "1", "borderRadius": "50px 0 0 50px",
                                        "border": f"1.5px solid {BORDER}",
                                        "borderRight": "none",
                                        "padding": "8px 16px",
                                        "fontSize": "0.875rem",
                                        "outline": "none",
                                        "backgroundColor": CARD,
                                        "color": TEXT,
                                    },
                                ),
                                html.Button("🔍", id="btn-search-id", n_clicks=0, style={
                                    "borderRadius": "0 50px 50px 0",
                                    "border": f"1.5px solid {BORDER}",
                                    "borderLeft": "none",
                                    "background": BG_DARK,
                                    "color": WHITE,
                                    "padding": "8px 18px",
                                    "cursor": "pointer",
                                    "fontSize": "0.9rem",
                                }),
                            ], style={"display": "flex", "marginBottom": "16px"}),

                            html.Label("Rows to display", className="small fw-semibold mb-1"),
                            html.Div([
                                dcc.Dropdown(
                                    id="data-row-count",
                                    options=[
                                        {"label": "10 rows",   "value": 10},
                                        {"label": "25 rows",   "value": 25},
                                        {"label": "50 rows",   "value": 50},
                                        {"label": "100 rows",  "value": 100},
                                        {"label": "All rows",  "value": 9999999},
                                    ],
                                    value=10, clearable=False,
                                    style={"borderRadius": "50px", "fontSize": "0.875rem"},
                                    className="filter-pill-dd",
                                ),
                            ], style={"marginBottom": "16px"}),

                            dbc.Button("Load / Refresh", id="btn-preview", color="success",
                                       size="sm", style={"borderRadius": "50px", "padding": "8px 24px"}),
                        ]),
                    ),
                ], md=6),
            ], className="g-3 mb-3"),

            html.Div(id="data-search-result", className="mb-3"),

            dbc.Card(
                dbc.CardBody([
                    html.Div(id="data-preview-label", className="fw-bold mb-3 small",
                             style={"color": TEXT_MUTED}),
                    html.Div(id="data-preview-table"),
                ]),
            ),

        ], className="content-wrapper"),
    ])


# ── Callbacks ─────────────────────────────────────────────────────────────
def register_callbacks(app, ctrl, repo):
    @app.callback(
        Output("data-preview-table", "children"),
        Output("data-preview-label", "children"),
        Input("btn-preview",    "n_clicks"),
        State("data-row-count", "value"),
        prevent_initial_call=True,
    )
    def load_preview(_, row_count):
        n    = int(row_count or 10)
        rows = repo.query("SELECT * FROM purchases") if n >= 9999999 else repo.query(f"SELECT * FROM purchases LIMIT {n}")
        if not rows:
            return dbc.Alert("No data found.", color="warning"), ""
        df = pd.DataFrame(rows)
        label = f"Showing {len(df):,} of {repo.query('SELECT COUNT(*) AS n FROM purchases')[0]['n']:,} records"
        table = dash_table.DataTable(
            columns=[{"name": c.replace("_", " ").title(), "id": c} for c in df.columns],
            data=df.to_dict("records"),
            page_size=n,
            style_header={"backgroundColor": BG_DARK, "color": CARD, "fontWeight": "600", "fontSize": "0.75rem", "border": "none"},
            style_cell={"fontSize": "0.75rem", "padding": "7px 10px", "textAlign": "left", "border": f"1px solid {BORDER}", "backgroundColor": CARD, "color": TEXT_2},
            style_data_conditional=[{"if": {"row_index": "odd"}, "backgroundColor": "rgba(45,61,46,0.04)"}],
            style_table={"overflowX": "auto"},
        )
        return table, label

    @app.callback(
        Output("data-search-result", "children"),
        Input("btn-search-id",  "n_clicks"),
        State("data-search-id", "value"),
        prevent_initial_call=True,
    )
    def search_product(_, product_id):
        if not product_id or not product_id.strip():
            return dbc.Alert("Enter a Product ID to search.", color="secondary", className="mt-2")

        rows = repo.query(
            "SELECT * FROM purchases WHERE product_id = %s LIMIT 50",
            (product_id.strip(),),
        )
        if not rows:
            return dbc.Alert(f"No records found for '{product_id.strip()}'.", color="warning", className="mt-2")

        df = pd.DataFrame(rows)

        is_ret  = int(df["is_returned"].sum()) if "is_returned" in df.columns else 0
        total   = len(df)
        reasons = df[df["is_returned"] == 1]["return_reason"].dropna().value_counts()
        top_r   = reasons.index[0] if not reasons.empty else "N/A"
        avg_p   = round(df["current_price"].mean(), 2) if "current_price" in df.columns else "N/A"
        avg_r   = round(df["customer_rating"].mean(), 1) if "customer_rating" in df.columns else "N/A"
        cat     = df["category"].iloc[0]  if "category" in df.columns else "N/A"
        brand   = df["brand"].iloc[0]     if "brand"    in df.columns else "N/A"

        summary = dbc.Card(
            dbc.CardBody([
                html.Div([
                    html.Span(f"{brand} — {cat}", style={"fontWeight": "700", "fontSize": "0.95rem", "color": TEXT}),
                    dbc.Badge(product_id.strip(), color="secondary", className="ms-2"),
                ], className="mb-2"),
                html.Div([
                    html.Div([html.Strong("Records: "),    html.Span(f"{total}")],          className="small mb-1"),
                    html.Div([html.Strong("Returns: "),    html.Span(f"{is_ret} ({round(is_ret/total*100,1) if total else 0}%)")], className="small mb-1"),
                    html.Div([html.Strong("Avg Price: "),  html.Span(f"£{avg_p}")],         className="small mb-1"),
                    html.Div([html.Strong("Avg Rating: "), html.Span(f"★ {avg_r}")],        className="small mb-1"),
                    html.Div([html.Strong("Top Reason: "), html.Span(top_r)],               className="small"),
                ]),
            ]),
            style={"borderLeft": f"3px solid {ACCENT_G}", "background": CARD, "borderRadius": "10px"},
            className="mt-2 border-0 shadow-sm",
        )
        return summary
