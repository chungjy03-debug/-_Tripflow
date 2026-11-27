# core/forecast.py의 소비속도, 예상 최종 지출, 일회성 지출 제외 옵션을 검증하는 테스트
import pytest

from core.forecast import spending_pace


def _exp(amount, one_time=False):
    """지출 dict를 만든다."""
    return {"krw_amount": amount, "is_one_time": one_time}


def test_spending_pace_over_budget_case():
    expenses = [_exp(300_000), _exp(142_000)]

    result = spending_pace(expenses, elapsed_days=2, total_days=4, budget=850_000)

    assert result["spent"] == 442_000
    assert result["daily_avg"] == 221_000
    assert result["projected_total"] == 884_000
    assert result["over_budget"] == 34_000
    assert result["surplus"] == 0
    assert result["remaining_budget"] == 408_000
    assert result["remaining_days"] == 2
    assert result["daily_allowance"] <= 204_000
    assert result["daily_allowance"] == 204_000


def test_one_time_expense_excluded_from_daily_avg_but_added_to_projection():
    expenses = [_exp(200_000, one_time=True), _exp(242_000)]

    result = spending_pace(expenses, elapsed_days=2, total_days=4, budget=850_000)

    assert result["daily_avg"] == 121_000
    assert result["projected_total"] == 684_000
    assert result["surplus"] == 166_000
    assert result["over_budget"] == 0


def test_one_time_expense_included_in_daily_avg_when_option_off():
    expenses = [_exp(200_000, one_time=True), _exp(242_000)]

    result = spending_pace(expenses, elapsed_days=2, total_days=4, budget=850_000,
                           exclude_one_time=False)

    assert result["daily_avg"] == 221_000
    assert result["projected_total"] == 884_000


def test_last_day_has_zero_daily_allowance():
    result = spending_pace([_exp(100_000)], elapsed_days=4, total_days=4, budget=850_000)

    assert result["remaining_days"] == 0
    assert result["daily_allowance"] == 0


def test_rejects_zero_elapsed_days():
    with pytest.raises(ValueError):
        spending_pace([], elapsed_days=0, total_days=4, budget=850_000)
