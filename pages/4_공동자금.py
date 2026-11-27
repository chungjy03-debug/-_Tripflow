# 멤버를 추가하고 입금을 기록하며, 공동자금 입금 현황과 예상 잔액을 보여주는 페이지
import streamlit as st

import db
import ui
from core.budget import summarize_budget
from core.fund import fund_status

st.set_page_config(page_title="공동 여행자금", layout="wide")
ui.setup()
st.title("공동 여행자금")

trip = ui.pick_trip()
if trip is None:
    st.stop()

trip_id = trip["id"]
members = db.list_members(trip_id)
names = {m["id"]: m["name"] for m in members}

st.subheader("멤버")
with st.form("member_form", clear_on_submit=True):
    new_name = st.text_input("멤버 이름")
    if st.form_submit_button("멤버 추가") and new_name.strip():
        db.create_member({"trip_id": trip_id, "name": new_name.strip(), "savings": 0})
        st.rerun()

st.subheader("입금 기록")
with st.form("deposit_form", clear_on_submit=True):
    c1, c2, c3 = st.columns(3)
    who = c1.selectbox("입금자", list(names), format_func=names.get)
    amount = c2.number_input("입금액(원)", min_value=0, value=300_000, step=10_000)
    deposited_on = c3.date_input("입금일")
    if st.form_submit_button("입금 저장") and amount > 0:
        db.create_deposit({"trip_id": trip_id, "member_id": who, "amount": amount,
                           "date": deposited_on.isoformat()})
        st.rerun()

deposits = db.list_deposits(trip_id)
budget = summarize_budget(db.list_budget_items(trip_id), trip["people"])
status = fund_status(deposits, [{"krw_amount": budget["total"]}], goal=max(budget["total"], 1))

st.subheader("입금 현황")
st.progress(min(status["achievement_pct"] / 100, 1.0),
            text=f"{ui.fmt_krw(status['total'])} / {ui.fmt_krw(budget['total'])} "
                 f"({status['achievement_pct']}%)")
st.table([{"멤버": names[m["id"]], "입금액": ui.fmt_krw(status["per_member"].get(m["id"], 0))}
          for m in members])

c1, c2 = st.columns(2)
c1.metric("예정 지출", ui.fmt_krw(status["planned_total"]))
c2.metric("예상 잔액", ui.fmt_krw(status["balance"]))
if status["shortage"]:
    st.warning(f"공동자금이 {ui.fmt_krw(-status['balance'])} 부족합니다.")
