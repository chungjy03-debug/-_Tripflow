# 현재 환율을 보여주고, 환율을 바꿨을 때 추가 필요금액과 주별 저축액을 시뮬레이션하는 페이지
from datetime import date

import streamlit as st

import db
import ui
from core.budget import savings_plan, summarize_budget
from core.fx import simulate_rate_change

st.set_page_config(page_title="환율 시뮬레이션", layout="wide")
ui.setup()
st.title("환율 시뮬레이션")

trip = ui.pick_trip()
if trip is None:
    st.stop()

trip_id = trip["id"]
members = db.list_members(trip_id)
budget = summarize_budget(db.list_budget_items(trip_id), trip["people"])
planned_rate = trip["planned_rate"]
currency = trip["currency"]

try:
    plan = savings_plan(budget["per_person"], members[0]["savings"], ui.today(),
                        date.fromisoformat(trip["start_date"]))
except ValueError as err:
    st.error(str(err))
    st.stop()

try:
    st.metric(f"현재 환율 (1 {currency})", f"{ui.current_rate(currency):,.2f}원")
except RuntimeError:
    st.warning("현재 환율을 가져오지 못했습니다. 아래 시뮬레이션은 예정 환율 기준으로 계산합니다.")
st.caption(f"예정 환율 {planned_rate:,.2f}원 기준으로 저장된 예산입니다.")

new_rate = st.slider("새 환율 (원)", min_value=round(planned_rate * 0.7, 2),
                     max_value=round(planned_rate * 1.3, 2), value=planned_rate, step=0.1)

sim = simulate_rate_change(trip["local_budget"], planned_rate, new_rate,
                           saved=members[0]["savings"], goal=budget["per_person"],
                           weeks_left=plan["remaining_weeks"])

c1, c2, c3 = st.columns(3)
c1.metric("원화 지출", ui.fmt_krw(sim["after_krw"]), delta=ui.fmt_signed(sim["delta_krw"]))
c2.metric("추가 필요금액", ui.fmt_krw(sim["extra_needed"]))
c3.metric("새 목표금액(1인)", ui.fmt_krw(sim["new_goal"]))
c4, c5 = st.columns(2)
c4.metric("변경 전 주별 저축액", ui.fmt_krw(sim["old_weekly"]))
c5.metric("변경 후 주별 저축액", ui.fmt_krw(sim["new_weekly"]),
          delta=ui.fmt_signed(sim["new_weekly"] - sim["old_weekly"]))
