# 여행 중 지출을 입력해 원화로 저장하고, 소비속도와 예상 최종 지출을 보여주는 페이지
from datetime import date

import pandas as pd
import streamlit as st

import db
import ui
from core.budget import CATEGORIES, summarize_budget
from core.forecast import spending_pace, trip_progress
from core.fx import to_krw

st.set_page_config(page_title="여행 중 관리", layout="wide")
ui.setup()
st.title("여행 중 관리")

trip = ui.pick_trip()
if trip is None:
    st.stop()

trip_id = trip["id"]
members = db.list_members(trip_id)
names = {m["id"]: m["name"] for m in members}
today = ui.today()

try:
    rate = ui.current_rate(trip["currency"])
except RuntimeError:
    rate = trip["planned_rate"]
    st.caption(f"현재 환율을 가져오지 못해 예정 환율 {rate:,.2f}원을 씁니다.")

st.subheader("지출 입력")
with st.form("expense_form", clear_on_submit=True):
    c1, c2 = st.columns(2)
    category = c1.selectbox("카테고리", CATEGORIES)
    local_amount = c2.number_input(f"금액 ({trip['currency']})", min_value=0.0, step=1.0)
    spent_on = c1.date_input("날짜", value=today)
    scope = c2.radio("구분", ["공동", "개인"], horizontal=True)
    payer_ids = [None] + [m["id"] for m in members] if scope == "공동" else [m["id"] for m in members]
    paid_by = c1.selectbox("결제자", payer_ids,
                           format_func=lambda i: "공동자금" if i is None else names[i])
    owner = c2.selectbox("개인 지출 대상", [m["id"] for m in members],
                         format_func=names.get, disabled=scope == "공동")
    one_time = c1.checkbox("1회성 지출(예: 숙박비, 하루 평균에서 제외)")
    memo = c2.text_input("메모")
    submitted = st.form_submit_button("저장")

if submitted and local_amount > 0:
    db.create_expense({
        "trip_id": trip_id,
        "date": spent_on.isoformat(),
        "category": category,
        "local_amount": local_amount,
        "rate": rate,
        "krw_amount": to_krw(local_amount, rate),
        "paid_by": paid_by,
        "is_shared": int(scope == "공동"),
        "owner": None if scope == "공동" else owner,
        "is_one_time": int(one_time),
        "memo": memo,
    })
    st.success("저장했습니다.")
elif submitted:
    st.error("금액을 입력하세요.")

expenses = db.list_expenses(trip_id)
budget = summarize_budget(db.list_budget_items(trip_id), trip["people"])
start = date.fromisoformat(trip["start_date"])
elapsed, total_days = trip_progress(start, date.fromisoformat(trip["end_date"]), today)
pace = spending_pace(expenses, elapsed, total_days, budget["total"])

st.subheader("소비 현황")
m1, m2, m3 = st.columns(3)
m1.metric("지금까지 지출", ui.fmt_krw(pace["spent"]))
m2.metric("남은 예산", ui.fmt_krw(pace["remaining_budget"]))
m3.metric("하루 평균 지출", ui.fmt_krw(pace["daily_avg"]))
m4, m5 = st.columns(2)
m4.metric("예상 최종 지출", ui.fmt_krw(pace["projected_total"]))
m5.metric("남은 날 하루 사용 가능", ui.fmt_krw(pace["daily_allowance"]))

if pace["over_budget"] > 0:
    st.warning(f"예상 최종 지출이 예산보다 {ui.fmt_krw(pace['over_budget'])} 많을 것으로 보입니다.")

st.subheader("오늘 지출")
todays = [e for e in expenses if e["date"] == today.isoformat()]
if todays:
    st.dataframe(pd.DataFrame([{
        "카테고리": e["category"],
        "현지 금액": f"{e['local_amount']:,.2f} {trip['currency']}",
        "원화": ui.fmt_krw(e["krw_amount"]),
        "구분": "공동" if e["is_shared"] else "개인",
        "결제자": "공동자금" if e["paid_by"] is None else names.get(e["paid_by"], "-"),
        "메모": e["memo"] or "",
    } for e in todays]), hide_index=True, width="stretch")
else:
    st.caption("오늘 입력된 지출이 없습니다.")
