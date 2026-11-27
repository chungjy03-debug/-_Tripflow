# 항목별 예상 여행비와 목표금액을 계산하는 순수 함수 모듈
import json
import math
from pathlib import Path

PRICES_PATH = Path(__file__).resolve().parent.parent / "data" / "prices.json"

# 단가 단위: 항공=1인, 숙박=1박(방 전체), 식비·교통=1인 1일, 관광·체험·쇼핑=여행 전체
CATEGORIES = ("항공", "숙박", "식비", "교통", "관광·체험", "쇼핑")

# 달력 한 달을 평균 일수로 환산한 값
DAYS_PER_MONTH = 30.4375


def _load_prices(path=PRICES_PATH):
    """prices.json을 읽어 {도시: {스타일: {항목: 단가}}} 형태로 돌려준다."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _ceil_div(a, b):
    """정수 나눗셈을 올림해 금액이 목표에 모자라지 않도록 한다."""
    return -(-a // b)


def _category_total(category, unit_price, people, nights, days):
    """항목 하나의 단가와 인원·일수로 총액을 계산한다."""
    if category == "항공":
        return unit_price * people
    if category == "숙박":
        return unit_price * nights
    if category in ("식비", "교통"):
        return unit_price * people * days
    return unit_price


def known_cities(prices_path=PRICES_PATH):
    """단가 파일에 등록된 도시 이름 목록을 돌려준다."""
    return list(_load_prices(prices_path))


def estimate_trip_cost(destination, style, people, nights, days,
                       overrides=None, prices_path=PRICES_PATH, unit_prices=None):
    """도시·스타일별 단가로 항목별 예상 여행비와 총액, 1인 부담액을 계산한다.

    unit_prices를 주면 단가 파일 대신 그 단가를 쓴다(목록에 없는 도시용). style은 이때 쓰지 않는다.
    overrides에 {항목: 단가}를 넣으면 해당 항목의 단가만 바꿔서 계산한다.
    숙박은 방 1개 기준(방 전체 단가 × 박 수)으로 계산한다.
    """
    if people < 1:
        raise ValueError("인원은 1명 이상이어야 합니다.")
    if unit_prices is None:
        unit_prices = get_unit_prices(destination, style, prices_path)

    unit = dict(unit_prices)
    unit.update(overrides or {})
    missing = [c for c in CATEGORIES if c not in unit]
    if missing:
        raise ValueError(f"단가가 빠진 항목이 있습니다: {', '.join(missing)}")

    items = {c: _category_total(c, unit[c], people, nights, days) for c in CATEGORIES}
    total = sum(items.values())
    return {
        "items": items,
        "total": total,
        "per_person": _ceil_div(total, people),
    }


def savings_plan(goal_per_person, savings, today, departure_date):
    """목표금액과 보유금액으로 필요 저축액을 구하고, 출발까지 월·주 단위로 나눈다.

    월 수와 주 수는 올림으로 계산하며, 금액도 올림해 목표를 채우도록 한다.
    """
    required = max(goal_per_person - savings, 0)
    remaining_days = (departure_date - today).days
    if remaining_days <= 0:
        raise ValueError("출발일은 오늘보다 뒤여야 합니다.")

    remaining_weeks = math.ceil(remaining_days / 7)
    remaining_months = math.ceil(remaining_days / DAYS_PER_MONTH)
    return {
        "required": required,
        "remaining_days": remaining_days,
        "remaining_weeks": remaining_weeks,
        "remaining_months": remaining_months,
        "monthly": _ceil_div(required, remaining_months),
        "weekly": _ceil_div(required, remaining_weeks),
    }


def recalc_with_new_price(destination, style, people, nights, days, item,
                          new_unit_price, savings, today, departure_date,
                          prices_path=PRICES_PATH, unit_prices=None):
    """항목 하나의 단가가 바뀌었을 때 총액, 1인 목표금액, 저축계획의 변동을 계산한다.

    목표금액은 바뀐 예상 1인 여행비로 다시 잡고, 보유금액은 그대로 쓴다.
    """
    if item not in CATEGORIES:
        raise ValueError(f"알 수 없는 항목입니다: {item}")

    old = estimate_trip_cost(destination, style, people, nights, days,
                             prices_path=prices_path, unit_prices=unit_prices)
    new = estimate_trip_cost(destination, style, people, nights, days,
                             overrides={item: new_unit_price}, prices_path=prices_path,
                             unit_prices=unit_prices)
    old_plan = savings_plan(old["per_person"], savings, today, departure_date)
    new_plan = savings_plan(new["per_person"], savings, today, departure_date)

    return {
        "old_total": old["total"],
        "new_total": new["total"],
        "total_delta": new["total"] - old["total"],
        "old_per_person": old["per_person"],
        "new_per_person": new["per_person"],
        "per_person_delta": new["per_person"] - old["per_person"],
        "old_plan": old_plan,
        "new_plan": new_plan,
        "monthly_delta": new_plan["monthly"] - old_plan["monthly"],
        "weekly_delta": new_plan["weekly"] - old_plan["weekly"],
    }


def summarize_budget(items, people):
    """저장된 예산 항목 금액의 합계와 1인 금액을 계산한다. 1인 금액은 올림한다.

    items는 amount 키를 가진 dict 목록이다.
    """
    if people < 1:
        raise ValueError("인원은 1명 이상이어야 합니다.")
    total = sum(item["amount"] for item in items)
    return {"total": total, "per_person": _ceil_div(total, people)}


def get_unit_prices(destination, style, prices_path=PRICES_PATH):
    """도시·스타일의 항목별 단가를 dict로 돌려준다. 단가 단위는 CATEGORIES 주석을 따른다."""
    prices = _load_prices(prices_path)
    if destination not in prices or style not in prices[destination]:
        raise ValueError(f"단가 정보가 없습니다: {destination} / {style}")
    return dict(prices[destination][style])


def cumulative_savings(required, weeks):
    """주별 누적 저축액 목록을 돌려준다. 주 단위로 올림한 금액을 쌓고, 목표를 넘지 않도록 맞춘다."""
    if weeks < 1:
        raise ValueError("남은 주는 1주 이상이어야 합니다.")
    weekly = _ceil_div(required, weeks)
    return [min(weekly * k, required) for k in range(1, weeks + 1)]
