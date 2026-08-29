"""KPI targets, RAG (red/amber/green) status logic, and the Edit Targets modal."""
import dash_bootstrap_components as dbc
from dash import html

from config import (
    BORDER, LOW, TEXT, TEXT_2, TEXT_MUTED,
)


# Each KPI definition: label shown to the user, default target value,
# unit, direction (lower or higher is better) and the business goal.
KPI_SPECS = {
    "return_rate": {
        "label": "Return Rate",
        "default_target": 25.0,
        "unit": "%",
        "direction": "lower",
        "goal": "Keep returns below the UK fashion average (~30%)",
    },
    "kept_rate": {
        "label": "Kept Rate",
        "default_target": 75.0,
        "unit": "%",
        "direction": "higher",
        "goal": "Retain the majority of sold items after purchase",
    },
    "avg_rating": {
        "label": "Avg Customer Rating",
        "default_target": 4.0,
        "unit": " ★",
        "direction": "higher",
        "goal": "Maintain a 4-star quality signal across the catalogue",
    },
    "records": {
        "label": "Data Coverage",
        "default_target": 10000.0,
        "unit": "",
        "direction": "higher",
        "goal": "Ensure enough records for reliable trend analysis",
    },
}

DEFAULT_KPI_TARGETS = {k: v["default_target"] for k, v in KPI_SPECS.items()}


# RAG status: green if the target is met, amber if within 20%, red otherwise.
def rag_status(current, target, direction):
    """Return (label, bg, text_color, border) for RAG traffic-light status.

    Green  = meets target.
    Amber  = within 20% of target.
    Red    = misses target by more than 20%.
    """
    try:
        c = float(current)
        t = float(target)
    except (TypeError, ValueError):
        return "—", "#f3f4f6", "#6b7280", "#9ca3af"

    if t == 0:
        return "—", "#f3f4f6", "#6b7280", "#9ca3af"

    if direction == "lower":
        if c <= t:
            return "On Target", "#dcfce7", "#166534", "#22c55e"
        if c <= t * 1.2:
            return "At Risk",   "#fef3c7", "#92400e", "#f59e0b"
        return "Off Target",    "#fee2e2", "#991b1b", "#ef4444"
    else:
        if c >= t:
            return "On Target", "#dcfce7", "#166534", "#22c55e"
        if c >= t * 0.8:
            return "At Risk",   "#fef3c7", "#92400e", "#f59e0b"
        return "Off Target",    "#fee2e2", "#991b1b", "#ef4444"


def _fmt_value(value, unit):
    """Format a KPI value for display, picking sensible precision per unit."""
    if value is None:
        return "—"
    if unit == "%":
        return f"{round(float(value), 1)}%"
    if unit.strip() == "★":
        return f"{round(float(value), 1)}{unit}"
    return f"{int(round(float(value))):,}{unit}"


# Two-zone card: top half shows the live statistic, bottom half shows
# the matching KPI with its target and RAG colour.
def stat_kpi_card(stat_label, stat_value, kpi_key, current_kpi_value, target_value,
                  icon="📊", accent="#22C55E", icon_bg="#DCFCE7", icon_color=None,
                  trend=None, trend_label=""):
    """
    Card with two zones:
      • STATISTIC — the raw value the dashboard already shows
      • KPI       — a target-measured indicator with goal + RAG status
    """
    spec = KPI_SPECS[kpi_key]
    status_label, rag_bg, rag_text, rag_border = rag_status(
        current_kpi_value, target_value, spec["direction"]
    )
    comparator = "≤" if spec["direction"] == "lower" else "≥"

    badge_style = {
        "background": icon_bg,
        "width": "44px", "height": "44px", "borderRadius": "12px",
        "display": "flex", "alignItems": "center", "justifyContent": "center",
        "fontSize": "1.3rem", "flexShrink": "0",
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
        ], style={"fontSize": "0.72rem", "marginTop": "6px"})

    # Top zone — the statistic
    stat_zone = html.Div([
        html.Div([
            html.Div(icon, style=badge_style),
            html.Div([
                html.Div(str(stat_value), style={
                    "fontSize": "1.65rem", "fontWeight": "800",
                    "color": TEXT, "lineHeight": "1.1",
                }),
                html.Div(stat_label, style={
                    "fontSize": "0.8rem", "fontWeight": "600",
                    "color": TEXT_2, "marginTop": "3px",
                    "textTransform": "uppercase", "letterSpacing": "0.04em",
                }),
            ], style={"flex": "1", "minWidth": 0}),
        ], style={"display": "flex", "alignItems": "center", "gap": "14px"}),
        trend_el,
    ])

    # Bottom zone — the KPI
    target_str  = _fmt_value(target_value, spec["unit"])
    current_str = _fmt_value(current_kpi_value, spec["unit"])

    kpi_zone = html.Div([
        html.Div([
            html.Div("KPI", style={
                "fontSize": "0.62rem", "fontWeight": "700",
                "letterSpacing": "0.12em", "color": TEXT_MUTED,
                "textTransform": "uppercase",
            }),
            html.Div(status_label, style={
                "fontSize": "0.68rem", "fontWeight": "700",
                "padding": "2px 10px", "borderRadius": "999px",
                "background": rag_bg, "color": rag_text,
                "border": f"1px solid {rag_border}",
            }),
        ], style={
            "display": "flex", "justifyContent": "space-between",
            "alignItems": "center", "marginBottom": "6px",
        }),
        html.Div(f"{spec['label']} {comparator} {target_str}", style={
            "fontSize": "0.88rem", "fontWeight": "700", "color": TEXT,
            "marginBottom": "3px",
        }),
        html.Div(spec["goal"], style={
            "fontSize": "0.72rem", "color": TEXT_MUTED, "lineHeight": "1.3",
            "marginBottom": "6px",
        }),
        html.Div([
            html.Span("Current: ", style={"color": TEXT_MUTED}),
            html.Span(current_str, style={"color": rag_text, "fontWeight": "700"}),
            html.Span("  •  Target: ", style={"color": TEXT_MUTED}),
            html.Span(target_str, style={"color": TEXT, "fontWeight": "700"}),
        ], style={"fontSize": "0.72rem"}),
    ], style={
        "marginTop": "12px", "paddingTop": "12px",
        "borderTop": f"1px dashed {BORDER}",
    })

    return dbc.Card(
        dbc.CardBody([stat_zone, kpi_zone]),
        className="stat-card h-100",
        style={
            "borderTop": f"3px solid {accent}",
            "background": f"linear-gradient(160deg, #fffef2 60%, {accent}18 100%)",
        },
    )


# Modal that lets the user update each KPI target.
def _edit_targets_modal():
    """Modal that lets the user update each KPI target; persisted via dcc.Store."""
    rows = []
    for key, spec in KPI_SPECS.items():
        comparator = "≤" if spec["direction"] == "lower" else "≥"
        hint = f"{comparator} target · {spec['goal']}"
        rows.append(html.Div([
            dbc.Label([
                html.Span(spec["label"], style={"fontWeight": "700", "color": TEXT}),
                html.Span(f"  ({spec['unit'].strip() or 'count'})", style={
                    "fontSize": "0.75rem", "color": TEXT_MUTED, "marginLeft": "4px",
                }),
            ]),
            dbc.Input(
                id={"type": "kpi-target-input", "key": key},
                type="number", min=0, step=0.1,
                value=spec["default_target"],
                style={"borderRadius": "10px"},
            ),
            html.Div(hint, style={
                "fontSize": "0.72rem", "color": TEXT_MUTED,
                "marginTop": "4px", "marginBottom": "14px",
            }),
        ]))

    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Edit KPI Targets")),
        dbc.ModalBody([
            html.Div(
                "Update the target each KPI is measured against. "
                "Green = meets target, amber = within 20%, red = misses target.",
                style={
                    "fontSize": "0.82rem", "color": TEXT_MUTED,
                    "marginBottom": "16px",
                },
            ),
            html.Div(rows),
            html.Div(id="kpi-targets-feedback", style={
                "fontSize": "0.8rem", "color": LOW, "marginTop": "4px",
            }),
        ]),
        dbc.ModalFooter([
            dbc.Button("Reset Defaults", id="btn-reset-targets",
                       color="secondary", outline=True, size="sm",
                       style={"borderRadius": "50px", "fontWeight": "600"}),
            dbc.Button("Cancel", id="btn-cancel-targets",
                       color="secondary", outline=True, size="sm",
                       style={"borderRadius": "50px", "fontWeight": "600"}),
            dbc.Button("Save", id="btn-save-targets",
                       color="success", size="sm",
                       style={"borderRadius": "50px", "fontWeight": "600"}),
        ]),
    ], id="edit-targets-modal", is_open=False, centered=True)
