"""
Full-screen overlays mounted once at the root layout and toggled by callbacks.

_splash            Splash screen shown on first paint.
_ai_overlay        Loading overlay shown while Claude generates a recommendation.
_page_transition   Brief fade overlay shown during route changes.
"""
from dash import html


_splash = html.Div([
    html.Div([
        html.Div("L", className="splash-logo", style={
            "width": "90px", "height": "90px",
            "background": "linear-gradient(135deg, #3a7a5f, #1a3d2e)",
            "borderRadius": "22px",
            "display": "flex", "alignItems": "center", "justifyContent": "center",
            "fontSize": "2.8rem", "fontWeight": "900", "color": "#fffef2",
            "marginBottom": "28px",
            "boxShadow": "0 16px 48px rgba(0,0,0,0.4)",
        }),
        html.Div("LOOPLESS", className="splash-title", style={
            "color": "#fffef2", "fontSize": "2.4rem", "fontWeight": "800",
            "letterSpacing": "0.18em", "marginBottom": "8px",
            "fontFamily": "'Inter', sans-serif",
        }),
        html.Div("RETURNS ANALYTICS", className="splash-subtitle", style={
            "color": "rgba(255,255,255,0.4)", "fontSize": "0.72rem",
            "letterSpacing": "0.28em", "fontWeight": "600", "marginBottom": "56px",
            "fontFamily": "'Inter', sans-serif",
        }),
        html.Div(
            html.Div(className="splash-bar-fill", style={
                "height": "100%", "borderRadius": "4px",
                "background": "linear-gradient(90deg, #10b981, #2d5f4a, #10b981)",
                "backgroundSize": "200% 100%", "width": "0%",
            }),
            className="splash-loader",
            style={
                "width": "220px", "height": "3px",
                "background": "rgba(255,255,255,0.12)",
                "borderRadius": "4px", "overflow": "hidden",
            },
        ),
    ], style={
        "display": "flex", "flexDirection": "column",
        "alignItems": "center", "justifyContent": "center",
    }),
], id="splash-screen", style={
    "position": "fixed", "top": 0, "left": 0, "right": 0, "bottom": 0,
    "background": "linear-gradient(135deg, #2d5f4a 0%, #1a3d2e 60%, #0f2418 100%)",
    "zIndex": 10000,
    "display": "flex", "alignItems": "center", "justifyContent": "center",
})


_ai_overlay = html.Div([
    html.Div([
        html.Div("L", style={
            "width": "80px", "height": "80px",
            "background": "linear-gradient(135deg, #3a7a5f, #1a3d2e)",
            "borderRadius": "20px",
            "display": "flex", "alignItems": "center", "justifyContent": "center",
            "fontSize": "2.4rem", "fontWeight": "900", "color": "#fffef2",
            "marginBottom": "28px",
            "boxShadow": "0 14px 44px rgba(0,0,0,0.45)",
            "animation": "splashBounceIn 0.6s cubic-bezier(0.34,1.56,0.64,1) both",
        }),
        html.Div("Generating AI Recommendation", style={
            "color": "#fffef2", "fontSize": "1.35rem", "fontWeight": "700",
            "letterSpacing": "0.01em", "marginBottom": "8px",
            "fontFamily": "'Inter', sans-serif",
            "animation": "splashTextIn 0.5s ease 0.25s both",
        }),
        html.Div("Claude is analysing this product…", style={
            "color": "rgba(255,255,255,0.45)", "fontSize": "0.82rem",
            "letterSpacing": "0.04em", "marginBottom": "44px",
            "fontFamily": "'Inter', sans-serif",
            "animation": "splashTextIn 0.5s ease 0.4s both",
        }),
        html.Div(
            html.Div(className="splash-bar-fill", style={
                "height": "100%", "borderRadius": "4px",
                "background": "linear-gradient(90deg, #10b981, #2d5f4a, #10b981)",
                "backgroundSize": "200% 100%", "width": "0%",
            }),
            className="splash-loader",
            style={
                "width": "220px", "height": "3px",
                "background": "rgba(255,255,255,0.12)",
                "borderRadius": "4px", "overflow": "hidden",
                "animation": "splashTextIn 0.5s ease 0.5s both",
            },
        ),
    ], style={
        "display": "flex", "flexDirection": "column",
        "alignItems": "center", "justifyContent": "center",
    }),
], id="ai-loading-overlay", style={"display": "none"})


_page_transition = html.Div([
    html.Div([
        html.Div("L", style={
            "width": "72px", "height": "72px",
            "background": "linear-gradient(135deg, #3a7a5f, #1a3d2e)",
            "borderRadius": "18px",
            "display": "flex", "alignItems": "center", "justifyContent": "center",
            "fontSize": "2.2rem", "fontWeight": "900", "color": "#fffef2",
            "marginBottom": "24px",
            "boxShadow": "0 12px 40px rgba(0,0,0,0.4)",
        }),
        html.Div("LOOPLESS", style={
            "color": "#fffef2", "fontSize": "1.9rem", "fontWeight": "800",
            "letterSpacing": "0.18em", "marginBottom": "6px",
            "fontFamily": "'Inter', sans-serif",
        }),
        html.Div("RETURNS ANALYTICS", style={
            "color": "rgba(255,255,255,0.35)", "fontSize": "0.65rem",
            "letterSpacing": "0.28em", "fontWeight": "600", "marginBottom": "44px",
            "fontFamily": "'Inter', sans-serif",
        }),
        html.Div(
            html.Div(id="nav-bar-fill", style={
                "height": "100%", "borderRadius": "4px", "width": "0%",
                "background": "linear-gradient(90deg, #10b981, #2d5f4a, #10b981)",
                "backgroundSize": "200% 100%",
            }),
            style={
                "width": "180px", "height": "3px",
                "background": "rgba(255,255,255,0.12)",
                "borderRadius": "4px", "overflow": "hidden",
            },
        ),
    ], style={
        "display": "flex", "flexDirection": "column",
        "alignItems": "center", "justifyContent": "center",
    }),
], id="page-transition-overlay", style={
    "display": "none",
    "position": "fixed", "top": 0, "left": 0, "right": 0, "bottom": 0,
    "background": "linear-gradient(135deg, #2d5f4a 0%, #1a3d2e 60%, #0f2418 100%)",
    "zIndex": 9999,
    "alignItems": "center", "justifyContent": "center",
})
