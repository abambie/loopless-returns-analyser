"""
Chart helpers used by every page.

empty_fig(msg)   Placeholder figure for when a chart has no data.
style_fig(fig)   Apply the project's standard Plotly theme to a figure.
_chart_card(...) Card wrapper around a dcc.Graph with a styled header.
"""
import dash_bootstrap_components as dbc
from dash import dcc, html
import plotly.graph_objects as go

from config import BORDER, CARD, TEXT_2, TEXT_MUTED


def empty_fig(msg="No data available"):
    """Placeholder Plotly figure shown when a chart has no data."""
    fig = go.Figure()
    fig.update_layout(
        annotations=[dict(
            text=msg, x=0.5, y=0.5,
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=14, color=TEXT_MUTED, family="Inter"),
        )],
        paper_bgcolor=CARD, plot_bgcolor=CARD,
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        margin=dict(t=40, b=20, l=10, r=10),
    )
    return fig


def style_fig(fig):
    """Apply the project's standard Plotly theme (Inter + cream background)."""
    fig.update_layout(
        paper_bgcolor=CARD,
        plot_bgcolor=CARD,
        margin=dict(t=20, b=20, l=10, r=10),
        font=dict(family="Inter, sans-serif", size=12, color=TEXT_2),
        legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0, font=dict(size=11, color=TEXT_2)),
        xaxis=dict(
            gridcolor=BORDER, linecolor=BORDER,
            tickfont=dict(size=11, color=TEXT_MUTED),
            tickcolor=BORDER,
        ),
        yaxis=dict(
            gridcolor=BORDER, linecolor=BORDER,
            tickfont=dict(size=11, color=TEXT_MUTED),
            tickcolor=BORDER,
        ),
    )
    return fig


def _chart_card(graph_id, title, subtitle="", period=""):
    """A card wrapper around a dcc.Graph with a styled header."""
    header = html.Div([
        html.Div([
            html.Div(title, className="chart-title"),
            html.Div(subtitle, className="chart-subtitle") if subtitle else None,
        ]),
        html.Div(period, className="chart-period-pill") if period else None,
    ], className="chart-header")
    return dbc.Card(
        dbc.CardBody([
            header,
            dcc.Graph(id=graph_id, config={"displayModeBar": False},
                      style={"marginTop": "8px"}),
        ]),
        className="chart-card h-100",
    )
