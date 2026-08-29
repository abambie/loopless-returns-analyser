"""Simulation page (route "/simulation") — layout + run_sim callback."""
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go

from config import ACCENT_G, CARD, HIGH, LOW, MEDIUM
from components import _page_header, stat_card, style_fig
from bootstrap import repo
from core.domain import PolicyScenario


# ── Layout ────────────────────────────────────────────────────────────────
def layout():
    cats    = repo.get_distinct_values("category")
    brands  = repo.get_distinct_values("brand")
    seasons = repo.get_distinct_values("season")

    return html.Div([
        _page_header("Policy Simulation", "Test return policy changes and see their projected impact"),
        html.Div([
            dbc.Row([
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            html.H6("Scenario Settings", className="fw-bold"),
                            html.Label("Scenario name", className="small fw-bold mt-2"),
                            dcc.Input(
                                id="sim-name", value="My Scenario",
                                className="form-control form-control-sm mb-3",
                            ),
                            html.Label("Block returns above markdown %:", className="small fw-bold"),
                            dcc.Slider(
                                id="sim-md", min=0, max=100, step=5, value=50,
                                marks={0: "0%", 25: "25%", 50: "50%", 75: "75%", 100: "100%"},
                            ),
                            html.Br(),
                            html.Label("Exclude categories", className="small fw-bold"),
                            dcc.Dropdown(cats, multi=True, id="sim-cats",
                                         placeholder="Select categories to block..."),
                            html.Br(),
                            html.Label("Exclude brands", className="small fw-bold"),
                            dcc.Dropdown(brands, multi=True, id="sim-brands",
                                         placeholder="Select brands to block..."),
                            html.Br(),
                            html.Label("Exclude seasons", className="small fw-bold"),
                            dcc.Dropdown(seasons, multi=True, id="sim-seasons",
                                         placeholder="Select seasons to block..."),
                            html.Br(),
                            dbc.Button("▶ Run Simulation", id="btn-sim",
                                       color="success", className="w-100"),
                        ]),
                        className="border-0 shadow-sm",
                    ),
                ], md=4),
                dbc.Col([
                    html.Div(id="sim-stats", className="mb-3"),
                    dcc.Graph(id="chart-sim", config={"displayModeBar": False}),
                ], md=8),
            ]),
        ], className="content-wrapper"),
    ])


# ── Callbacks ─────────────────────────────────────────────────────────────
def register_callbacks(app, ctrl, repo):
    @app.callback(
        Output("sim-stats", "children"),
        Output("chart-sim", "figure"),
        Input("btn-sim", "n_clicks"),
        State("sim-name",    "value"),
        State("sim-md",      "value"),
        State("sim-cats",    "value"),
        State("sim-brands",  "value"),
        State("sim-seasons", "value"),
        prevent_initial_call=True,
    )
    def run_sim(_, name, md, cats, brands, seasons):
        scenario = PolicyScenario(
            scenario_id="UI_SIM",
            name=name or "My Scenario",
            markdown_threshold=float(md or 50),
            excluded_categories=cats or [],
            excluded_brands=brands or [],
            excluded_seasons=seasons or [],
        )
        result = ctrl.run_scenario(scenario)

        baseline  = round(result.baseline_return_rate * 100, 1)
        simulated = round(result.simulated_return_rate * 100, 1)
        delta     = round(simulated - baseline, 1)
        delta_icon  = "↓" if delta <= 0 else "↑"
        delta_color = "#2E7D32" if delta <= 0 else "#c62828"

        stat_row = dbc.Row([
            dbc.Col(stat_card("Baseline Return Rate",  f"{baseline}%",  "📊", ACCENT_G, "#e4ede6"), md=4),
            dbc.Col(stat_card("Simulated Return Rate", f"{simulated}%", "🔁", MEDIUM,   "#fef3e2"), md=4),
            dbc.Col(
                dbc.Card(dbc.CardBody([
                    html.Div("📉" if delta <= 0 else "📈", style={"fontSize": "1.6rem"}),
                    html.P("Change", className="text-muted mb-1 mt-1",
                           style={"fontSize": "0.8rem", "fontWeight": "600"}),
                    html.H4(f"{delta_icon} {abs(delta)}%",
                            style={"color": delta_color, "fontWeight": "800", "margin": 0}),
                    html.Small(f"{result.affected_return_count} returns affected",
                               className="text-muted"),
                ]), className="shadow-sm text-center h-100 border-0"),
                md=4,
            ),
        ], className="g-3")

        fig = style_fig(go.Figure(go.Bar(
            x=["Baseline", "Simulated"],
            y=[baseline, simulated],
            marker_color=[ACCENT_G, LOW if delta <= 0 else HIGH],
            text=[f"{baseline}%", f"{simulated}%"],
            textposition="auto",
            textfont=dict(color=CARD, family="Inter"),
            width=0.4,
        )))
        fig.update_layout(
            title=f"Simulation: {scenario.name}",
            yaxis_title="Return Rate (%)",
            showlegend=False,
        )
        return stat_row, fig
