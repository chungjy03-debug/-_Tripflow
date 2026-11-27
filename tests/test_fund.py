# core/fund.py의 멤버별 입금 집계, 달성률, 예상 잔액과 부족 경고를 검증하는 테스트
from core.fund import fund_status


def test_fund_status_warns_when_planned_expenses_exceed_deposits():
    deposits = [
        {"member_id": 1, "amount": 300_000},
        {"member_id": 2, "amount": 300_000},
        {"member_id": 3, "amount": 300_000},
    ]
    planned = [{"krw_amount": 1_400_000}]

    result = fund_status(deposits, planned, goal=1_400_000)

    assert result["per_member"] == {1: 300_000, 2: 300_000, 3: 300_000}
    assert result["total"] == 900_000
    assert result["achievement_pct"] == 64.3
    assert result["planned_total"] == 1_400_000
    assert result["balance"] == -500_000
    assert result["shortage"] is True


def test_fund_status_no_warning_when_balance_is_positive():
    deposits = [{"member_id": 1, "amount": 900_000}]
    planned = [{"krw_amount": 500_000}]

    result = fund_status(deposits, planned, goal=1_000_000)

    assert result["balance"] == 400_000
    assert result["shortage"] is False
