# agent/answer_formatter.py
from __future__ import annotations
import pandas as pd
from agent.tools.finance_utils import fmt_money, fmt_pct

def fmt_month(m: pd.Period) -> str:
    return m.strftime("%b %Y")  # e.g., "Jun 2025"

def revenue_vs_budget_text(month, actual, budget, var, var_pct):
    m = fmt_month(month)
    vp = fmt_pct(var_pct)
    return (f"{m} revenue was {fmt_money(actual)} vs budget {fmt_money(budget)} "
            f"({fmt_money(var)}; {vp}).")

def gm_trend_text(df):
    # describe last point if available
    if df.empty:
        return "No data to compute Gross Margin trend."
    last = df.iloc[-1]
    m = last["month"]
    return f"Gross Margin trend shown; latest ({m}) is {fmt_pct(last['gm_pct'])}."

def opex_breakdown_text(month, series):
    m = fmt_month(month)
    total = series.sum() if len(series) else 0.0
    return f"Opex breakdown for {m} (total {fmt_money(total)})."

def cash_runway_text(asof, cash_current, avg_burn, runway):
    m = fmt_month(asof)
    if avg_burn in (None, 0) or runway is None:
        return (f"As of {m}, cash is {fmt_money(cash_current)}. "
                f"Average burn is zero → runway is not applicable.")
    return (f"As of {m}, cash is {fmt_money(cash_current)}. "
            f"Average burn is {fmt_money(avg_burn)}/mo → runway ≈ {runway:.1f} months.")
