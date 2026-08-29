from __future__ import annotations  # enables modern type-hint syntax on Python 3.9
import json  # used to parse the JSON string returned by Claude and to build fallback error JSON
import os  # used to read the ANTHROPIC_API_KEY environment variable
from typing import Any, Dict  # type hint aliases used in the function signature

import anthropic  # the official Anthropic Python SDK — provides the client that calls the Claude API

_client: anthropic.Anthropic | None = None  # module-level singleton: the Anthropic client is created once and reused across all calls (avoids repeated initialisation overhead)


def _get_client() -> anthropic.Anthropic | None:  # lazy initialiser — creates the Anthropic client on first call and returns the cached instance on subsequent calls
    global _client  # reference the module-level singleton variable
    if _client is None:  # only create the client if it hasn't been created yet
        api_key = os.environ.get("ANTHROPIC_API_KEY")  # read the API key from the environment variable (set before running the app)
        if not api_key:
            return None
        _client = anthropic.Anthropic(api_key=api_key)
    return _client  # return the cached (or newly created) client


def generate_product_recommendation(product: Dict[str, Any], overall_return_rate: float) -> str:
    client = _get_client()

    if client is None:
        return json.dumps({
            "summary": "AI recommendations are optional and currently disabled.",
            "risk_level": "High",
            "priority_action": "Set ANTHROPIC_API_KEY to enable tailored recommendations.",
            "recommendations": [],
        })

    # Gather product context and format it for the prompt
    risk_pct = round(float(product.get("avg_risk_score", 0)) * 100, 1)
    overall_pct = round(float(overall_return_rate) * 100, 1)
    price = product.get("current_price")
    price_str = f"£{round(float(price), 2)}" if price is not None else "N/A"
    md_pct = product.get("markdown_percentage")
    md_str = f"{round(float(md_pct), 1)}%" if md_pct is not None else "N/A"
    rating = product.get("customer_rating")
    rating_str = f"{round(float(rating), 1)}/5" if rating is not None else "N/A"

    # Prompt pins a strict JSON schema: summary, risk_level, priority_action, recommendations[]
    prompt = f"""You are a retail returns analyst for a fashion boutique called Loopless.
Analyse the following high-risk product and provide actionable recommendations to reduce its return rate.

## Product Details
- Product ID:        {product.get("product_id", "Unknown")}
- Category:          {product.get("category", "Unknown")}
- Brand:             {product.get("brand", "Unknown")}
- Season:            {product.get("season", "Unknown")}
- Current Price:     {price_str}
- Markdown:          {md_str}
- Customer Rating:   {rating_str}
- ML Return Risk:    {risk_pct}%  (store average: {overall_pct}%)
- Top Return Reason: {product.get("top_return_reason", "Unknown")}

## Task
Provide 3 concise, specific, actionable recommendations to reduce the return rate for this product.
Consider: pricing strategy, sizing guidance, product description improvements, quality signalling,
or targeted promotions.

Respond ONLY with a JSON object in this exact format (no markdown, no extra text):
{{
  "summary": "One-sentence executive summary of the risk and key opportunity.",
  "risk_level": "High",
  "priority_action": "The single most impactful action to take immediately.",
  "recommendations": [
    {{
      "title": "Short title",
      "action": "Specific action the retailer should take.",
      "expected_impact": "Brief expected outcome."
    }}
  ]
}}"""

    # Call Claude and return the text block; fall back to structured error JSON on any failure
    try:
        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=1024,
            thinking={"type": "adaptive"},
            messages=[{"role": "user", "content": prompt}],
        )
        for block in message.content:
            if block.type == "text":
                return block.text.strip()
        return json.dumps({"summary": "No recommendation generated.", "recommendations": [], "priority_action": "", "risk_level": "High"})
    except anthropic.AuthenticationError:
        return json.dumps({
            "summary": "API key not configured. Set the ANTHROPIC_API_KEY environment variable to enable AI recommendations.",
            "risk_level": "High",
            "priority_action": "Set ANTHROPIC_API_KEY in your environment and restart the app.",
            "recommendations": [],
        })
    except Exception as exc:
        return json.dumps({
            "summary": f"Could not generate recommendation: {exc}",
            "risk_level": "High",
            "priority_action": "Check your API key and network connection.",
            "recommendations": [],
        })
