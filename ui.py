# 여러 페이지가 함께 쓰는 금액 표시, DB 준비, 여행 선택, 환율 조회, 기준일 헬퍼 모듈
import os
from datetime import date

import streamlit as st

import db
from core.fx import get_currencies, get_rate

# 단가 파일에 있는 도시의 기본 통화. 목록에 없는 도시는 USD를 기본으로 보여 준다.
DEFAULT_CURRENCY = {"홍콩": "HKD", "도쿄": "JPY", "방콕": "THB", "싱가포르": "SGD", "파리": "EUR", "뉴욕": "USD"}
STYLES = ("알뜰", "보통", "여유")


def fmt_krw(amount):
    """정수 금액을 '1,234,000원' 형식 문자열로 바꾼다."""
    return f"{int(amount):,}원"


def fmt_signed(amount):
    """증감 금액을 '+100,000원' 또는 '-50,000원' 형식 문자열로 바꾼다."""
    return f"{int(amount):+,}원"


def today():
    """기준일을 돌려준다. TRIPFLOW_TODAY(YYYY-MM-DD) 환경 변수가 있으면 그 날짜를 쓴다(발표용 기준일 고정)."""
    value = os.environ.get("TRIPFLOW_TODAY")
    return date.fromisoformat(value) if value else date.today()


def setup():
    """DB 테이블을 준비한다. 여러 번 호출해도 안전하다."""
    db.init_db()


@st.cache_data(ttl=3600)
def current_rate(currency):
    """Frankfurter에서 1시간 동안 캐시한 현재 환율을 돌려준다. 실패하면 RuntimeError를 낸다."""
    return get_rate(currency)


@st.cache_data(ttl=86400)
def currency_options():
    """Frankfurter가 지원하는 통화 목록을 하루 동안 캐시해서 돌려준다."""
    return get_currencies()


def pick_trip():
    """사이드바에서 저장된 여행을 고른다. 저장된 여행이 없으면 None을 돌려준다."""
    trips = db.list_trips()
    if not trips:
        st.info("저장된 여행이 없습니다. '1_여행전' 페이지에서 먼저 여행을 저장하세요.")
        return None
    labels = {t["id"]: f"{t['destination']} ({t['start_date']} ~ {t['end_date']})" for t in trips}
    trip_id = st.sidebar.selectbox("여행 선택", list(labels), format_func=labels.get, key="trip_id")
    return next(t for t in trips if t["id"] == trip_id)
