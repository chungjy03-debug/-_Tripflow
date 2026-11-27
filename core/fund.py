# 공동 여행자금의 입금 현황과 예상 잔액을 계산하는 순수 함수 모듈


def fund_status(deposits, planned_expenses, goal):
    """멤버별 입금액, 총 모금액, 목표 달성률, 예상 잔액과 부족 여부를 계산한다.

    deposits는 member_id와 amount 키를 가진 dict 목록이다.
    planned_expenses는 krw_amount 키를 가진 dict 목록이다.
    잔액(총 모금액 − 예정 지출)이 음수면 shortage를 True로 돌려준다.
    """
    if goal <= 0:
        raise ValueError("목표 금액은 0보다 커야 합니다.")

    per_member = {}
    for d in deposits:
        per_member[d["member_id"]] = per_member.get(d["member_id"], 0) + d["amount"]

    total = sum(d["amount"] for d in deposits)
    planned_total = sum(e["krw_amount"] for e in planned_expenses)
    balance = total - planned_total
    return {
        "per_member": per_member,
        "total": total,
        "achievement_pct": round(total / goal * 100, 1),
        "planned_total": planned_total,
        "balance": balance,
        "shortage": balance < 0,
    }
