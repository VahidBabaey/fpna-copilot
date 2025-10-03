# tests/test_metrics.py
import pandas as pd
from agent.tools.metrics import (
    revenue_vs_budget, gross_margin_pct_trend, opex_breakdown_by_category,
    ebitda_value, cash_runway_months
)

def _mk_period(s):  # helper
    return pd.Period(s, freq="M")


def test_revenue_vs_budget_simple():
    # tiny synthetic data (already USD-projected like Milestone 1 output)
    actuals = pd.DataFrame({
        "month": [_mk_period("2025-06"), _mk_period("2025-06")],
        "entity": ["A","A"],
        "account_category": ["Revenue","COGS"],
        "amount_usd": [1000.0, 400.0],
    })
    budget  = pd.DataFrame({
        "month": [_mk_period("2025-06")],
        "entity": ["A"],
        "account_category": ["Revenue"],
        "amount_usd": [900.0],
    })

    r = revenue_vs_budget(actuals, budget, _mk_period("2025-06"))
    assert r["revenue_actual_usd"] == 1000.0
    assert r["revenue_budget_usd"] == 900.0
    assert r["variance_usd"] == 100.0
    assert abs(r["variance_pct"] - (100.0/900.0)) < 1e-9

def test_gm_trend_and_ebitda():
    m1, m2 = _mk_period("2025-05"), _mk_period("2025-06")
    actuals = pd.DataFrame({
        "month": [m1, m1, m1, m2, m2, m2],
        "entity": ["A"]*6,
        "account_category": ["Revenue","COGS","Opex:Sales"]*2,
        "amount_usd": [1000, 400, 200, 800, 300, 250],
    })
    gm = gross_margin_pct_trend(actuals, [m1,m2])
    # m1 GM% = (1000-400)/1000 = 0.6
    assert abs(gm.loc[gm["month"]==m1, "gm_pct"].iloc[0] - 0.6) < 1e-9
    # EBITDA m2 = 800-300-250 = 250
    assert ebitda_value(actuals, m2) == 250

def test_opex_breakdown_and_runway():
    m1, m2, m3, m4 = map(_mk_period, ["2025-03","2025-04","2025-05","2025-06"])
    actuals = pd.DataFrame({
        "month": [m4, m4, m4, m3, m3, m2, m1, m1, m1],
        "entity": ["A"]*9,
        "account_category": ["Opex:Marketing","Opex:Sales","Revenue","Revenue","COGS","Revenue","Revenue","COGS","Opex:R&D"],
        "amount_usd": [100, 150, 1000, 900, 500, 800, 700, 750, 50],
    })
    cash = pd.DataFrame({
        "month": [m4],
        "cash_usd": [2000.0],
    })
    ob = opex_breakdown_by_category(actuals, m4)
    assert set(ob.index) == {"Marketing", "Sales"}

    # burns: use last 3 complete months before m4 => m1,m2,m3
    # m3 pnl = 900-500 = +400 => burn 0
    # m2 pnl = 800 => burn 0
    # m1 pnl = 700-750-50 = -100 => burn 100
    # avg_burn = 100/3 = 33.33... -> runway ~ 60 months
    ans = cash_runway_months(actuals, cash, asof=m4, burn_lookback=3)
    assert ans["months_used"] == [m1,m2,m3]
    assert round(ans["runway_months"], 1) == round(2000/(100/3), 1)
