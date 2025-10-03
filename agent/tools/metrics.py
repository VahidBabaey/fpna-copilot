# agent/tools/metrics.py
from __future__ import annotations
import pandas as pd
from typing import Literal, Tuple, Dict, Any, Optional
from .finance_utils import safe_pct

# ---------- helpers to aggregate P&L by account groups ----------

def _sum_revenue(df: pd.DataFrame, month: Optional[pd.Period] = None) -> float:
    q = df[df["account_category"] == "Revenue"]
    if month is not None:
        q = q[q["month"] == month]
    return float(q["amount_usd"].sum())

def _sum_cogs(df: pd.DataFrame, month: Optional[pd.Period] = None) -> float:
    q = df[df["account_category"] == "COGS"]
    if month is not None:
        q = q[q["month"] == month]
    return float(q["amount_usd"].sum())

def _sum_opex(df: pd.DataFrame, month: Optional[pd.Period] = None) -> float:
    q = df[df["account_category"].str.startswith("Opex:", na=False)]
    if month is not None:
        q = q[q["month"] == month]
    return float(q["amount_usd"].sum())

def _opex_breakdown(df: pd.DataFrame, month: pd.Period) -> pd.Series:
    q = df[
        (df["month"] == month) &
        (df["account_category"].str.startswith("Opex:", na=False))
    ].copy()
    # category = substring after "Opex:"
    q["category"] = q["account_category"].str.split(":", n=1).str[1].fillna("Other")
    s = q.groupby("category")["amount_usd"].sum().sort_values(ascending=False)
    return s

# ---------- metric APIs (called by planner/agent) ----------

def revenue_vs_budget(
    actuals_usd: pd.DataFrame,
    budget_usd: pd.DataFrame,
    month: pd.Period,
) -> Dict[str, Any]:
    """
    Returns revenue actual vs budget for a month in USD, plus variance.
    """
    actual = _sum_revenue(actuals_usd, month)
    budget = _sum_revenue(budget_usd, month)
    variance = actual - budget
    variance_pct = safe_pct(variance, budget)  # None if budget==0
    return {
        "month": month,
        "revenue_actual_usd": actual,
        "revenue_budget_usd": budget,
        "variance_usd": variance,
        "variance_pct": variance_pct,
    }

def gross_margin_pct_trend(
    actuals_usd: pd.DataFrame,
    months: list[pd.Period],
) -> pd.DataFrame:
    """
    For each month, GM% = (Revenue - COGS) / Revenue (None if revenue==0).
    Returns a DataFrame with columns: month, gm_pct
    """
    rows = []
    for m in months:
        rev = _sum_revenue(actuals_usd, m)
        cogs = _sum_cogs(actuals_usd, m)
        gm_pct = safe_pct(rev - cogs, rev)
        rows.append({"month": m, "gm_pct": gm_pct})
    return pd.DataFrame(rows)

def opex_breakdown_by_category(
    actuals_usd: pd.DataFrame,
    month: pd.Period,
) -> pd.Series:
    """
    Returns a Series: index=category, value=amount_usd for that month.
    """
    return _opex_breakdown(actuals_usd, month)

def ebitda_value(
    actuals_usd: pd.DataFrame,
    month: pd.Period,
) -> float:
    """
    EBITDA (proxy) = Revenue - COGS - Opex for a month (USD).
    """
    rev = _sum_revenue(actuals_usd, month)
    cogs = _sum_cogs(actuals_usd, month)
    opex = _sum_opex(actuals_usd, month)
    return rev - cogs - opex

def cash_runway_months(
    actuals_usd: pd.DataFrame,
    cash_usd: pd.DataFrame,
    asof: Optional[pd.Period] = None,
    burn_lookback: int = 3,
) -> Dict[str, Any]:
    """
    Cash runway = current cash / avg monthly net burn over last `burn_lookback` complete months.

    burn_i = max(0, -(Revenue_i - COGS_i - Opex_i))
             (i.e., if P&L is positive, burn is 0; else use absolute loss)
    """
    # determine "now"
    cash_usd = cash_usd.copy()
    if asof is None:
        asof = cash_usd["month"].max()

    # current cash at (or before) asof
    cur_row = cash_usd[cash_usd["month"] == asof]
    if cur_row.empty:
        # if no exact asof, fallback to latest prior month
        cur_row = cash_usd[cash_usd["month"] <= asof].sort_values("month").tail(1)
    if cur_row.empty:
        return {"asof": asof, "cash_current_usd": 0.0, "avg_burn_usd": None, "runway_months": None, "months_used": []}

    cash_current = float(cur_row.iloc[0]["cash_usd"])

    # last N complete months BEFORE asof
    months_all = sorted(actuals_usd["month"].unique())
    months_before = [m for m in months_all if m < asof]
    look = months_before[-burn_lookback:] if len(months_before) >= burn_lookback else months_before

    burns = []
    for m in look:
        pnl = _sum_revenue(actuals_usd, m) - _sum_cogs(actuals_usd, m) - _sum_opex(actuals_usd, m)
        burn = 0.0 if pnl >= 0 else (-pnl)
        burns.append(burn)

    avg_burn = None if len(burns) == 0 else (sum(burns) / len(burns))
    runway = None if (avg_burn is None or avg_burn == 0) else (cash_current / avg_burn)

    return {
        "asof": asof,
        "cash_current_usd": cash_current,
        "avg_burn_usd": avg_burn,
        "runway_months": runway,
        "months_used": look,
    }
