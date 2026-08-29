"""Plain statistic cards, shimmer skeletons, and metric badges."""
import dash_bootstrap_components as dbc
from dash import html

from config import TEXT_MUTED


def _metric_badge(label, value, bg, color, subtitle=None):
    """Small coloured metric badge used inside the ML metrics card.

    label    : the technical metric name (e.g. "Precision")
    value    : the metric value as a string (e.g. "85.3%")
    bg       : background colour of the badge
    color    : colour of the value text
    subtitle : optional plain-English explanation shown underneath the label
               (e.g. "Return Flag Accuracy"). Lets the same badge serve both
               technical and non-technical readers.
    """
    inner = [
        html.Div(value, style={
            "fontSize": "1.4rem",
            "fontWeight": "800",
            "color": color,
            "fontFamily": "'Inter', sans-serif",
        }),
        html.Div(label, style={
            "fontSize": "0.7rem",
            "fontWeight": "700",
            "color": TEXT_MUTED,
            "letterSpacing": "0.05em",
            "textTransform": "uppercase",
        }),
    ]
    if subtitle:
        inner.append(html.Div(subtitle, style={
            "fontSize": "0.62rem",
            "fontWeight": "500",
            "color": TEXT_MUTED,
            "marginTop": "2px",
            "fontStyle": "italic",
            "lineHeight": "1.2",
        }))
    return html.Div(inner, style={
        "background": bg,
        "borderRadius": "12px",
        "padding": "14px 12px",
        "textAlign": "center",
    })


def stat_card(label, value, icon="📊", accent="#22C55E", icon_bg="#DCFCE7", icon_color=None, trend=None, trend_label=""):
    """
    Simple statistic card (no KPI target). Used on the Simulation page.
    trend: "up" | "down" | None
    trend_label: e.g. "2.4% vs last month"
    """
    badge_style = {
        "background": icon_bg,
        "width": "52px", "height": "52px", "borderRadius": "14px",
        "display": "flex", "alignItems": "center", "justifyContent": "center",
        "fontSize": "1.5rem", "flexShrink": "0",
    }
    if icon_color:
        badge_style["color"] = icon_color

    trend_el = None
    if trend and trend_label:
        arrow   = "↗" if trend == "up" else "↘"
        t_color = "#10b981" if trend == "up" else "#ec4899"
        trend_el = html.Div([
            html.Span(f"{arrow} ", style={"color": t_color, "fontWeight": "700"}),
            html.Span(trend_label, style={"color": TEXT_MUTED}),
        ], style={"fontSize": "0.78rem", "marginTop": "10px"})

    return dbc.Card(
        dbc.CardBody([
            html.Div([
                html.Div(icon, style=badge_style),
                html.Div([
                    html.Div(str(value), className="stat-value"),
                    html.P(label, className="stat-label"),
                ], style={"flex": "1"}),
            ], style={"display": "flex", "alignItems": "flex-start", "gap": "16px"}),
            trend_el,
        ]),
        className="stat-card h-100",
        style={
            "borderTop": f"3px solid {accent}",
            "background": f"linear-gradient(160deg, #fffef2 60%, {accent}18 100%)",
        },
    )


def _skeleton_stat():
    """Shimmer placeholder shown while statistic data is loading."""
    skel = lambda w, h: html.Div(style={
        "height": h, "width": w, "borderRadius": "6px",
        "background": "linear-gradient(90deg, #e8e3d8 25%, #f2ede4 50%, #e8e3d8 75%)",
        "backgroundSize": "200% 100%",
        "animation": "skeletonShimmer 1.4s ease-in-out infinite",
    })
    return dbc.Col(
        dbc.Card(dbc.CardBody([
            skel("55%", "13px"),
            html.Div(style={"marginBottom": "10px"}),
            skel("40%", "32px"),
            html.Div(style={"marginBottom": "8px"}),
            skel("70%", "11px"),
        ]), className="stat-card border-0"),
        md=3,
    )
