"""
app.py — entry point for the Loopless dashboard.

Creates the Dash app, sets the root layout, registers the URL router and
the cross-page callbacks (splash, page transitions, filter bar JS), then
asks each page in pages/ to register its own callbacks. Run with:

    python app.py
"""
import os
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State

from config import BG, MODEL_DIR
from bootstrap import ctrl, repo
from components import _splash, _ai_overlay, _page_transition, topnav

from pages import dashboard            as page_dashboard
from pages import risk                 as page_risk
from pages import simulation           as page_simulation
from pages import recommendations      as page_recommendations
from pages import data_management      as page_data


# ── Dash app + root layout ────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap",
    ],
    suppress_callback_exceptions=True,
    title="Loopless",
)

# Expose the underlying Flask server for hosts such as Render or Railway.
server = app.server

app.index_string = '''<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        <link rel="icon" type="image/svg+xml" href="/assets/favicon.svg">
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>'''

app.layout = html.Div(
    [
        _splash,
        _ai_overlay,
        _page_transition,
        dcc.Store(id="nav-dummy"),
        dcc.Interval(id="splash-timer", interval=2800, n_intervals=0, max_intervals=1),
        dcc.Location(id="url"),
        topnav,
        html.Div(
            id="page-content",
            style={
                "paddingTop": "64px",
                "backgroundColor": BG,
                "minHeight": "100vh",
            },
        ),
    ],
    style={"backgroundColor": BG},
)


# ── Page routing ──────────────────────────────────────────────────────────
@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def route(path):
    if path == "/risk":             return page_risk.layout()
    if path == "/simulation":       return page_simulation.layout()
    if path == "/recommendations":  return page_recommendations.layout()
    if path == "/data":             return page_data.layout()
    return page_dashboard.layout()


# ── Cross-page callbacks (splash, transitions, filter bar JS) ─────────────
# JS implementations live in assets/clientside.js
@app.callback(
    Output("splash-screen", "style"),
    Input("splash-timer", "n_intervals"),
    prevent_initial_call=True,
)
def hide_splash(_):
    return {"display": "none"}


# Fade overlay during route changes
app.clientside_callback(
    "window.dash_clientside.loopless.pageTransition",
    Output("nav-dummy", "data"),
    Input("url", "pathname"),
    prevent_initial_call=True,
)

# Filter bar JS — same callbacks for the main and risk-page filter bars
for _sfx in ["", "-risk"]:
    for _fld in ["from", "to"]:
        app.clientside_callback(
            "window.dash_clientside.loopless.formatDate",
            Output(f"f-{_fld}{_sfx}", "value"),
            Output(f"f-{_fld}{_sfx}", "style"),
            Input(f"f-{_fld}{_sfx}",  "value"),
            prevent_initial_call=True,
        )
    app.clientside_callback(
        "window.dash_clientside.loopless.validateDateRange",
        Output(f"filter-val-msg{_sfx}", "children"),
        Input(f"btn-apply{_sfx}", "n_clicks"),
        State(f"f-from{_sfx}",   "value"),
        State(f"f-to{_sfx}",     "value"),
        State(f"f-from{_sfx}",   "style"),
        State(f"f-to{_sfx}",     "style"),
        prevent_initial_call=True,
    )
    app.clientside_callback(
        "window.dash_clientside.loopless.showToast",
        Output(f"filter-toast{_sfx}", "is_open"),
        Input(f"btn-apply{_sfx}",     "n_clicks"),
        prevent_initial_call=True,
    )


# ── Register per-page callbacks ───────────────────────────────────────────
page_dashboard.register_callbacks(app, ctrl, repo)
page_risk.register_callbacks(app, ctrl, repo)
page_simulation.register_callbacks(app, ctrl, repo)
page_recommendations.register_callbacks(app, ctrl, repo)
page_data.register_callbacks(app, ctrl, repo)


# ── Run ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    os.makedirs(MODEL_DIR, exist_ok=True)
    print("\nLoopless is starting...")
    print("   Open your browser at: http://127.0.0.1:8050\n")
    app.run(debug=False)
