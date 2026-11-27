# 예상과 실제 지출을 비교하는 그래프, 카테고리별 도넛 그래프, 항목별 차이 표를 보여주는 페이지
import pandas as pd
import plotly.express as px
import streamlit as st

import db
import ui
from core.forecast import compare_by_category

st.set_page_config(page_title="리포트", layout="wide")
ui.setup()
st.title("리포트")

trip = ui.pick_trip()
if trip is None:
    st.stop()

trip_id = trip["id"]
rows = compare_by_category(db.list_budget_items(trip_id), db.list_expenses(trip_id))
if not rows:
    st.info("예산 항목이나 지출이 아직 없습니다.")
    st.stop()

df = pd.DataFrame(rows)
expected_total = int(df["expected"].sum())
actual_total = int(df["actual"].sum())
m1, m2, m3 = st.columns(3)
m1.metric("예상 여행비", ui.fmt_krw(expected_total))
m2.metric("실제 지출", ui.fmt_krw(actual_total))
m3.metric("차이(실제 − 예상)", ui.fmt_signed(actual_total - expected_total))

long = df.melt(id_vars="category", value_vars=["expected", "actual"],
               var_name="구분", value_name="금액")
long["구분"] = long["구분"].map({"expected": "예상", "actual": "실제"})
st.plotly_chart(px.bar(long, x="category", y="금액", color="구분", barmode="group",
                       labels={"category": "카테고리", "금액": "금액(원)"},
                       title="예상 vs 실제"), width="stretch")

spent = df[df["actual"] > 0]
if not spent.empty:
    st.plotly_chart(px.pie(spent, names="category", values="actual", hole=0.4,
                           title="카테고리별 실제 지출"), width="stretch")

st.subheader("항목별 차이")
st.dataframe(pd.DataFrame([{
    "카테고리": r["category"],
    "예상": ui.fmt_krw(r["expected"]),
    "실제": ui.fmt_krw(r["actual"]),
    "차이": ui.fmt_signed(r["diff"]),
} for r in rows]), hide_index=True, width="stretch")
