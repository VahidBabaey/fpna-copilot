# agent/planners.py
from __future__ import annotations
from typing import Dict, Any, List
import pandas as pd

from agent.intent_router import route_intent
from agent.tools.metrics import (
    revenue_vs_budget, gross_margin_pct_trend, opex_breakdown_by_category,
    ebitda_value, cash_runway_months
)
from agent.tools.charts import (
    bar_actual_vs_budget, line_gm_trend, pie_opex_breakdown, line_cash_trend
)
from agent.answer_formatter import (
    revenue_vs_budget_text, gm_trend_text, opex_breakdown_text, cash_runway_text
)

def _most_recent_complete_month(df: pd.DataFrame) -> pd.Period:
    return df["month"].max()

def plan_and_answer(query: str, data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """
    Returns a dict with keys:
      - 'intent'
      - 'text'
      - 'figure' (plotly fig or None)
    """
    actuals = data["actuals_usd"]
    budget  = data["budget_usd"]
    cash    = data["cash_usd"]

    route = route_intent(query)
    intent = route.get("intent")

    if intent == "revenue_vs_budget":
        month = route.get("month") or _most_recent_complete_month(actuals)
        res = revenue_vs_budget(actuals, budget, month)
        text = revenue_vs_budget_text(month=res["month"],
                                      actual=res["revenue_actual_usd"],
                                      budget=res["revenue_budget_usd"],
                                      var=res["variance_usd"],
                                      var_pct=res["variance_pct"])
        fig  = bar_actual_vs_budget(month_label=str(month),
                                    actual=res["revenue_actual_usd"],
                                    budget=res["revenue_budget_usd"])
        return {"intent": intent, "text": text, "figure": fig}

    if intent == "gross_margin_trend":
        n = route.get("last_n") or 3
        all_months = sorted(actuals["month"].unique())
        months = all_months[-n:] if len(all_months) >= n else all_months
        df = gross_margin_pct_trend(actuals, months=list(months))
        text = gm_trend_text(df)
        fig = line_gm_trend(df)
        return {"intent": intent, "text": text, "figure": fig}

    if intent == "opex_breakdown":
        month = route.get("month") or _most_recent_complete_month(actuals)
        series = opex_breakdown_by_category(actuals, month)
        text = opex_breakdown_text(month, series)
        fig = pie_opex_breakdown(series, month_label=str(month))
        return {"intent": intent, "text": text, "figure": fig}

    if intent == "cash_runway":
        ans = cash_runway_months(actuals, cash)
        text = cash_runway_text(ans["asof"], ans["cash_current_usd"], ans["avg_burn_usd"], ans["runway_months"])
        # optional: small trend chart for last 6 months
        cash_tail = cash.sort_values("month").tail(12)
        fig = line_cash_trend(cash_tail, title="Cash (last 12 months)")
        return {"intent": intent, "text": text, "figure": fig}

    # Unknown intent
    return {
        "intent": None,
        "text": "Sorry—I couldn’t classify that. Try asking about: revenue vs budget (for a month), gross margin trend, opex breakdown (for a month), or cash runway.",
        "figure": None,
    }
