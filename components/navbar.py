"""
Top-level page chrome.

topnav           The fixed top navigation bar (logo + page links + database
                 link). Mounted once in app.layout.
_page_header()   Big title + optional subtitle at the top of each page.
"""
import dash_bootstrap_components as dbc
from dash import html

from config import WHITE


def _page_header(title, subtitle=""):
    children = [html.H1(title, className="page-heading")]
    if subtitle:
        children.append(html.P(subtitle, className="page-subheading"))
    return html.Div(children, className="page-header")


# Top navigation bar (mounted once in app.layout).
_NAV_LINKS = [
    ("Dashboard",          "/"),
    ("High-Risk Products", "/risk"),
]

topnav = html.Div(
    html.Div([
        html.Div([
            html.Div("L", style={
                "background": "linear-gradient(135deg, #2d5f4a, #1a3d2e)", "color": WHITE,
                "width": "36px", "height": "36px", "borderRadius": "9px",
                "display": "flex", "alignItems": "center", "justifyContent": "center",
                "fontWeight": "900", "fontSize": "1.1rem", "flexShrink": "0",
            }),
            html.Div([
                html.Div("LOOPLESS", style={
                    "color": WHITE, "fontWeight": "800",
                    "fontSize": "0.9rem", "letterSpacing": "0.06em",
                }),
                html.Div("RETURNS ANALYTICS", style={
                    "color": "rgba(255,255,255,0.45)",
                    "fontSize": "0.58rem", "letterSpacing": "0.12em",
                }),
            ]),
        ], style={"display": "flex", "alignItems": "center", "gap": "10px"}),

        html.Div([
            dbc.Nav(
                [
                    dbc.NavLink(label, href=href, active="exact", className="topnav-link")
                    for label, href in _NAV_LINKS
                ],
                pills=True,
                style={"display": "flex", "gap": "2px",
                       "background": "rgba(255,255,255,0.1)",
                       "borderRadius": "50px", "padding": "4px"},
            ),
        ], style={
            "position": "absolute", "left": "50%",
            "transform": "translateX(-50%)",
        }),

        html.A(
            html.Div([
                html.Span("🗄", style={"fontSize": "0.95rem"}),
                html.Span("Database", style={
                    "fontSize": "0.82rem", "fontWeight": "600",
                    "color": "rgba(255,255,255,0.85)",
                }),
                html.Span("●", style={
                    "fontSize": "0.55rem", "color": "#10b981",
                    "verticalAlign": "middle",
                }),
            ], style={
                "display": "flex", "alignItems": "center", "gap": "6px",
                "background": "rgba(255,255,255,0.1)",
                "borderRadius": "50px", "padding": "6px 14px",
                "cursor": "pointer", "minWidth": "120px",
                "transition": "background 0.2s ease",
            }),
            href="/data",
            style={"textDecoration": "none"},
        ),
    ], style={
        "display": "flex",
        "justifyContent": "space-between",
        "alignItems": "center",
        "padding": "0 36px",
        "height": "64px",
        "position": "relative",
    }),
    style={
        "background": "linear-gradient(135deg, #2d5f4a, #1a3d2e)",
        "position": "fixed", "top": 0, "left": 0, "right": 0,
        "zIndex": 1000,
        "boxShadow": "0 2px 20px rgba(0,0,0,0.35)",
    },
)
