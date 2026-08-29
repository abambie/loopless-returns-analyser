"""Dashboard page (route "/") — layout + callbacks."""
import io
import csv
from datetime import datetime

import pandas as pd
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State, ALL, ctx
import plotly.express as px

from config import (
    BG, BG_DARK, CARD, TEXT, TEXT_2, TEXT_MUTED, ACCENT_G, BORDER,
    HIGH, MEDIUM, LOW, TEAL, CSV_PATH,
)
from components import (
    _page_header, _chart_card, _skeleton_stat, _edit_targets_modal,
    filter_row, get_filters, empty_fig, style_fig, stat_kpi_card,
    KPI_SPECS, DEFAULT_KPI_TARGETS, rag_status,
)


# ── Layout ────────────────────────────────────────────────────────────────
def layout():
    return html.Div([
        html.Div([
            _page_header("Returns Overview", "Monitor key metrics and trends in your product returns"),
            html.Div(
                dbc.Button("⬇ Export CSV", id="btn-export", color="success", outline=True, size="sm",
                           style={"borderRadius": "50px", "fontWeight": "600", "whiteSpace": "nowrap"}),
                style={"position": "absolute", "top": "28px", "right": "36px"},
            ),
        ], style={"position": "relative"}),
        dcc.Download(id="download-csv"),
        dcc.Store(id="kpi-targets-store", storage_type="local", data=DEFAULT_KPI_TARGETS),
        _edit_targets_modal(),
        html.Div([
            filter_row(),
            html.Div([
                html.Div([
                    html.Div("Statistics & KPIs", style={
                        "color": "#fffef2",
                        "fontSize": "1.6rem",
                        "fontWeight": "800",
                        "letterSpacing": "-0.01em",
                        "fontFamily": "'Inter', sans-serif",
                        "lineHeight": "1.15",
                    }),
                    html.Div("Targets measured against goals", style={
                        "color": "rgba(255,255,255,0.55)",
                        "fontSize": "0.88rem",
                        "fontWeight": "500",
                        "marginTop": "4px",
                    }),
                ]),
                dbc.Button("⚙ Edit Targets", id="btn-edit-targets",
                           size="sm", outline=True, color="light",
                           style={
                               "borderRadius": "50px", "fontWeight": "600",
                               "fontSize": "0.78rem", "whiteSpace": "nowrap",
                               "position": "absolute", "right": "0", "top": "50%",
                               "transform": "translateY(-50%)",
                           }),
            ], style={
                "position": "relative",
                "textAlign": "center",
                "marginTop": "18px",
                "marginBottom": "18px",
            }),
            dbc.Row(
                [_skeleton_stat(), _skeleton_stat(), _skeleton_stat(), _skeleton_stat()],
                id="stat-row", className="g-3 mb-4",
            ),
            html.Div([
                html.Div("View", style={
                    "fontFamily": "'Inter', sans-serif",
                    "fontSize": "1.4rem",
                    "fontWeight": "800",
                    "letterSpacing": "-0.02em",
                    "color": "#fffef2",
                    "textAlign": "center",
                    "marginBottom": "10px",
                }),
                html.Div([
                    html.Button("Trend",     id="tab-btn-trend",     className="dash-tab-btn", n_clicks=0),
                    html.Button("Breakdown", id="tab-btn-breakdown", className="dash-tab-btn", n_clicks=0),
                    html.Button("Deep Dive", id="tab-btn-deepdive",  className="dash-tab-btn", n_clicks=0),
                ], className="dash-tab-strip"),
            ], style={
                "display": "flex", "flexDirection": "column", "alignItems": "center",
                "marginBottom": "20px",
                "position": "sticky", "top": "64px", "zIndex": "50",
                "paddingTop": "14px", "paddingBottom": "14px",
                "backdropFilter": "blur(12px)",
                "WebkitBackdropFilter": "blur(12px)",
                "background": "transparent",
            }),
            html.Div(
                dbc.Row([
                    dbc.Col(_chart_card("chart-trend", "Returns Trend", "Monthly return rate percentage", "Last 12 Months"), md=12),
                ], className="g-3 mb-3"),
                id="tab-panel-trend",    style={},
            ),
            html.Div(
                html.Div([
                    dbc.Row([
                        dbc.Col(_chart_card("chart-cat",    "Category Breakdown", "Return rate by product category", "This Month"), md=6),
                        dbc.Col(_chart_card("chart-season", "Seasonal Trends",    "Return rate by season"),                         md=6),
                    ], className="g-3 mb-3"),
                    dbc.Row([
                        dbc.Col(_chart_card("chart-brand",  "Brand Breakdown",    "Return rate by brand — top 15"),                 md=6),
                        dbc.Col(_chart_card("chart-size",   "Size Breakdown",     "Return rate by size"),                           md=6),
                    ], className="g-3 mb-3"),
                ]),
                id="tab-panel-breakdown", style={},
            ),
            html.Div(
                dbc.Row([
                    dbc.Col(_chart_card("chart-duration", "Avg Days Held Before Return", "By category — returned items only"), md=7),
                    dbc.Col(_chart_card("chart-reasons",  "Return Reasons",               "Breakdown by reason"),              md=5),
                ], className="g-3 mb-3"),
                id="tab-panel-deepdive",  style={},
            ),
        ], className="content-wrapper"),
    ])


# ── Callbacks ─────────────────────────────────────────────────────────────
_TAB_ON  = {"background": "linear-gradient(135deg, #2d5f4a, #1a3d2e)", "color": "#fffef2", "fontWeight": "700", "boxShadow": "0 2px 10px rgba(26,61,46,0.35)", "opacity": "1"}
_TAB_OFF = {"background": "transparent",                                "color": "#9ca3af", "fontWeight": "500", "boxShadow": "none",                            "opacity": "0.55"}


def register_callbacks(app, ctrl, repo):

    # ── Tab toggle ──────────────────────────────────────────────────────────
    @app.callback(
        Output("tab-btn-trend",     "style"),
        Output("tab-btn-breakdown", "style"),
        Output("tab-btn-deepdive",  "style"),
        Input("tab-btn-trend",      "n_clicks"),
        Input("tab-btn-breakdown",  "n_clicks"),
        Input("tab-btn-deepdive",   "n_clicks"),
        prevent_initial_call=True,
    )
    def toggle_tabs(_t, _b, _d):
        tid = ctx.triggered_id
        return (
            _TAB_ON  if tid == "tab-btn-trend"     else _TAB_OFF,
            _TAB_ON  if tid == "tab-btn-breakdown" else _TAB_OFF,
            _TAB_ON  if tid == "tab-btn-deepdive"  else _TAB_OFF,
        )

    # ── KPI targets modal ──────────────────────────────────────────────────
    @app.callback(
        Output("edit-targets-modal", "is_open"),
        Output("kpi-targets-store",  "data"),
        Output({"type": "kpi-target-input", "key": ALL}, "value"),
        Output("kpi-targets-feedback", "children"),
        Input("btn-edit-targets",   "n_clicks"),
        Input("btn-save-targets",   "n_clicks"),
        Input("btn-cancel-targets", "n_clicks"),
        Input("btn-reset-targets",  "n_clicks"),
        State("edit-targets-modal", "is_open"),
        State("kpi-targets-store",  "data"),
        State({"type": "kpi-target-input", "key": ALL}, "value"),
        State({"type": "kpi-target-input", "key": ALL}, "id"),
        prevent_initial_call=True,
    )
    def toggle_targets_modal(_open, _save, _cancel, _reset, is_open, store, values, ids):
        trigger = ctx.triggered_id
        store = {**DEFAULT_KPI_TARGETS, **(store or {})}
        order = [i["key"] for i in ids] if ids else list(DEFAULT_KPI_TARGETS.keys())

        if trigger == "btn-edit-targets":
            return True, store, [store[k] for k in order], ""

        if trigger == "btn-save-targets":
            new_store = dict(store)
            for key, val in zip(order, values or []):
                try:
                    if val is None or val == "":
                        continue
                    num = float(val)
                    if num < 0:
                        continue
                    new_store[key] = num
                except (TypeError, ValueError):
                    continue
            return False, new_store, [new_store[k] for k in order], "Saved."

        if trigger == "btn-reset-targets":
            return True, DEFAULT_KPI_TARGETS, [DEFAULT_KPI_TARGETS[k] for k in order], "Reset to defaults."

        if trigger == "btn-cancel-targets":
            return False, store, [store[k] for k in order], ""

        return is_open, store, [store[k] for k in order], ""

    # ── Main dashboard callback (charts + stat cards) ──────────────────────
    @app.callback(
        Output("stat-row",        "children"),
        Output("chart-trend",     "figure"),
        Output("chart-reasons",   "figure"),
        Output("chart-cat",       "figure"),
        Output("chart-season",    "figure"),
        Output("chart-duration",  "figure"),
        Output("chart-brand",     "figure"),
        Output("chart-size",      "figure"),
        Input("btn-apply", "n_clicks"),
        Input("kpi-targets-store", "data"),
        State("f-cat",    "value"),
        State("f-brand",  "value"),
        State("f-season", "value"),
        State("f-from",   "value"),
        State("f-to",     "value"),
        prevent_initial_call=False,
    )
    def update_dashboard(_, targets, cat, brand, season, date_from, date_to):
        targets = {**DEFAULT_KPI_TARGETS, **(targets or {})}
        f = get_filters(cat, brand, season, date_from, date_to)
        ctrl.set_filters(f)
        data = ctrl.get_dashboard_data()
        stats = data["statistics"]
        rr   = round(stats.get("overall_return_rate", 0) * 100, 1)

        total     = stats.get("total_records", 0)
        returned  = stats.get("returned_records", 0)
        not_ret   = total - returned
        avg_price = round(stats.get("avg_current_price", 0) or 0, 2)

        reasons = data.get("return_reasons", [])
        top_reason = reasons[0]["return_reason"] if reasons else "N/A"

        kept_pct = round(not_ret / total * 100, 1) if total else 0
        avg_rating = round(stats.get("avg_customer_rating", 0) or 0, 1)

        df_all = repo.load_dataset(f)
        high_rated = int((df_all["customer_rating"] >= 4).sum()) if not df_all.empty and "customer_rating" in df_all.columns else 0
        n_cats = df_all["category"].nunique() if not df_all.empty and "category" in df_all.columns else 0

        cards = dbc.Row([
            dbc.Col(stat_kpi_card(
                "Return Rate", f"{rr}%",
                kpi_key="return_rate",
                current_kpi_value=rr,
                target_value=targets["return_rate"],
                icon="📉", accent=HIGH, icon_bg="#fce7f3", icon_color="#be185d",
                trend="down", trend_label=f"Top reason: {top_reason}",
            ), md=3),
            dbc.Col(stat_kpi_card(
                "Total Returns", f"{returned:,}",
                kpi_key="kept_rate",
                current_kpi_value=kept_pct,
                target_value=targets["kept_rate"],
                icon="↩", accent=MEDIUM, icon_bg="#fef3c7", icon_color="#d97706",
                trend="down", trend_label=f"{kept_pct}% of items kept",
            ), md=3),
            dbc.Col(stat_kpi_card(
                "Avg Rating", f"{avg_rating} ★",
                kpi_key="avg_rating",
                current_kpi_value=avg_rating,
                target_value=targets["avg_rating"],
                icon="★", accent=TEAL, icon_bg="#ccfbf1", icon_color="#0d9488",
                trend="up", trend_label=f"{high_rated:,} rated 4★ or above",
            ), md=3),
            dbc.Col(stat_kpi_card(
                "Total Records", f"{total:,}",
                kpi_key="records",
                current_kpi_value=total,
                target_value=targets["records"],
                icon="▤", accent=LOW, icon_bg="#dcfce7", icon_color="#059669",
                trend="up", trend_label=f"Avg price £{avg_price} · {n_cats} categories",
            ), md=3),
        ], className="g-3")

        # ── Trend ───────────────────────────────────────────────────────────
        trend_rows = data.get("return_trend", [])
        if trend_rows:
            trend_df = pd.DataFrame(trend_rows)
            trend_df["return_rate"] = (trend_df["return_rate"] * 100).round(1)
            fig_trend = style_fig(px.line(
                trend_df, x="bucket", y="return_rate",
                labels={"bucket": "Period", "return_rate": "Return Rate (%)"},
                color_discrete_sequence=[ACCENT_G],
                markers=True,
            ))
            fig_trend.update_traces(
                line=dict(width=2.5),
                marker=dict(size=7, color=ACCENT_G, line=dict(width=2, color=CARD)),
            )
            fig_trend.add_hline(
                y=30, line_dash="dot", line_color="#94a3b8", line_width=1.5,
                annotation_text="UK fashion avg ~30%",
                annotation_position="top right",
                annotation_font=dict(size=10, color="#94a3b8"),
            )
        else:
            fig_trend = empty_fig("No trend data available")

        # ── Reasons (pie) ───────────────────────────────────────────────────
        reasons = data.get("return_reasons", [])
        if reasons:
            fig_reasons = style_fig(px.pie(
                pd.DataFrame(reasons), names="return_reason", values="count",
                color_discrete_sequence=["#1a3d2e", "#2d7a5a", "#10b981", "#14b8a6", "#60a5fa", "#94a3b8"],
                hole=0.4,
            ))
            fig_reasons.update_traces(textfont=dict(color=CARD))
        else:
            fig_reasons = empty_fig("No return reasons found")

        # ── Category breakdown ──────────────────────────────────────────────
        by_cat = data.get("return_rate_by_category", [])
        if by_cat:
            df_cat = pd.DataFrame(by_cat)
            df_cat["return_rate"] = (df_cat["return_rate"] * 100).round(1)
            fig_cat = style_fig(px.bar(
                df_cat, x="return_rate", y="category",
                orientation="h",
                color="return_rate",
                color_continuous_scale=[[0, "#c2dfd0"], [1, "#1a3d2e"]],
                labels={"return_rate": "Return Rate (%)", "category": ""},
                text="return_rate",
            ))
            fig_cat.update_traces(
                texttemplate="%{x:.1f}%", textposition="outside",
                textfont=dict(size=11, color=TEXT_2, family="Inter"),
                cliponaxis=False,
            )
            fig_cat.update_layout(
                coloraxis_showscale=False,
                yaxis=dict(autorange="reversed"),
                xaxis=dict(range=[0, df_cat["return_rate"].max() * 1.25]),
                margin=dict(t=10, b=20, l=10, r=50),
            )
        else:
            fig_cat = empty_fig("No category data")

        # ── Season breakdown ────────────────────────────────────────────────
        season_rows = ctrl.statistics_service.get_return_rate_by_field("season", f)
        if season_rows:
            df_s = pd.DataFrame(season_rows)
            df_s["return_rate"] = (df_s["return_rate"] * 100).round(1)
            fig_season = style_fig(px.bar(
                df_s, x="season", y="return_rate",
                color="return_rate",
                color_continuous_scale=[[0, "#c2dfd0"], [1, "#1a3d2e"]],
                labels={"return_rate": "Return Rate (%)", "season": ""},
                text="return_rate",
            ))
            fig_season.update_traces(
                texttemplate="%{y:.1f}%", textposition="outside",
                textfont=dict(size=11, color=TEXT_2, family="Inter"),
                cliponaxis=False,
            )
            fig_season.update_layout(
                coloraxis_showscale=False,
                yaxis=dict(range=[0, df_s["return_rate"].max() * 1.25]),
            )
        else:
            fig_season = empty_fig("No season data")

        # ── Duration to return (CSV-based) ─────────────────────────────────
        try:
            df_csv = pd.read_csv(CSV_PATH)
            df_csv.columns = [c.strip().lower().replace(" ", "_") for c in df_csv.columns]
            if "return_date" in df_csv.columns and "purchase_date" in df_csv.columns:
                df_ret = df_csv[
                    df_csv["is_returned"].astype(str).str.strip().str.lower().isin(["1", "true", "yes"])
                ].copy()
                if cat    and cat    != "All": df_ret = df_ret[df_ret["category"] == cat]
                if brand  and brand  != "All": df_ret = df_ret[df_ret["brand"]    == brand]
                if season and season != "All": df_ret = df_ret[df_ret["season"]   == season]
                df_ret["purchase_date"] = pd.to_datetime(df_ret["purchase_date"], errors="coerce")
                df_ret["return_date"]   = pd.to_datetime(df_ret["return_date"],   errors="coerce")
                df_ret["days_held"]     = (df_ret["return_date"] - df_ret["purchase_date"]).dt.days
                df_ret = df_ret.dropna(subset=["days_held", "category"])
                if not df_ret.empty:
                    df_dur = (
                        df_ret.groupby("category")["days_held"]
                        .mean().round(1).reset_index()
                        .rename(columns={"days_held": "avg_days"})
                        .sort_values("avg_days", ascending=False)
                    )
                    fig_duration = style_fig(px.bar(
                        df_dur, x="category", y="avg_days",
                        color="avg_days",
                        color_continuous_scale=[[0, "#c2dfd0"], [1, "#1a3d2e"]],
                        labels={"avg_days": "Avg Days", "category": "Category"},
                        text="avg_days",
                    ))
                    fig_duration.update_traces(
                        texttemplate="%{y:.0f}d", textposition="outside",
                        textfont=dict(size=11, color=TEXT_2, family="Inter"),
                        cliponaxis=False,
                    )
                    fig_duration.update_layout(
                        coloraxis_showscale=False,
                        yaxis=dict(range=[0, df_dur["avg_days"].max() * 1.25]),
                    )
                else:
                    fig_duration = empty_fig("No returned items match current filters")
            else:
                fig_duration = empty_fig("return_date column not found in dataset")
        except Exception as e:
            fig_duration = empty_fig(f"Could not compute duration: {e}")

        # ── Brand breakdown ─────────────────────────────────────────────────
        brand_rows = ctrl.statistics_service.get_return_rate_by_field("brand", f)
        if brand_rows:
            df_brand = pd.DataFrame(brand_rows)
            df_brand["return_rate"] = (df_brand["return_rate"] * 100).round(1)
            df_brand = df_brand.sort_values("return_rate", ascending=False).head(15)
            fig_brand = style_fig(px.bar(
                df_brand, x="return_rate", y="brand",
                orientation="h",
                color="return_rate",
                color_continuous_scale=[[0, "#c2dfd0"], [1, "#1a3d2e"]],
                labels={"return_rate": "Return Rate (%)", "brand": ""},
                text="return_rate",
            ))
            fig_brand.update_traces(
                texttemplate="%{x:.1f}%", textposition="outside",
                textfont=dict(size=11, color=TEXT_2, family="Inter"),
                cliponaxis=False,
            )
            fig_brand.update_layout(
                coloraxis_showscale=False,
                yaxis=dict(autorange="reversed"),
                xaxis=dict(range=[0, df_brand["return_rate"].max() * 1.25]),
                margin=dict(t=10, b=20, l=10, r=50),
            )
        else:
            fig_brand = empty_fig("No brand data")

        # ── Size breakdown ──────────────────────────────────────────────────
        size_rows = ctrl.statistics_service.get_return_rate_by_field("size", f)
        if size_rows:
            df_size = pd.DataFrame(size_rows)
            df_size["return_rate"] = (df_size["return_rate"] * 100).round(1)
            df_size = df_size.sort_values("size")
            fig_size = style_fig(px.bar(
                df_size, x="size", y="return_rate",
                color="return_rate",
                color_continuous_scale=[[0, "#c2dfd0"], [1, "#1a3d2e"]],
                labels={"return_rate": "Return Rate (%)", "size": ""},
                text="return_rate",
            ))
            fig_size.update_traces(
                texttemplate="%{y:.1f}%", textposition="outside",
                textfont=dict(size=11, color=TEXT_2, family="Inter"),
                cliponaxis=False,
            )
            fig_size.update_layout(
                coloraxis_showscale=False,
                yaxis=dict(range=[0, df_size["return_rate"].max() * 1.25]),
            )
        else:
            fig_size = empty_fig("No size data")

        return cards, fig_trend, fig_reasons, fig_cat, fig_season, fig_duration, fig_brand, fig_size

    # ── CSV export ──────────────────────────────────────────────────────────
    # CSV is a plain-text format and cannot carry visual formatting (column
    # widths, fonts, colours, etc.). What we can do is produce the cleanest
    # possible CSV content with:
    #   • a UTF-8 BOM so Excel reads £ and other symbols correctly
    #   • Excel's "sep=," hint so locales that default to ; still parse it
    #   • clear visual section breaks made of dashes
    #   • fully quoted strings so commas inside text never break the layout
    @app.callback(
        Output("download-csv", "data"),
        Input("btn-export", "n_clicks"),
        State("kpi-targets-store", "data"),
        State("f-cat",    "value"),
        State("f-brand",  "value"),
        State("f-season", "value"),
        State("f-from",   "value"),
        State("f-to",     "value"),
        prevent_initial_call=True,
    )
    def export_csv(_, targets, cat, brand, season, date_from, date_to):
        targets = {**DEFAULT_KPI_TARGETS, **(targets or {})}
        f = get_filters(cat, brand, season, date_from, date_to)

        stats      = ctrl.statistics_service.get_statistics(f)
        rr         = round((stats.get("overall_return_rate") or 0) * 100, 1)
        total      = int(stats.get("total_records") or 0)
        returned   = int(stats.get("returned_records") or 0)
        not_ret    = total - returned
        kept_pct   = round(not_ret / total * 100, 1) if total else 0.0
        avg_rating = round(stats.get("avg_customer_rating") or 0, 1)
        avg_md     = round(stats.get("avg_markdown_percentage") or 0, 2)
        avg_price  = round(stats.get("avg_current_price") or 0, 2)

        buf = io.StringIO()
        buf.write("﻿")        # UTF-8 BOM so Excel handles £ and other symbols correctly
        buf.write("sep=,\n")        # Excel directive: forces "," as separator regardless of locale
        # csv.QUOTE_ALL puts quotes around every value — keeps text containing
        # commas, quotes, or newlines from breaking the column layout.
        w = csv.writer(buf, quoting=csv.QUOTE_ALL)

        # ── 1. Title + timestamp ───────────────────────────────────────────
        w.writerow(["LOOPLESS RETURNS ANALYTICS — DASHBOARD EXPORT"])
        w.writerow(["Generated", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        w.writerow([])

        # ── 2. Filters applied ─────────────────────────────────────────────
        w.writerow(["============================================================"])
        w.writerow(["FILTERS APPLIED"])
        w.writerow(["============================================================"])
        w.writerow(["Field", "Value"])
        w.writerow(["Category",  cat or "All"])
        w.writerow(["Brand",     brand or "All"])
        w.writerow(["Season",    season or "All"])
        w.writerow(["Date From", date_from or "(no start)"])
        w.writerow(["Date To",   date_to   or "(no end)"])
        w.writerow([])

        # ── 3. Headline statistics ─────────────────────────────────────────
        w.writerow(["============================================================"])
        w.writerow(["STATISTICS"])
        w.writerow(["============================================================"])
        w.writerow(["Metric", "Value"])
        w.writerow(["Return Rate (%)",          rr])
        w.writerow(["Kept Rate (%)",            kept_pct])
        w.writerow(["Total Returns",            returned])
        w.writerow(["Total Records",            total])
        w.writerow(["Avg Customer Rating",      avg_rating])
        w.writerow(["Avg Markdown %",           avg_md])
        w.writerow(["Avg Current Price (GBP)",  avg_price])
        w.writerow([])

        # ── 4. KPIs: current vs target + RAG status ────────────────────────
        w.writerow(["============================================================"])
        w.writerow(["KPIs — CURRENT vs TARGET"])
        w.writerow(["============================================================"])
        w.writerow(["KPI", "Direction", "Target", "Current", "Status", "Goal"])
        current_by_key = {
            "return_rate": rr,
            "kept_rate":   kept_pct,
            "avg_rating":  avg_rating,
            "records":     total,
        }
        for key, spec in KPI_SPECS.items():
            current = current_by_key.get(key)
            target  = targets.get(key, spec["default_target"])
            status, *_unused = rag_status(current, target, spec["direction"])
            direction = "Lower is better" if spec["direction"] == "lower" else "Higher is better"
            unit      = spec["unit"].strip() or "count"
            w.writerow([
                f"{spec['label']} ({unit})",
                direction, target, current, status, spec["goal"],
            ])
        w.writerow([])

        # ── 5. Return-rate breakdowns by dimension ─────────────────────────
        for field_name, label in [("category", "Category"), ("brand", "Brand"),
                                  ("season",   "Season"),   ("size",  "Size")]:
            rows = ctrl.statistics_service.get_return_rate_by_field(field_name, f)
            if not rows:
                continue
            w.writerow(["============================================================"])
            w.writerow([f"RETURN RATE BY {label.upper()}"])
            w.writerow(["============================================================"])
            w.writerow([label, "Return Rate (%)", "Record Count"])
            for r in rows:
                w.writerow([r[field_name], round(r["return_rate"] * 100, 1), r["records"]])
            w.writerow([])

        # ── 6. Return reasons ──────────────────────────────────────────────
        reasons = ctrl.statistics_service.get_return_reason_breakdown(f)
        if reasons:
            w.writerow(["============================================================"])
            w.writerow(["RETURN REASON BREAKDOWN"])
            w.writerow(["============================================================"])
            w.writerow(["Reason", "Count"])
            for r in reasons:
                w.writerow([r["return_reason"], r["count"]])
            w.writerow([])

        # ── 7. Monthly trend ───────────────────────────────────────────────
        trend = ctrl.statistics_service.get_return_trend_over_time("monthly", f)
        if trend:
            w.writerow(["============================================================"])
            w.writerow(["MONTHLY RETURN TREND"])
            w.writerow(["============================================================"])
            w.writerow(["Month", "Return Rate (%)", "Record Count"])
            for r in trend:
                w.writerow([r["bucket"], round(r["return_rate"] * 100, 1), r["records"]])
            w.writerow([])

        filename = f"loopless_summary_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        return dcc.send_string(buf.getvalue(), filename)
