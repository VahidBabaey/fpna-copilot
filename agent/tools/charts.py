# agent/tools/charts.py
from __future__ import annotations
import plotly.graph_objects as go
import pandas as pd

def bar_actual_vs_budget(month_label: str, actual: float, budget: float):
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Actual", x=[month_label], y=[actual]))
    fig.add_trace(go.Bar(name="Budget", x=[month_label], y=[budget]))
    fig.update_layout(barmode="group", title=f"Revenue vs Budget — {month_label}", height=380)
    return fig

def line_gm_trend(df: pd.DataFrame):
    # df: columns month (Period), gm_pct (float or None)
    x = [str(m) for m in df["month"].tolist()]
    y = [None if v is None else v*100 for v in df["gm_pct"].tolist()]
    fig = go.Figure(go.Scatter(x=x, y=y, mode="lines+markers"))
    fig.update_layout(title="Gross Margin % Trend", yaxis_title="GM %", height=380)
    return fig

def pie_opex_breakdown(series: pd.Series, month_label: str):
    fig = go.Figure(go.Pie(labels=series.index.tolist(), values=series.values.tolist(), hole=0.3))
    fig.update_layout(title=f"Opex Breakdown — {month_label}", height=380)
    return fig

def line_cash_trend(df: pd.DataFrame, title="Cash Trend"):
    fig = go.Figure(go.Scatter(x=df["month"].astype(str), y=df["cash_usd"], mode="lines+markers"))
    fig.update_layout(title=title, yaxis_title="USD", height=320)
    return fig
