# 여행 정보를 입력받아 예상 여행비, 목표금액, 저축계획을 보여주고 저장하는 페이지
from datetime import timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

import db
import ui
from core.budget import (CATEGORIES, cumulative_savings, estimate_trip_cost,
                         get_unit_prices, known_cities, recalc_with_new_price, savings_plan)
from core.fx import to_local

st.set_page_config(page_title="여행 전 계획", layout="wide")
ui.setup()
st.title("여행 전 계획")

today = ui.today()
col1, col2 = st.columns(2)
destination = col1.text_input("여행지 (예: 파리)", value="홍콩").strip()
if not destination:
    st.error("여행지를 입력하세요.")
    st.stop()

known = destination in known_cities()
currencies = ui.currency_options()
default_currency = ui.DEFAULT_CURRENCY.get(destination, "USD")
currency = col2.selectbox("통화", currencies,
                          index=currencies.index(default_currency) if default_currency in currencies else 0)

style = col1.selectbox("스타일", ui.STYLES, index=1)
start = col2.date_input("출발일", value=today + timedelta(days=60))
end = col1.date_input("귀국일", value=today + timedelta(days=63))
people = col2.number_input("인원", min_value=1, value=3, step=1)
savings = col1.number_input("내 보유금액(원)", min_value=0, value=0, step=10_000)

nights = (end - start).days
if nights < 1:
    st.error("귀국일은 출발일보다 뒤여야 합니다.")
    st.stop()
days = nights + 1

if known:
    unit = get_unit_prices(destination, style)
    flight = st.number_input("항공권 1인 가격(원) - 바꾸면 즉시 재계산됩니다",
                             min_value=0, value=unit["항공"], step=10_000)
else:
    st.info(f"'{destination}'은(는) 단가 목록에 없습니다. 아래 단가를 직접 입력하세요. "
            "입력한 단가는 스타일과 관계없이 그대로 씁니다.")
    hints = {"항공": "1인", "숙박": "1박(방 1개)", "식비": "1인 1일", "교통": "1인 1일",
             "관광·체험": "여행 전체", "쇼핑": "여행 전체"}
    with st.expander("항목별 단가 직접 입력", expanded=True):
        unit = {c: st.number_input(f"{c} 단가 ({hints[c]}, 원)", min_value=0, value=0,
                                   step=1_000, key=f"unit_{c}")
                for c in CATEGORIES}
    flight = unit["항공"]

try:
    result = estimate_trip_cost(destination, style, people, nights, days,
                                overrides={"항공": flight}, unit_prices=unit)
    change = recalc_with_new_price(destination, style, people, nights, days, "항공",
                                   flight, savings, today, start, unit_prices=unit)
except ValueError as err:
    st.error(str(err))
    st.stop()

st.subheader("예상 여행비")
st.dataframe(
    pd.DataFrame([{"항목": c, "예상 금액": ui.fmt_krw(result["items"][c])} for c in CATEGORIES]),
    hide_index=True, width="stretch",
)
m1, m2, m3 = st.columns(3)
m1.metric("총 예상 여행비", ui.fmt_krw(result["total"]),
          delta=ui.fmt_signed(change["total_delta"]))
m2.metric("1인 목표금액", ui.fmt_krw(result["per_person"]),
          delta=ui.fmt_signed(change["per_person_delta"]))
m3.metric("1인 필요 저축액", ui.fmt_krw(change["new_plan"]["required"]))

plan = change["new_plan"]
st.subheader("저축계획")
s1, s2, s3 = st.columns(3)
s1.metric("월별 저축액", ui.fmt_krw(plan["monthly"]), delta=ui.fmt_signed(change["monthly_delta"]))
s2.metric("주별 저축액", ui.fmt_krw(plan["weekly"]), delta=ui.fmt_signed(change["weekly_delta"]))
s3.metric("출발까지", f"{plan['remaining_months']}개월 ({plan['remaining_weeks']}주)")

if plan["required"] > 0:
    try:
        cumulative = cumulative_savings(plan["required"], plan["remaining_weeks"])
    except ValueError as err:
        st.error(str(err))
    else:
        chart = px.bar(x=list(range(1, len(cumulative) + 1)), y=cumulative,
                       labels={"x": "주차", "y": "누적 저축액(원)"},
                       title="출발까지 누적 저축")
        st.plotly_chart(chart, width="stretch")
else:
    st.success("이미 목표금액을 모았습니다.")

rate_default = 0.0
try:
    rate_default = round(ui.current_rate(currency), 2)
except RuntimeError:
    st.caption("현재 환율을 가져오지 못했습니다. 예정 환율을 직접 입력하세요.")
rate = st.number_input(f"예정 환율 (1 {currency} = ? 원)",
                       min_value=0.0, value=rate_default, step=0.01, format="%.2f")

if st.button("이 계획으로 여행 저장", disabled=rate <= 0):
    trip_id = db.create_trip({
        "destination": destination,
        "currency": currency,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "people": people,
        "style": style,
        "planned_rate": rate,
        "local_budget": to_local(result["total"], rate),
    })
    db.create_member({"trip_id": trip_id, "name": "본인", "savings": savings})
    for category, amount in result["items"].items():
        db.create_budget_item({"trip_id": trip_id, "category": category, "amount": amount})
    st.success("저장했습니다. 사이드바에서 이 여행을 선택해 다른 페이지를 사용하세요.")
