"""
The cross-page filter bar.

filter_row(id_suffix)  Builds the bar (Category / Brand / Season dropdowns
                       + date range + Apply + toast). id_suffix is appended
                       to every input id so the bar can appear on multiple
                       pages without collisions ("" / "-risk" / "-rec").
get_filters(...)       Turns the input values into the FilterMap dict the
                       repository expects.
"""
import dash_bootstrap_components as dbc
from dash import dcc, html

from config import BORDER, TEXT, TEXT_MUTED
from bootstrap import repo


def filter_row(id_suffix=""):
    """The reusable filter bar — Category / Brand / Season + date range + Apply."""
    cats    = [{"label": "All Categories", "value": "All"}] + [{"label": v, "value": v} for v in repo.get_distinct_values("category")]
    brands  = [{"label": "All Brands",     "value": "All"}] + [{"label": v, "value": v} for v in repo.get_distinct_values("brand")]
    seasons = [{"label": "All Seasons",    "value": "All"}] + [{"label": v, "value": v} for v in repo.get_distinct_values("season")]

    dd_style = {
        "borderRadius": "50px",
        "border": f"1.5px solid {BORDER}",
        "fontSize": "0.875rem",
        "flex": "1",
        "minWidth": "130px",
    }

    return html.Div(
        [html.Div([
            # ── Icon + label ───────────────────────────────────────────────
            html.Div([
                html.Div("⊞", style={
                    "width": "34px", "height": "34px", "borderRadius": "9px",
                    "background": "#f3f4f6",
                    "border": f"1.5px solid {BORDER}",
                    "display": "flex", "alignItems": "center", "justifyContent": "center",
                    "fontSize": "1rem", "color": TEXT_MUTED, "flexShrink": "0",
                }),
                html.Span("Filters", style={
                    "fontWeight": "700", "fontSize": "0.875rem",
                    "color": TEXT, "letterSpacing": "0.01em",
                }),
            ], style={
                "display": "flex", "alignItems": "center", "gap": "8px",
                "paddingRight": "18px", "borderRight": f"1.5px solid {BORDER}",
                "flexShrink": "0",
            }),

            # ── Dropdowns ─────────────────────────────────────────────────
            dcc.Dropdown(cats,    "All", id=f"f-cat{id_suffix}",    clearable=False,
                         style=dd_style, className="filter-pill-dd"),
            dcc.Dropdown(brands,  "All", id=f"f-brand{id_suffix}",  clearable=False,
                         style=dd_style, className="filter-pill-dd"),
            dcc.Dropdown(seasons, "All", id=f"f-season{id_suffix}", clearable=False,
                         style=dd_style, className="filter-pill-dd"),

            # ── Date range ────────────────────────────────────────────────
            html.Div([
                html.Span("📅", style={"fontSize": "0.9rem", "color": TEXT_MUTED}),
                dcc.Input(id=f"f-from{id_suffix}", placeholder="YYYY-MM-DD",
                          className="filter-date-pill", type="text"),
                html.Span("→", style={"color": TEXT_MUTED, "fontSize": "0.85rem", "flexShrink": "0"}),
                dcc.Input(id=f"f-to{id_suffix}", placeholder="YYYY-MM-DD",
                          className="filter-date-pill", type="text"),
            ], style={
                "display": "flex", "alignItems": "center", "gap": "6px",
                "background": "#f9fafb",
                "border": f"1.5px solid {BORDER}",
                "borderRadius": "50px", "padding": "0 14px", "height": "40px",
                "flex": "1", "minWidth": "200px",
            }),

            # ── Apply button ──────────────────────────────────────────────
            html.Button("Apply", id=f"btn-apply{id_suffix}", n_clicks=0,
                        className="filter-apply-btn"),
        ], className="filter-bar-inner"),
        # ── Validation message ────────────────────────────────────────────
        html.Div(id=f"filter-val-msg{id_suffix}", className="filter-val-msg"),
        # ── Success toast ─────────────────────────────────────────────────
        dbc.Toast(
            [html.P("Your filters have been applied.", className="mb-0",
                    style={"fontSize": "0.875rem"})],
            id=f"filter-toast{id_suffix}",
            header="Filters Applied",
            is_open=False,
            dismissable=True,
            duration=3000,
            color="success",
            style={
                "position": "fixed", "bottom": "24px", "right": "24px",
                "zIndex": "9999", "minWidth": "260px",
                "boxShadow": "0 8px 28px rgba(0,0,0,0.22)",
                "borderRadius": "14px", "fontFamily": "'Inter', sans-serif",
            },
        ),
        ],
        className="filter-bar-card",
    )


def get_filters(cat, brand, season, date_from, date_to):
    """Translate dropdown/input values into a FilterMap dict for the repository."""
    f = {}
    if cat    and cat    != "All": f["category"] = cat
    if brand  and brand  != "All": f["brand"]    = brand
    if season and season != "All": f["season"]   = season
    if date_from: f["date_from"] = date_from
    if date_to:   f["date_to"]   = date_to
    return f
