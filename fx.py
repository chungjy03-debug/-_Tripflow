# 현지 통화와 원화 사이의 환율 조회, 캐시 폴백, 원화 환산, 환율 변동 시뮬레이션 함수 모듈
import calendar
import json
from datetime import date
from pathlib import Path

import requests

BASE_URL = "https://api.frankfurter.dev/v1"
CACHE_PATH = Path(__file__).resolve().parent.parent / "data" / "fx_cache.json"
TIMEOUT_SECONDS = 5

# 응답 구조(실제 호출로 확인):
#   latest:      {"amount": 1.0, "base": "HKD", "date": "...", "rates": {"KRW": 171.57}}
#   time series: {"amount": 1.0, "base": "HKD", "start_date": "...", "end_date": "...",
#                 "rates": {"2026-09-01": {"KRW": 175.31}, ...}}


def _fetch_json(path, params):
    """Frankfurter API에 GET 요청을 보내고 JSON 응답을 돌려준다. 실패하면 예외를 그대로 던진다."""
    response = requests.get(f"{BASE_URL}/{path}", params=params, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


def _read_cache(cache_path):
    """로컬 환율 캐시를 읽는다. 파일이 없거나 깨졌으면 빈 dict를 돌려준다."""
    try:
        with open(cache_path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _write_cache(currency, rate, cache_path):
    """통화별 마지막으로 받은 환율을 로컬 캐시 파일에 저장한다."""
    cache = _read_cache(cache_path)
    cache[currency] = rate
    cache_path = Path(cache_path)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def _months_ago(day, months):
    """날짜에서 지정한 개월 수만큼 이전 날짜를 구한다. 말일이 없는 달이면 그 달의 말일로 맞춘다."""
    month_index = day.month - months
    year = day.year + (month_index - 1) // 12
    month = (month_index - 1) % 12 + 1
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(day.day, last_day))


def get_rate(currency, user_rate=None, cache_path=CACHE_PATH):
    """1단위당 원화 환율을 조회한다.

    순서는 Frankfurter 최신 환율, 로컬 캐시의 마지막 환율, 사용자 입력값(user_rate)이다.
    API 호출에 성공하면 캐시를 갱신한다. 세 가지 모두 없으면 RuntimeError를 낸다.
    """
    try:
        data = _fetch_json("latest", {"base": currency, "symbols": "KRW"})
        rate = float(data["rates"]["KRW"])
    except (requests.RequestException, KeyError, TypeError, ValueError) as err:
        cached = _read_cache(cache_path).get(currency)
        if cached is not None:
            return float(cached)
        if user_rate is not None:
            return float(user_rate)
        raise RuntimeError(f"{currency} 환율을 구할 수 없습니다.") from err

    _write_cache(currency, rate, cache_path)
    return rate


def get_average_rate(currency, months=3, user_rate=None, today=None, cache_path=CACHE_PATH):
    """최근 여러 달 동안의 평균 환율을 구한다. 조회에 실패하면 get_rate와 같은 폴백을 쓴다."""
    today = today or date.today()
    start = _months_ago(today, months)
    try:
        data = _fetch_json(f"{start.isoformat()}..{today.isoformat()}",
                           {"base": currency, "symbols": "KRW"})
        rates = [float(day["KRW"]) for day in data["rates"].values()]
        if not rates:
            raise ValueError("환율 데이터가 비어 있습니다.")
    except (requests.RequestException, KeyError, TypeError, ValueError):
        return get_rate(currency, user_rate=user_rate, cache_path=cache_path)
    return sum(rates) / len(rates)


def to_krw(local_amount, rate):
    """현지 통화 금액을 원화로 환산하고 반올림해 정수로 돌려준다."""
    return int(round(local_amount * rate))


def _ceil_div(a, b):
    """정수 나눗셈을 올림해 금액이 목표에 모자라지 않도록 한다."""
    return -(-a // b)


def simulate_rate_change(local_total, old_rate, new_rate, saved, goal, weeks_left):
    """환율이 바뀌었을 때 원화 지출, 추가 필요금액, 새 목표금액, 주별 저축액의 변화를 계산한다.

    새 목표금액은 원화 지출 변동분만큼 기존 목표를 올리거나 내린 값이다.
    """
    if weeks_left <= 0:
        raise ValueError("남은 주는 1주 이상이어야 합니다.")

    before = to_krw(local_total, old_rate)
    after = to_krw(local_total, new_rate)
    delta = after - before
    new_goal = goal + delta
    return {
        "before_krw": before,
        "after_krw": after,
        "delta_krw": delta,
        "extra_needed": max(delta, 0),
        "new_goal": new_goal,
        "old_weekly": _ceil_div(max(goal - saved, 0), weeks_left),
        "new_weekly": _ceil_div(max(new_goal - saved, 0), weeks_left),
    }


def to_local(krw_amount, rate):
    """원화 금액을 현지 통화로 환산하고 소수 둘째 자리까지 반올림한다. 예정 환율로 예산을 현지 통화로 바꿀 때 쓴다."""
    return round(krw_amount / rate, 2)


# API를 못 받을 때 쓰는 자주 쓰는 통화 목록
FALLBACK_CURRENCIES = ["AUD", "EUR", "GBP", "HKD", "JPY", "SGD", "THB", "USD"]


def get_currencies():
    """Frankfurter가 지원하는 통화 코드 목록을 돌려준다(원화 제외). 실패하면 자주 쓰는 통화 목록을 돌려준다."""
    try:
        data = _fetch_json("currencies", {})
        codes = sorted(code for code in data if code != "KRW")
    except (requests.RequestException, TypeError, ValueError, AttributeError):
        return list(FALLBACK_CURRENCIES)
    return codes or list(FALLBACK_CURRENCIES)
