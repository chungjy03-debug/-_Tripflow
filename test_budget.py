# core/budget.py의 여행비 추정, 저축계획, 단가 변경 재계산 함수를 검증하는 테스트
from datetime import date, timedelta

import pytest

from core.budget import estimate_trip_cost, recalc_with_new_price, savings_plan


def test_estimate_hongkong_normal_3people_3nights_4days():
    result = estimate_trip_cost("홍콩", "보통", people=3, nights=3, days=4)

    assert result["items"] == {
        "항공": 1_500_000,
        "숙박": 750_000,
        "식비": 300_000,
        "교통": 150_000,
        "관광·체험": 200_000,
        "쇼핑": 100_000,
    }
    assert result["total"] == 3_000_000
    assert result["per_person"] == 1_000_000


def test_savings_plan_4months_16weeks():
    today = date(2026, 1, 1)
    departure = today + timedelta(days=112)  # 16주 = 4개월 기준

    result = savings_plan(1_000_000, 400_000, today, departure)

    assert result["required"] == 600_000
    assert result["remaining_months"] == 4
    assert result["remaining_weeks"] == 16
    assert result["monthly"] == 150_000
    assert result["weekly"] == 37_500


def test_flight_price_drop_reduces_per_person_by_80000():
    today = date(2026, 1, 1)
    departure = today + timedelta(days=112)

    result = recalc_with_new_price(
        "홍콩", "보통", people=3, nights=3, days=4,
        item="항공", new_unit_price=420_000,
        savings=0, today=today, departure_date=departure,
    )

    assert result["old_per_person"] == 1_000_000
    assert result["new_per_person"] == 920_000
    assert result["per_person_delta"] == -80_000
    assert result["total_delta"] == -240_000


def test_estimate_rejects_unknown_destination():
    with pytest.raises(ValueError):
        estimate_trip_cost("없는도시", "보통", people=1, nights=1, days=2)


def test_savings_plan_rejects_past_departure():
    today = date(2026, 1, 1)
    with pytest.raises(ValueError):
        savings_plan(1_000_000, 0, today, today)
