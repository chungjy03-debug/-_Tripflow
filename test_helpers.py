# 화면에서 쓰는 예산 합계, 카테고리 비교, 현지 통화 환산, 누적 저축, 여행 진행률 함수를 검증하는 테스트
from datetime import date

from core.budget import (CATEGORIES, cumulative_savings, estimate_trip_cost,
                         get_unit_prices, known_cities, summarize_budget)
from core.forecast import compare_by_category, trip_progress
from core.fx import to_local


def test_summarize_budget_total_and_per_person_rounds_up():
    items = [{"amount": 1_500_000}, {"amount": 750_000}, {"amount": 100_000}]

    result = summarize_budget(items, people=3)

    assert result == {"total": 2_350_000, "per_person": 783_334}


def test_compare_by_category_diff_is_actual_minus_expected():
    budget_items = [{"category": "항공", "amount": 1_500_000},
                    {"category": "숙박", "amount": 750_000}]
    expenses = [{"category": "항공", "krw_amount": 1_400_000},
                {"category": "쇼핑", "krw_amount": 50_000}]

    rows = compare_by_category(budget_items, expenses)

    assert rows == [
        {"category": "항공", "expected": 1_500_000, "actual": 1_400_000, "diff": -100_000},
        {"category": "숙박", "expected": 750_000, "actual": 0, "diff": -750_000},
        {"category": "쇼핑", "expected": 0, "actual": 50_000, "diff": 50_000},
    ]


def test_to_local_converts_krw_to_local_currency():
    assert to_local(850_000, 170.0) == 5_000.0


def test_cumulative_savings_reaches_required_amount():
    assert cumulative_savings(600_000, 4) == [150_000, 300_000, 450_000, 600_000]


def test_get_unit_prices_returns_flight_price_for_hongkong_normal():
    assert get_unit_prices("홍콩", "보통")["항공"] == 500_000


def test_every_city_has_all_styles_and_categories():
    for city in known_cities():
        for style in ("알뜰", "보통", "여유"):
            prices = get_unit_prices(city, style)
            assert set(prices) == set(CATEGORIES), (city, style)


def test_estimate_with_directly_entered_unit_prices():
    unit = {"항공": 1_000_000, "숙박": 300_000, "식비": 50_000,
            "교통": 20_000, "관광·체험": 250_000, "쇼핑": 250_000}

    result = estimate_trip_cost("로마", "보통", people=2, nights=3, days=4, unit_prices=unit)

    assert result["items"]["항공"] == 2_000_000
    assert result["items"]["숙박"] == 900_000
    assert result["items"]["식비"] == 400_000
    assert result["total"] == 3_960_000
    assert result["per_person"] == 1_980_000


def test_trip_progress_clamps_before_start_and_after_end():
    start, end = date(2027, 1, 1), date(2027, 1, 4)

    assert trip_progress(start, end, date(2027, 1, 2)) == (2, 4)
    assert trip_progress(start, end, date(2026, 12, 20)) == (1, 4)
    assert trip_progress(start, end, date(2027, 2, 1)) == (4, 4)
