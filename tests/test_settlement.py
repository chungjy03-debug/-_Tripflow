# core/settlement.py의 멤버별 차액 계산, 자투리 원 처리, 송금 목록 생성을 검증하는 테스트
import pytest

from core.settlement import calc_balances, settle

MEMBERS = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}, {"id": 3, "name": "C"}]
# 공동자금: 모두 같은 30만원씩 입금
DEPOSITS = [
    {"member_id": 1, "amount": 300_000},
    {"member_id": 2, "amount": 300_000},
    {"member_id": 3, "amount": 300_000},
]


def _shared_fund(amount):
    """공동자금에서 결제한 공동지출 행을 만든다."""
    return {"krw_amount": amount, "paid_by": None, "is_shared": True, "owner": None}


def test_calc_balances_and_settle_transfers():
    expenses = [
        _shared_fund(900_000),
        # 공동지출 밖에서 대신 낸 금액: B가 택시 15,000원, C가 저녁 42,000원
        {"krw_amount": 15_000, "paid_by": 2, "is_shared": True, "owner": None},
        {"krw_amount": 42_000, "paid_by": 3, "is_shared": True, "owner": None},
        # A의 개인지출 57,000원을 A가 결제
        {"krw_amount": 57_000, "paid_by": 1, "is_shared": False, "owner": 1},
    ]

    balances = calc_balances(MEMBERS, DEPOSITS, expenses)

    # 공동지출 957,000원 ÷ 3 = 319,000원씩 부담
    assert balances[1]["owed"] == 319_000 + 57_000
    assert balances[1]["balance"] == -19_000
    assert balances[2]["balance"] == -4_000
    assert balances[3]["balance"] == 23_000

    transfers = settle({mid: r["balance"] for mid, r in balances.items()})

    assert transfers == [(1, 3, 19_000), (2, 3, 4_000)]


def test_indivisible_taxi_leaves_residue_in_fund():
    expenses = [
        _shared_fund(900_000),
        # 택시 5,000원: 1인당 1,666원(버림), 남은 2원은 공동자금에 남는다
        {"krw_amount": 5_000, "paid_by": 2, "is_shared": True, "owner": None},
    ]

    balances = calc_balances(MEMBERS, DEPOSITS, expenses)

    assert {mid: r["balance"] for mid, r in balances.items()} == {1: -1_666, 2: 3_334, 3: -1_666}

    transfers = settle({mid: r["balance"] for mid, r in balances.items()})

    assert transfers == [(1, 2, 1_666), (3, 2, 1_666)]


def test_leftover_fund_is_refunded_equally_with_residue_kept():
    # 입금 90만원, 공동지출 80만원 → 남은 10만원 + 나머지 2원을 3명이 나눔(환급 33,334원)
    expenses = [_shared_fund(800_000)]

    balances = calc_balances(MEMBERS, DEPOSITS, expenses)

    assert {mid: r["balance"] for mid, r in balances.items()} == {1: 0, 2: 0, 3: 0}
    assert settle({mid: r["balance"] for mid, r in balances.items()}) == []


def test_settle_rejects_residue_outside_allowed_range():
    with pytest.raises(ValueError):
        settle({1: -7_000, 2: 15_000})
