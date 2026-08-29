"""Risk page (route "/risk") — layout + callbacks (ML training, scoring, AI modal)."""
import json

import pandas as pd
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State, ALL, ctx
import plotly.express as px
import plotly.graph_objects as go
import joblib as _joblib

from config import (
    BORDER, CARD, TEXT, TEXT_2, TEXT_MUTED, ACCENT_G, HIGH, MEDIUM, LOW, WHITE,
)
from components import (
    _page_header, _chart_card, _metric_badge, filter_row, get_filters,
    empty_fig, style_fig,
)
from bootstrap import MODEL_PATH as _MODEL_PATH, FE_PATH as _FE_PATH
from core.domain import PolicyScenario
from core.ai_service import generate_product_recommendation


# ── Layout ────────────────────────────────────────────────────────────────
def layout():
    return html.Div([
        _page_header("Products Likely to Be Returned", "See which products customers are most likely to send back"),
        html.Div([
            html.Div([
                html.Div([
                    dbc.Button("🔍 Analyse My Products", id="btn-train", color="success", size="lg", style={
                        "padding": "22px 80px",
                        "fontSize": "1.4rem",
                        "fontWeight": "800",
                        "borderRadius": "50px",
                        "background": "linear-gradient(135deg, #2d5f4a, #1a3d2e)",
                        "border": "none",
                        "boxShadow": "0 6px 32px rgba(29,61,46,0.5)",
                        "letterSpacing": "0.02em",
                        "minWidth": "360px",
                    }),
                ], id="risk-btn-inner", className="risk-btn-scale hero"),
                dbc.Spinner(
                    html.Span(id="train-msg", style={
                        "fontSize": "0.9rem", "color": "rgba(255,255,255,0.7)",
                        "fontWeight": "500",
                    }),
                    size="sm", color="light",
                ),
            ], id="risk-btn-wrap", className="risk-btn-wrap hero"),

            html.Div([
                filter_row("-risk"),
                html.Div(id="ml-metrics-card", className="mb-3"),
                html.Div(_chart_card("chart-risk-bar", "Products Most Likely to Be Returned", "Top 15 products ranked by return likelihood"), className="mb-3"),
                html.Div(id="risk-table", className="mb-3"),
                html.Div(_chart_card("chart-feature-importance", "Main Factors Behind Returns",
                            "The factors that most influence whether a customer returns a product"), className="mb-3"),
            ], id="risk-cards-container", style={"display": "none"}),
        ], className="content-wrapper"),

        dcc.Store(id="risk-data-store"),
        dcc.Store(id="selected-risk-product"),

        dbc.Modal([
            dbc.ModalHeader(
                dbc.ModalTitle(html.Div(id="modal-product-title", style={
                    "fontFamily": "'Inter', sans-serif",
                    "fontWeight": "700",
                    "fontSize": "1.05rem",
                })),
                style={"background": "linear-gradient(135deg, #2d5f4a, #1a3d2e)", "color": WHITE},
                close_button=True,
            ),
            dbc.ModalBody([
                html.Div(id="modal-product-overview", className="mb-3"),

                dbc.Spinner(
                    html.Div(id="modal-ai-content"),
                    color="success",
                    type="border",
                    size="sm",
                ),

                html.Hr(style={"borderColor": BORDER, "margin": "20px 0"}),
                html.Div([
                    html.H6("What Would Happen?", style={
                        "fontWeight": "800", "color": "#1f2937", "marginBottom": "4px",
                        "fontFamily": "'Inter', sans-serif",
                    }),
                    html.P(
                        "Use the slider below to see how many returns you could prevent "
                        "by setting a maximum discount limit for this type of product.",
                        className="text-muted small mb-3",
                    ),
                    dbc.Row([
                        dbc.Col([
                            html.Label("Only allow returns when discount is below %", className="small fw-semibold mb-1"),
                            dcc.Slider(
                                id="modal-sim-md", min=0, max=100, step=5, value=50,
                                marks={0: "0%", 25: "25%", 50: "50%", 75: "75%", 100: "100%"},
                            ),
                        ], md=8),
                        dbc.Col([
                            dbc.Button(
                                "▶ See Results",
                                id="modal-btn-sim",
                                color="success",
                                size="sm",
                                className="w-100",
                                style={"marginTop": "24px"},
                            ),
                        ], md=4),
                    ], className="mb-3 align-items-center"),
                    html.Div(id="modal-sim-result"),
                ]),
            ], style={"backgroundColor": "#f9fafb"}),
            dbc.ModalFooter([
                dbc.Button("📄 Export as PDF", id="modal-export-pdf", color="success",
                           outline=True, size="sm",
                           style={"borderRadius": "50px", "fontWeight": "600"}),
                dbc.Button("Close", id="modal-close", color="secondary",
                           outline=True, size="sm", className="ms-2",
                           style={"borderRadius": "50px"}),
            ], style={"backgroundColor": "#f9fafb", "borderTop": f"1px solid {BORDER}"}),
        ], id="ai-modal", size="lg", is_open=False, scrollable=True),
    ])


# ── Callbacks ─────────────────────────────────────────────────────────────
_OVERLAY_SHOW = {
    "position": "fixed", "top": 0, "left": 0, "right": 0, "bottom": 0,
    "background": "linear-gradient(135deg, #2d5f4a 0%, #1a3d2e 60%, #0f2418 100%)",
    "zIndex": 9000,
    "display": "flex", "alignItems": "center", "justifyContent": "center",
}
_OVERLAY_HIDE = {"display": "none"}


def register_callbacks(app, ctrl, repo):
    # Clientside callbacks: button loading + reveal + PDF export
    app.clientside_callback(
        "window.dash_clientside.loopless.riskBtnLoading",
        Output("risk-btn-inner", "className", allow_duplicate=True),
        Output("btn-train",      "disabled",  allow_duplicate=True),
        Input("btn-train",       "n_clicks"),
        prevent_initial_call=True,
    )
    app.clientside_callback(
        "window.dash_clientside.loopless.riskBtnReveal",
        Output("risk-btn-wrap",        "className"),
        Output("risk-btn-inner",       "className", allow_duplicate=True),
        Output("risk-cards-container", "style"),
        Output("btn-train",            "disabled",  allow_duplicate=True),
        Input("train-msg",             "children"),
        prevent_initial_call=True,
    )
    app.clientside_callback(
        "window.dash_clientside.loopless.exportPdf",
        Output("modal-export-pdf", "n_clicks"),
        Input("modal-export-pdf",  "n_clicks"),
        prevent_initial_call=True,
    )

    # ── Train model + render metrics card ──────────────────────────────────
    @app.callback(
        Output("train-msg",        "children"),
        Output("ml-metrics-card",  "children"),
        Input("btn-train", "n_clicks"),
        prevent_initial_call=True,
    )
    def train_model(_):
        try:
            metrics = ctrl.risk_service.train_model(filters={})
            acc     = round(metrics.get("accuracy",  0) * 100, 1)
            prec    = round(metrics.get("precision", 0) * 100, 1)
            rec     = round(metrics.get("recall",    0) * 100, 1)
            f1      = round(metrics.get("f1",        0) * 100, 1)
            roc_auc = round(metrics.get("roc_auc",   0) * 100, 1)
            cm      = metrics.get("confusion_matrix", [[0, 0], [0, 0]])
            tn, fp  = cm[0][0], cm[0][1]
            fn, tp  = cm[1][0], cm[1][1]

            ctrl.risk_service.model.save(_MODEL_PATH)
            _joblib.dump(ctrl.risk_service.feature_engineer, _FE_PATH)

            # ── Five evaluation metrics (technical name + plain English subtitle) ──
            # Palette: Tailwind 100 backgrounds + 700 text — same tonal level
            # across all five for a harmonious, "data-viz-quality" look.
            metrics_grid = html.Div([
                _metric_badge("Accuracy",  f"{acc}%",     "#dcfce7", "#15803d", subtitle="Correct Predictions"),
                _metric_badge("Precision", f"{prec}%",    "#fef3c7", "#b45309", subtitle="Return Flag Accuracy"),
                _metric_badge("Recall",    f"{rec}%",     "#fee2e2", "#b91c1c", subtitle="Returns Caught"),
                _metric_badge("F1 Score",  f"{f1}%",      "#dbeafe", "#1d4ed8", subtitle="Overall Balance"),
                _metric_badge("ROC AUC",   f"{roc_auc}%", "#ede9fe", "#6d28d9", subtitle="Discrimination Power"),
            ], style={
                "display": "grid",
                "gridTemplateColumns": "repeat(5, 1fr)",
                "gap": "10px",
                "marginBottom": "24px",
            })

            # ── Confusion matrix cells (technical abbreviation + plain English) ──
            def _cm_cell(tech, plain, count, plain_desc, value_color, bg):
                return html.Div([
                    html.Div(tech, style={
                        "fontSize": "0.62rem", "color": TEXT_MUTED, "fontWeight": "700",
                        "letterSpacing": "0.06em", "textTransform": "uppercase",
                    }),
                    html.Div(plain, style={
                        "fontSize": "0.68rem", "color": TEXT_2, "fontWeight": "600",
                        "marginBottom": "4px",
                    }),
                    html.Div(str(count), style={
                        "fontSize": "1.3rem", "fontWeight": "800", "color": value_color,
                    }),
                    html.Div(plain_desc, style={
                        "fontSize": "0.6rem", "color": TEXT_MUTED, "fontStyle": "italic",
                    }),
                ], style={"background": bg, "borderRadius": "8px", "padding": "10px", "textAlign": "center"})

            confusion_grid = html.Div([
                _cm_cell("✓ TN — True Negative",  "Correctly Said Safe",
                         tn, "Predicted no return — and it wasn't returned",
                         "#15803d", "#dcfce7"),
                _cm_cell("⚠ FP — False Positive", "Wrongly Flagged as Return",
                         fp, "Predicted return — but it wasn't returned",
                         "#b91c1c", "#fee2e2"),
                _cm_cell("⚠ FN — False Negative", "Missed a Real Return",
                         fn, "Predicted safe — but the customer returned it",
                         "#b45309", "#fef3c7"),
                _cm_cell("✓ TP — True Positive",  "Correctly Spotted Return",
                         tp, "Predicted return — and it was returned",
                         "#15803d", "#dcfce7"),
            ], style={
                "display": "grid",
                "gridTemplateColumns": "1fr 1fr",
                "gap": "10px",
                "width": "100%",
            })

            metrics_card = dbc.Card(dbc.CardBody([
                html.H6("How Accurate Is the Analysis?", className="fw-bold mb-3",
                        style={"color": TEXT, "fontFamily": "'Inter', sans-serif"}),
                metrics_grid,
                html.P("Prediction Results Breakdown (Confusion Matrix)",
                       className="small fw-semibold mb-2 text-center",
                       style={"color": TEXT_MUTED}),
                confusion_grid,
            ]), className="border-0 shadow-sm", style={"backgroundColor": CARD})

            return (
                f"Analysis complete! "
                f"Accuracy {acc}%  ·  Precision {prec}%  ·  Recall {rec}%  ·  "
                f"F1 {f1}%  ·  ROC AUC {roc_auc}%"
            ), metrics_card

        except Exception as e:
            return f"Error: {e}", html.Div()

    # ── Score risk + render bar chart, cards, feature importance ───────────
    @app.callback(
        Output("chart-risk-bar",            "figure"),
        Output("risk-table",                "children"),
        Output("risk-data-store",           "data"),
        Output("chart-feature-importance",  "figure"),
        Input("btn-apply-risk",             "n_clicks"),
        Input("train-msg",        "children"),
        State("f-cat-risk",    "value"),
        State("f-brand-risk",  "value"),
        State("f-season-risk", "value"),
        State("f-from-risk",   "value"),
        State("f-to-risk",     "value"),
        prevent_initial_call=False,
    )
    def update_risk(_, trained, cat, brand, season, date_from, date_to):
        f = get_filters(cat, brand, season, date_from, date_to)
        ctrl.set_filters(f)

        if not ctrl.risk_service.model.is_trained:
            return (
                empty_fig("No analysis run yet"),
                dbc.Alert([
                    html.Strong("Analysis not run yet. "),
                    "Click the ",
                    html.Strong("🔍 Analyse My Products"),
                    " button above, wait for it to finish, then click ",
                    html.Strong("Apply"),
                    " to see which products are most likely to be returned.",
                ], color="warning", style={"borderRadius": "12px"}),
                None,
                empty_fig("Run the analysis first to see results"),
            )

        scored_df = ctrl.risk_service.score_risk(f)
        if scored_df.empty:
            return empty_fig("No risk data"), html.Div(), None, empty_fig("No risk data")

        agg_dict = {"risk_score": "mean"}
        for col in ["category", "brand", "season"]:
            if col in scored_df.columns:
                agg_dict[col] = "first"
        for col in ["current_price", "markdown_percentage", "customer_rating"]:
            if col in scored_df.columns:
                agg_dict[col] = "mean"

        product_details = (
            scored_df.groupby("product_id")
            .agg(agg_dict)
            .reset_index()
            .rename(columns={"risk_score": "avg_risk_score"})
            .sort_values("avg_risk_score", ascending=False)
            .head(20)
        )

        if "return_reason" in scored_df.columns and "is_returned" in scored_df.columns:
            returned = scored_df[scored_df["is_returned"] == 1].copy()
            if not returned.empty:
                returned["return_reason"] = returned["return_reason"].fillna("Not recorded")
                rc = (
                    returned.groupby(["product_id", "return_reason"])
                    .size().reset_index(name="cnt")
                    .sort_values("cnt", ascending=False)
                    .drop_duplicates("product_id")[["product_id", "return_reason"]]
                    .rename(columns={"return_reason": "top_return_reason"})
                )
                product_details = product_details.merge(rc, on="product_id", how="left")

        if "top_return_reason" not in product_details.columns:
            product_details["top_return_reason"] = "No returns yet"
        product_details["top_return_reason"] = product_details["top_return_reason"].fillna("No returns yet")

        if "avg_risk_score" in product_details.columns:
            product_details["avg_risk_score"] = product_details["avg_risk_score"].round(4)
        for col in ["current_price", "markdown_percentage", "customer_rating"]:
            if col in product_details.columns:
                product_details[col] = product_details[col].round(2)

        store_data = product_details.to_dict(orient="records")

        # Risk bar chart
        chart_df = product_details.head(15).copy()
        for col in ["brand", "category", "season"]:
            if col not in chart_df.columns:
                chart_df[col] = "Unknown"
        chart_df["_price_str"]  = chart_df["current_price"].apply(lambda x: f"£{x:.2f}" if pd.notna(x) else "N/A") if "current_price" in chart_df.columns else "N/A"
        chart_df["_md_str"]     = chart_df["markdown_percentage"].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A") if "markdown_percentage" in chart_df.columns else "N/A"
        chart_df["_rating_str"] = chart_df["customer_rating"].apply(lambda x: f"{x:.1f}/5" if pd.notna(x) else "N/A") if "customer_rating" in chart_df.columns else "N/A"

        fig = style_fig(px.bar(
            chart_df, x="product_id", y="avg_risk_score",
            color="avg_risk_score",
            color_continuous_scale=[[0, "#c2dfd0"], [1, "#1a3d2e"]],
            labels={"avg_risk_score": "Return Likelihood", "product_id": "Product"},
            text="avg_risk_score",
            custom_data=["brand", "category", "season", "_price_str", "_md_str", "_rating_str", "top_return_reason"],
        ))
        fig.update_traces(
            texttemplate="%{y:.1%}", textposition="outside",
            textfont=dict(size=10, color=TEXT_2, family="Inter"),
            cliponaxis=False,
            hovertemplate=(
                "<b>%{x}</b><br>"
                "<b>%{customdata[0]} — %{customdata[1]}</b><br><br>"
                "📅 Season: %{customdata[2]}<br>"
                "💷 Price: %{customdata[3]}<br>"
                "🏷 Discount: %{customdata[4]}<br>"
                "★ Rating: %{customdata[5]}<br>"
                "↩ Why returned: %{customdata[6]}<br>"
                "📊 Return likelihood: %{y:.1%}"
                "<extra></extra>"
            ),
        )
        fig.update_layout(
            coloraxis_showscale=False,
            yaxis=dict(
                range=[0, chart_df["avg_risk_score"].max() * 1.25],
                tickformat=".0%",
            ),
        )

        # Risk cards (with percentile-based labels)
        scores = product_details["avg_risk_score"]
        high_thresh   = scores.quantile(0.75)
        medium_thresh = scores.quantile(0.40)

        def _risk_color(score):
            if score >= high_thresh:   return HIGH,   "#fce7f3", "High"
            if score >= medium_thresh: return MEDIUM, "#fef3c7", "Medium"
            return LOW, "#dcfce7", "Low"

        cards = []
        for row in store_data:
            pid    = row.get("product_id", "?")
            score  = float(row.get("avg_risk_score", 0))
            clr, bg, label = _risk_color(score)
            cat    = row.get("category", "")
            brand  = row.get("brand",    "")
            season = row.get("season",   "")
            price  = row.get("current_price")
            md     = row.get("markdown_percentage")
            rating = row.get("customer_rating")
            reason = row.get("top_return_reason", "No returns yet")

            name_parts = [p for p in [brand, cat] if p]
            display_name = " — ".join(name_parts) if name_parts else pid

            meta_items = []
            if season: meta_items.append(html.Span(season, className="risk-card-tag"))

            def _stat(icon, label_text, value):
                return html.Div([
                    html.Span(f"{icon} ", style={"fontSize": "0.8rem"}),
                    html.Span(f"{label_text}: ", style={
                        "fontSize": "0.75rem", "color": TEXT_MUTED,
                        "fontWeight": "600", "textTransform": "uppercase",
                        "letterSpacing": "0.04em",
                    }),
                    html.Span(value, style={"fontSize": "0.8rem", "color": TEXT_2, "fontWeight": "500"}),
                ], style={"display": "flex", "alignItems": "center", "gap": "2px"})

            stat_items = []
            if price  is not None: stat_items.append(_stat("💷", "Price",    f"£{round(price, 2)}"))
            if md     is not None: stat_items.append(_stat("🏷",  "Discount", f"{round(md, 1)}%"))
            if rating is not None: stat_items.append(_stat("★",  "Rating",   f"{round(rating, 1)}/5"))
            stat_items.append(_stat("↩", "Why returned", reason))

            cards.append(
                html.Div([
                    html.Div([
                        html.Div(f"{round(score * 100, 1)}%", style={
                            "fontSize": "1.3rem", "fontWeight": "800",
                            "color": clr, "lineHeight": "1",
                        }),
                        html.Div("risk", style={
                            "fontSize": "0.65rem", "color": TEXT_MUTED,
                            "textTransform": "uppercase", "letterSpacing": "0.08em",
                        }),
                    ], style={
                        "background": bg, "borderRadius": "12px",
                        "padding": "10px 14px", "textAlign": "center",
                        "minWidth": "70px", "flexShrink": "0",
                        "border": f"1.5px solid {clr}22",
                    }),
                    html.Div([
                        html.Div([
                            html.Span(display_name, style={
                                "fontWeight": "700", "fontSize": "0.95rem", "color": TEXT,
                            }),
                            html.Span(f" · {pid}", style={
                                "fontSize": "0.78rem", "color": TEXT_MUTED, "marginLeft": "6px",
                            }),
                            dbc.Badge(
                                label,
                                color="danger" if label == "High" else ("warning" if label == "Medium" else "success"),
                                className="ms-2",
                            ),
                        ], style={"marginBottom": "6px", "display": "flex", "alignItems": "center", "flexWrap": "wrap", "gap": "2px"}),
                        html.Div(meta_items, style={
                            "display": "flex", "flexWrap": "wrap", "gap": "6px", "marginBottom": "8px",
                        }) if meta_items else None,
                        html.Div(stat_items, style={
                            "display": "flex", "flexWrap": "wrap", "gap": "14px",
                        }),
                    ], style={"flex": "1", "minWidth": "0"}),
                    html.Button(
                        "💡 Get AI Recommendation",
                        id={"type": "rec-btn", "index": pid},
                        n_clicks=0,
                        className="rec-btn",
                    ),
                ], className="risk-product-card"),
            )

        # Feature importance
        try:
            model_obj  = ctrl.risk_service.model.model_object
            feat_names = ctrl.risk_service.feature_engineer.get_feature_names()
            coefs      = model_obj.coef_[0]
            fi_df = pd.DataFrame({"feature": feat_names, "coefficient": coefs})
            fi_df["abs"] = fi_df["coefficient"].abs()
            fi_df = fi_df.nlargest(15, "abs").sort_values("coefficient")
            prefix_map = {
                "category_": "Category: ", "brand_": "Brand: ",
                "season_": "Season: ", "size_": "Size: ", "color_": "Color: ",
            }
            def _clean(name):
                for prefix, label in prefix_map.items():
                    if name.startswith(prefix):
                        return label + name[len(prefix):]
                return name.replace("_", " ").title()
            fi_df["feature"] = fi_df["feature"].apply(_clean)
            bar_colors = ["#ec4899" if c > 0 else "#10b981" for c in fi_df["coefficient"]]
            fig_fi = style_fig(go.Figure(go.Bar(
                x=fi_df["coefficient"],
                y=fi_df["feature"],
                orientation="h",
                marker_color=bar_colors,
                text=fi_df["coefficient"].round(2),
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>Coefficient: %{x:.3f}<extra></extra>",
            )))
            fig_fi.update_layout(
                xaxis=dict(title="Impact on return likelihood  (pink = more returns · green = fewer returns)", zeroline=True,
                           zerolinecolor=BORDER, zerolinewidth=1),
                yaxis=dict(autorange=True),
                margin=dict(t=10, b=40, l=10, r=70),
            )
        except Exception:
            fig_fi = empty_fig("Feature importance unavailable")

        return fig, html.Div(cards, style={"display": "flex", "flexDirection": "column", "gap": "16px"}), store_data, fig_fi

    # ── AI Modal: open ──────────────────────────────────────────────────────
    @app.callback(
        Output("selected-risk-product", "data"),
        Output("ai-loading-overlay",    "style"),
        Input({"type": "rec-btn", "index": ALL}, "n_clicks"),
        State("risk-data-store", "data"),
        prevent_initial_call=True,
    )
    def open_recommendation_modal(btn_clicks, risk_data):
        triggered = ctx.triggered_id
        if not triggered or not isinstance(triggered, dict):
            return dash.no_update, dash.no_update
        if not any(btn_clicks):
            return dash.no_update, dash.no_update

        product_id = triggered.get("index")
        if not risk_data or product_id is None:
            return dash.no_update, dash.no_update

        product = next(
            (p for p in risk_data if str(p.get("product_id", "")) == str(product_id)),
            None,
        )
        if not product:
            return dash.no_update, dash.no_update

        return product, _OVERLAY_SHOW

    # ── AI Modal: generate Claude content ──────────────────────────────────
    @app.callback(
        Output("modal-product-title",    "children"),
        Output("modal-product-overview", "children"),
        Output("modal-ai-content",       "children"),
        Output("ai-modal",               "is_open",  allow_duplicate=True),
        Output("ai-loading-overlay",     "style",    allow_duplicate=True),
        Input("selected-risk-product",   "data"),
        prevent_initial_call=True,
    )
    def generate_recommendation_content(product):
        if not product:
            return "AI Recommendation", html.Div(), html.Div(), False, _OVERLAY_HIDE

        pid   = product.get("product_id", "Unknown")
        score = float(product.get("avg_risk_score", 0))
        risk_pct = round(score * 100, 1)
        badge_color = "danger" if score >= 0.7 else ("warning" if score >= 0.4 else "success")
        overview = html.Div([
            dbc.Badge(f"Risk: {risk_pct}%", color=badge_color, className="me-2", style={"fontSize": "0.8rem"}),
            dbc.Badge(product.get("category", "—"), color="secondary",  className="me-2", style={"fontSize": "0.8rem"}),
            dbc.Badge(product.get("brand",    "—"), color="info",       className="me-2", style={"fontSize": "0.8rem"}),
            dbc.Badge(product.get("season",   "—"), color="primary",    className="me-2", style={"fontSize": "0.8rem"}),
        ], className="mb-3")

        stats        = ctrl.statistics_service.get_statistics({})
        overall_rate = stats.get("overall_return_rate", 0)
        rec_text     = generate_product_recommendation(product, overall_rate)

        try:
            rec = json.loads(rec_text)
        except Exception:
            rec = {"summary": rec_text, "recommendations": [], "priority_action": "", "risk_level": "High"}

        blocks = []
        if rec.get("summary"):
            blocks.append(dbc.Alert(rec["summary"], color="info", className="mb-3",
                                    style={"fontSize": "0.9rem"}))
        if rec.get("priority_action"):
            blocks.append(dbc.Alert([
                html.Strong("Priority Action: "),
                rec["priority_action"],
            ], color="warning", className="mb-3", style={"fontSize": "0.875rem"}))
        for i, r in enumerate(rec.get("recommendations", []), 1):
            blocks.append(
                dbc.Card(
                    dbc.CardBody([
                        html.Div([
                            html.Span(f"{i}. ", style={"color": ACCENT_G, "fontWeight": "800", "marginRight": "4px"}),
                            html.Span(r.get("title", f"Recommendation {i}"), style={"fontWeight": "700", "color": TEXT}),
                        ], style={"marginBottom": "6px"}),
                        html.P(r.get("action", ""), className="mb-1",
                               style={"fontSize": "0.875rem", "color": TEXT_2}),
                        html.Small(
                            f"Expected impact: {r.get('expected_impact', '')}",
                            style={"color": TEXT_MUTED},
                        ),
                    ]),
                    className="mb-2",
                    style={
                        "borderLeft": f"3px solid {ACCENT_G}",
                        "background": CARD,
                        "borderRadius": "8px",
                    },
                )
            )
        if not blocks:
            blocks.append(dbc.Alert("No recommendations generated.", color="secondary"))

        title = f"💡 Tips to Reduce Returns — {pid}"
        return title, overview, html.Div(blocks), True, _OVERLAY_HIDE

    # ── AI Modal: scoped impact simulation ─────────────────────────────────
    @app.callback(
        Output("modal-sim-result",     "children"),
        Input("modal-btn-sim",         "n_clicks"),
        State("selected-risk-product", "data"),
        State("modal-sim-md",          "value"),
        prevent_initial_call=True,
    )
    def run_modal_simulation(_, product, md_threshold):
        if not product:
            return html.Div()

        scenario = PolicyScenario(
            scenario_id="MODAL_SIM",
            name=f"Impact for {product.get('product_id', 'product')}",
            markdown_threshold=float(md_threshold or 50),
            excluded_categories=[],
            excluded_brands=[],
            excluded_seasons=[],
        )
        sim_filters = {}
        if product.get("category"):
            sim_filters["category"] = product["category"]

        result    = ctrl.simulation_service.run_scenario(scenario, sim_filters)
        baseline  = round(result.baseline_return_rate  * 100, 1)
        simulated = round(result.simulated_return_rate * 100, 1)
        delta     = round(simulated - baseline, 1)
        is_improvement = delta <= 0
        arrow    = "↓" if is_improvement else "↑"
        d_color  = "#10b981" if is_improvement else "#ec4899"

        return dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.Div("📊", style={"fontSize": "1.4rem"}),
                html.P("Current Return Rate",  className="text-muted small mb-0", style={"fontWeight": "600"}),
                html.H5(f"{baseline}%",  style={"fontWeight": "800", "color": TEXT}),
            ]), className="text-center border-0 h-100",
                style={"background": CARD, "borderRadius": "10px", "boxShadow": "0 1px 8px rgba(0,0,0,0.06)"}),
            md=4),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.Div("🔁", style={"fontSize": "1.4rem"}),
                html.P("If Policy Applied", className="text-muted small mb-0", style={"fontWeight": "600"}),
                html.H5(f"{simulated}%", style={"fontWeight": "800", "color": TEXT}),
            ]), className="text-center border-0 h-100",
                style={"background": CARD, "borderRadius": "10px", "boxShadow": "0 1px 8px rgba(0,0,0,0.06)"}),
            md=4),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.Div("📉" if is_improvement else "📈", style={"fontSize": "1.4rem"}),
                html.P("Difference",    className="text-muted small mb-0", style={"fontWeight": "600"}),
                html.H5(f"{arrow} {abs(delta)}%", style={"fontWeight": "800", "color": d_color}),
                html.Small(f"{result.affected_return_count} returns could be prevented", className="text-muted"),
            ]), className="text-center border-0 h-100",
                style={"background": CARD, "borderRadius": "10px", "boxShadow": "0 1px 8px rgba(0,0,0,0.06)"}),
            md=4),
        ], className="g-2 mt-1")

    # ── AI Modal: close ────────────────────────────────────────────────────
    @app.callback(
        Output("ai-modal", "is_open", allow_duplicate=True),
        Input("modal-close", "n_clicks"),
        prevent_initial_call=True,
    )
    def close_modal(_):
        return False
