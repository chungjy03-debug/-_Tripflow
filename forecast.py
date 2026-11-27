# 여행 중 소비속도를 분석해 예상 최종 지출과 예산 초과 여부를 계산하는 순수 함수 모듈
import math


def _round_int(value):
    """금액을 정수로 반올림한다. 0.5는 올림한다."""
    return math.floor(value + 0.5)


def spending_pace(expenses, elapsed_days, total_days, budget, exclude_one_time=True):
    """지금까지의 지출로 소비속도, 예상 최종 지출, 예산 초과액 또는 여유액을 계산한다.

    expenses는 krw_amount와 is_one_time 키를 가진 지출 dict 목록이다.
    exclude_one_time이 True면 is_one_time 지출(예: 숙박비)은 하루 평균에서 빼고,
    예상 최종 지출에는 그대로 더한다. False면 모든 지출을 하루 평균에 넣는다.
    """
    if not 1 <= elapsed_days <= total_days:
        raise ValueError("경과 일수는 1일 이상, 전체 여행 일수 이하여야 합니다.")

    spent = sum(e["krw_amount"] for e in expenses)
    one_time = sum(e["krw_amount"] for e in expenses if e["is_one_time"])
    recurring = spent - one_time if exclude_one_time else spent

    daily_avg = _round_int(recurring / elapsed_days)
    one_time_extra = one_time if exclude_one_time else 0
    projected = _round_int(recurring / elapsed_days * total_days) + one_time_extra

    remaining_budget = budget - spent
    remaining_days = total_days - elapsed_days
    daily_allowance = max(remaining_budget, 0) // remaining_days if remaining_days > 0 else 0

    gap = projected - budget
    return {
        "spent": spent,
        "remaining_budget": remaining_budget,
        "daily_avg": daily_avg,
        "projected_total": projected,
        "over_budget": max(gap, 0),
        "surplus": max(-gap, 0),
        "remaining_days": remaining_days,
        "daily_allowance": daily_allowance,
    }


def compare_by_category(budget_items, expenses):
    """카테고리별 예상 금액과 실제 지출을 비교한다. 차이는 실제 − 예상이다.

    budget_items는 category, amount 키를, expenses는 category, krw_amount 키를 가진 dict 목록이다.
    예산 항목 순서를 먼저 두고, 예산에 없는 지출 카테고리는 뒤에 붙인다.
    """
    categories = []
    for row in list(budget_items) + list(expenses):
        if row["category"] not in categories:
            categories.append(row["category"])

    rows = []
    for category in categories:
        expected = sum(i["amount"] for i in budget_items if i["category"] == category)
        actual = sum(e["krw_amount"] for e in expenses if e["category"] == category)
        rows.append({"category": category, "expected": expected,
                     "actual": actual, "diff": actual - expected})
    return rows


def trip_progress(start, end, today):
    """여행 전체 일수와 오늘까지 경과한 일수를 돌려준다. 경과 일수는 1일과 전체 일수 사이로 맞춘다."""
    total = (end - start).days + 1
    elapsed = min(max((today - start).days + 1, 1), total)
    return elapsed, total
