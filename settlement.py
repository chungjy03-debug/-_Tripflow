# 공동/개인 지출로 멤버별 차액을 구하고 송금 목록을 계산하는 순수 함수 모듈


def calc_balances(members, deposits, expenses):
    """멤버별 낸 돈, 부담할 돈, 차액을 계산한다.

    낸 돈 = 공동자금 입금 − 남은 공동자금 환급 + 본인이 결제한 지출(공동·개인 모두)
    부담할 돈 = 공동지출 전체 ÷ 인원(버림) + 본인 개인지출
    차액 = 낸 돈 − 부담할 돈 (양수면 받을 돈, 음수면 보낼 돈)

    남은 공동자금 = 입금 합계 − 공동자금 결제 공동지출 + 공동지출 나누고 남은 원.
    이 금액을 인원으로 버림해 환급하고, 나머지 원은 공동자금에 남는다.

    members는 id와 name 키, deposits는 member_id와 amount 키,
    expenses는 krw_amount, paid_by, is_shared, owner 키를 가진 dict 목록이다.
    paid_by가 None인 공동지출은 공동자금에서 결제한 것으로 본다.
    반환값은 {member_id: {"name", "paid", "owed", "balance"}}이다.
    """
    if not members:
        raise ValueError("멤버가 한 명 이상 있어야 합니다.")

    count = len(members)
    shared_total = sum(e["krw_amount"] for e in expenses if e["is_shared"])
    fund_spent = sum(e["krw_amount"] for e in expenses if e["is_shared"] and e["paid_by"] is None)
    deposit_total = sum(d["amount"] for d in deposits)

    share = shared_total // count
    shared_residue = shared_total - share * count
    refund = (deposit_total - fund_spent + shared_residue) // count

    result = {}
    for m in members:
        mid = m["id"]
        deposited = sum(d["amount"] for d in deposits if d["member_id"] == mid)
        advanced = sum(e["krw_amount"] for e in expenses if e["paid_by"] == mid)
        personal = sum(e["krw_amount"] for e in expenses
                       if not e["is_shared"] and e["owner"] == mid)
        paid = deposited - refund + advanced
        owed = share + personal
        result[mid] = {"name": m["name"], "paid": paid, "owed": owed, "balance": paid - owed}
    return result


def settle(balances):
    """차액으로 송금 목록을 만든다. 금액이 큰 보낼 사람과 받을 사람부터 짝지어 정산한다.

    balances는 {member_id: 차액}이다. 차액 합은 공동자금에 남은 자투리 원이므로
    0 이상이고 인원 수보다 작아야 한다. 이 범위를 벗어나면 ValueError를 낸다.
    자투리 원은 송금 대상이 아니므로 정산 목록에 포함되지 않는다.
    반환값은 [(보내는 사람 id, 받는 사람 id, 금액)] 목록이다.
    """
    total = sum(balances.values())
    if not 0 <= total < len(balances):
        raise ValueError("차액 합이 허용 범위(0 이상, 인원 수 미만)를 벗어났습니다. 정산 데이터를 확인하세요.")

    debtors = sorted(([k, -v] for k, v in balances.items() if v < 0), key=lambda x: -x[1])
    creditors = sorted(([k, v] for k, v in balances.items() if v > 0), key=lambda x: -x[1])

    transfers = []
    i = j = 0
    while i < len(debtors) and j < len(creditors):
        amount = min(debtors[i][1], creditors[j][1])
        transfers.append((debtors[i][0], creditors[j][0], amount))
        debtors[i][1] -= amount
        creditors[j][1] -= amount
        if debtors[i][1] == 0:
            i += 1
        if creditors[j][1] == 0:
            j += 1
    return transfers
