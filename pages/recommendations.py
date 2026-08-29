"""Recommendations page (route "/recommendations") — layout + update_recs callback."""
import dash_bootstrap_components as dbc
from dash import html, Input, Output, State

from config import GREEN
from components import _page_header, filter_row, get_filters


# ── Layout ────────────────────────────────────────────────────────────────
def layout():
    return html.Div([
        _page_header("AI Recommendations", "Actionable insights generated from your return data"),
        html.Div([
            filter_row("-rec"),
            html.Div(id="rec-list"),
        ], className="content-wrapper"),
    ])


# ── Callbacks ─────────────────────────────────────────────────────────────
def register_callbacks(app, ctrl, repo):
    @app.callback(
        Output("rec-list", "children"),
        Input("btn-apply-rec", "n_clicks"),
        State("f-cat-rec",    "value"),
        State("f-brand-rec",  "value"),
        State("f-season-rec", "value"),
        State("f-from-rec",   "value"),
        State("f-to-rec",     "value"),
        prevent_initial_call=False,
    )
    def update_recs(_, cat, brand, season, date_from, date_to):
        f = get_filters(cat, brand, season, date_from, date_to)
        ctrl.set_filters(f)
        recs = ctrl.get_recommendations()

        if not recs:
            return dbc.Alert("No recommendations generated — make sure data is loaded.", color="info")

        priority_color = {"High": "danger", "Medium": "warning", "Low": "success"}
        cards = []
        for rec in recs:
            pc = priority_color.get(getattr(rec, "priority", "Low"), "secondary")
            cards.append(
                dbc.Card(
                    dbc.CardBody(dbc.Row([
                        dbc.Col(
                            html.Div(getattr(rec, "icon", "💡"),
                                     style={"fontSize": "2rem", "textAlign": "center"}),
                            width=1,
                        ),
                        dbc.Col([
                            html.Div([
                                html.Strong(getattr(rec, "title", "Recommendation")),
                                dbc.Badge(getattr(rec, "priority", ""), color=pc, className="ms-2"),
                                dbc.Badge(getattr(rec, "category", ""), color="secondary", className="ms-1"),
                            ]),
                            html.P(getattr(rec, "description", ""),
                                   className="mb-0 mt-1 text-muted small"),
                        ]),
                    ], align="center")),
                    className="mb-3 shadow-sm border-0",
                    style={"borderLeft": f"4px solid {GREEN}"},
                )
            )
        return cards
