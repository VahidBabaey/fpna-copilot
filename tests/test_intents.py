# tests/test_intents.py
import pandas as pd
from agent.intent_router import route_intent

def test_route_intent_variants():
    r = route_intent("What was June 2025 revenue vs budget in USD?")
    assert r["intent"] == "revenue_vs_budget"
    assert str(r["month"]) in ("2025-06", "Jun 2025")

    r = route_intent("Show Gross Margin % trend for the last 3 months.")
    assert r["intent"] == "gross_margin_trend"
    assert r["last_n"] == 3

    r = route_intent("Break down Opex by category for 2023-09.")
    assert r["intent"] == "opex_breakdown"
    assert str(r["month"]) == "2023-09"

    r = route_intent("What is our cash runway right now?")
    assert r["intent"] == "cash_runway"
