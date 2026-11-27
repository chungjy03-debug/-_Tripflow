# core/fx.py의 환율 조회(API mock), 캐시 폴백, 원화 환산, 환율 변동 시뮬레이션을 검증하는 테스트
from datetime import date

import pytest
import requests

from core import fx
from core.fx import get_average_rate, get_rate, simulate_rate_change, to_krw


def _latest_payload(rate):
    """Frankfurter latest 응답과 같은 구조의 가짜 응답을 만든다."""
    return {"amount": 1.0, "base": "HKD", "date": "2026-11-26", "rates": {"KRW": rate}}


def _fail(path, params):
    """네트워크 실패를 흉내 낸다."""
    raise requests.ConnectionError("mock failure")


def test_to_krw_50hkd_at_170():
    assert to_krw(50, 170) == 8_500


def test_simulate_rate_change_hkd_5000_170_to_190():
    result = simulate_rate_change(5_000, 170, 190, saved=0, goal=0, weeks_left=1)

    assert result["before_krw"] == 850_000
    assert result["after_krw"] == 950_000
    assert result["delta_krw"] == 100_000
    assert result["extra_needed"] == 100_000


def test_simulate_rate_change_weekly_savings_150000_to_175000():
    result = simulate_rate_change(5_000, 170, 190, saved=900_000,
                                  goal=1_500_000, weeks_left=4)

    assert result["new_goal"] == 1_600_000
    assert result["old_weekly"] == 150_000
    assert result["new_weekly"] == 175_000


def test_get_rate_parses_latest_response(monkeypatch, tmp_path):
    monkeypatch.setattr(fx, "_fetch_json", lambda path, params: _latest_payload(171.57))

    assert get_rate("HKD", cache_path=tmp_path / "cache.json") == 171.57


def test_get_rate_saves_successful_rate_to_cache(monkeypatch, tmp_path):
    cache = tmp_path / "cache.json"
    monkeypatch.setattr(fx, "_fetch_json", lambda path, params: _latest_payload(171.57))

    get_rate("HKD", cache_path=cache)

    assert fx._read_cache(cache)["HKD"] == 171.57


def test_get_rate_falls_back_to_cache_when_api_fails(monkeypatch, tmp_path):
    cache = tmp_path / "cache.json"
    fx._write_cache("HKD", 168.0, cache)
    monkeypatch.setattr(fx, "_fetch_json", _fail)

    assert get_rate("HKD", user_rate=999.0, cache_path=cache) == 168.0


def test_get_rate_falls_back_to_user_input_when_no_cache(monkeypatch, tmp_path):
    monkeypatch.setattr(fx, "_fetch_json", _fail)

    assert get_rate("HKD", user_rate=175.0, cache_path=tmp_path / "none.json") == 175.0


def test_get_rate_raises_when_no_source_available(monkeypatch, tmp_path):
    monkeypatch.setattr(fx, "_fetch_json", _fail)

    with pytest.raises(RuntimeError):
        get_rate("HKD", cache_path=tmp_path / "none.json")


def test_get_average_rate_is_mean_of_daily_rates(monkeypatch, tmp_path):
    payload = {
        "amount": 1.0, "base": "HKD",
        "start_date": "2026-08-27", "end_date": "2026-11-27",
        "rates": {"2026-09-01": {"KRW": 170.0}, "2026-10-01": {"KRW": 180.0}},
    }
    monkeypatch.setattr(fx, "_fetch_json", lambda path, params: payload)

    result = get_average_rate("HKD", months=3, today=date(2026, 11, 27),
                              cache_path=tmp_path / "cache.json")

    assert result == 175.0


def test_get_currencies_lists_supported_codes_without_krw(monkeypatch):
    payload = {"USD": "US Dollar", "KRW": "South Korean Won", "EUR": "Euro"}
    monkeypatch.setattr(fx, "_fetch_json", lambda path, params: payload)

    assert fx.get_currencies() == ["EUR", "USD"]


def test_get_currencies_falls_back_when_api_fails(monkeypatch):
    monkeypatch.setattr(fx, "_fetch_json", _fail)

    assert fx.get_currencies() == fx.FALLBACK_CURRENCIES


def test_months_ago_clamps_to_end_of_month():
    assert fx._months_ago(date(2026, 5, 31), 3) == date(2026, 2, 28)
