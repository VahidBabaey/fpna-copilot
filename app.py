import streamlit as st
import pandas as pd

from agent.tools.data_loader import load_finance_data
from agent.planners import plan_and_answer
from agent.tools.pdf_export import build_board_pdf

st.set_page_config(page_title="FP&A Copilot", page_icon="💼", layout="wide")
st.title("FP&A Copilot")

@st.cache_data(show_spinner=False)
def _load():
    return load_finance_data("data/finance.xlsx")

data = _load()

# ---- Sidebar: Export PDF ----
st.sidebar.header("Export")
# build selectable month list from actuals
all_months = sorted(data["actuals_usd"]["month"].unique())
default_month = all_months[-1] if all_months else pd.Period("2025-01", freq="M")
month_strs = [str(m) for m in all_months]
sel = st.sidebar.selectbox("Month for PDF", options=month_strs, index=len(month_strs)-1 if month_strs else 0)
sel_month = pd.Period(sel, freq="M") if sel else default_month

if st.sidebar.button("Export PDF"):
    with st.spinner("Building PDF…"):
        pdf_bytes = build_board_pdf(data, sel_month)
    st.sidebar.download_button(
        label="Download Board PDF",
        data=pdf_bytes,
        file_name=f"fpna_board_{sel_month}.pdf",
        mime="application/pdf"
    )

# ---- Q&A box ----
q = st.text_input("Ask a question (e.g., 'What was June 2025 revenue vs budget?', 'Show Gross Margin % trend for the last 3 months', 'Break down Opex by category for June 2025', 'What is our cash runway right now?')")

if q:
    with st.spinner("Thinking..."):
        ans = plan_and_answer(q, data)
    st.write(ans["text"])
    if ans.get("figure") is not None:
        st.plotly_chart(ans["figure"], use_container_width=True)
