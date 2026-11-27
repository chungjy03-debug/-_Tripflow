# 공동/개인 지출을 분류해 보여주고, 멤버별 차액과 최종 송금 목록을 계산해 보여주는 페이지
import pandas as pd
import streamlit as st

import db
import ui
from core.settlement import calc_balances, settle

st.set_page_config(page_title="여행 후 정산", layout="wide")
ui.setup()
st.title("여행 후 정산")

trip = ui.pick_trip()
if trip is None:
    st.stop()

trip_id = trip["id"]
members = db.list_members(trip_id)
names = {m["id"]: m["name"] for m in members}
expenses = db.list_expenses(trip_id)
deposits = db.list_deposits(trip_id)

st.subheader("지출 분류 확인")
st.dataframe(pd.DataFrame([{
    "날짜": e["date"],
    "카테고리": e["category"],
    "원화": ui.fmt_krw(e["krw_amount"]),
    "분류": "공동" if e["is_shared"] else "개인",
    "결제자": "공동자금" if e["paid_by"] is None else names.get(e["paid_by"], "-"),
    "대상": "전체" if e["is_shared"] else names.get(e["owner"], "-"),
} for e in expenses]), hide_index=True, width="stretch")

st.subheader("멤버별 정산")
try:
    balances = calc_balances(members, deposits, expenses)
    transfers = settle({mid: r["balance"] for mid, r in balances.items()})
except ValueError as err:
    st.error(str(err))
    st.stop()

st.dataframe(pd.DataFrame([{
    "멤버": r["name"],
    "낸 돈": ui.fmt_krw(r["paid"]),
    "부담할 돈": ui.fmt_krw(r["owed"]),
    "차액": ui.fmt_signed(r["balance"]),
} for r in balances.values()]), hide_index=True, width="stretch")

st.subheader("최종 송금 목록")
if not transfers:
    st.success("정산할 금액이 없습니다.")
for payer, payee, amount in transfers:
    with st.container(border=True):
        st.markdown(f"**{names[payer]}** → **{names[payee]}**")
        st.markdown(f"### {ui.fmt_krw(amount)}")
