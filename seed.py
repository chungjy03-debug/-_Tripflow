# 발표용 샘플 데이터(홍콩 3박 4일, A·B·C 3명)를 DB에 넣는 스크립트
import db
from core.budget import estimate_trip_cost
from core.fx import to_local

DESTINATION = "홍콩"
STYLE = "보통"
START, END = "2026-10-10", "2026-10-13"
NIGHTS, DAYS = 3, 4
PEOPLE = 3
RATE = 170.0
DEPOSIT = 300_000
# 발표용 기준일(TRIPFLOW_TODAY=2026-06-20)에서 출발까지 정확히 16주, 4개월이 남는다.
SAMPLE_TODAY = "2026-06-20"


def _expense(day, category, krw, paid_by, shared, owner=None, one_time=False, memo=""):
    """지출 행 하나를 만든다. 현지 금액은 예정 환율로 환산한다."""
    return {
        "date": day,
        "category": category,
        "local_amount": to_local(krw, RATE),
        "rate": RATE,
        "krw_amount": krw,
        "paid_by": paid_by,
        "is_shared": int(shared),
        "owner": owner,
        "is_one_time": int(one_time),
        "memo": memo,
    }


def seed():
    """샘플 여행을 다시 넣는다. 같은 샘플 여행이 있으면 지우고 새로 넣는다."""
    db.init_db()
    for trip in db.list_trips():
        if trip["destination"] == DESTINATION and trip["start_date"] == START:
            db.delete_trip(trip["id"])

    estimate = estimate_trip_cost(DESTINATION, STYLE, PEOPLE, NIGHTS, DAYS)
    trip_id = db.create_trip({
        "destination": DESTINATION,
        "currency": "HKD",
        "start_date": START,
        "end_date": END,
        "people": PEOPLE,
        "style": STYLE,
        "planned_rate": RATE,
        "local_budget": to_local(estimate["total"], RATE),
    })

    # 본인 A의 보유금액 400,000원, B·C는 0원. 첫 번째 멤버(A)가 '본인'이다.
    a = db.create_member({"trip_id": trip_id, "name": "A", "savings": 400_000})
    b = db.create_member({"trip_id": trip_id, "name": "B", "savings": 0})
    c = db.create_member({"trip_id": trip_id, "name": "C", "savings": 0})

    for category, amount in estimate["items"].items():
        db.create_budget_item({"trip_id": trip_id, "category": category, "amount": amount})

    for member in (a, b, c):
        db.create_deposit({"trip_id": trip_id, "member_id": member, "amount": DEPOSIT,
                           "date": SAMPLE_TODAY})

    expenses = [
        # 공동자금에서 결제한 공동지출 합계 900,000원
        _expense("2026-10-10", "숙박", 750_000, None, True, one_time=True, memo="호텔 3박(방 1개)"),
        _expense("2026-10-11", "식비", 150_000, None, True, memo="공동 식비"),
        # 공동지출 밖에서 대신 낸 금액: B 택시 15,000원, C 저녁 42,000원
        _expense("2026-10-11", "교통", 15_000, b, True, memo="택시"),
        _expense("2026-10-12", "식비", 42_000, c, True, memo="저녁"),
        # A의 개인지출 57,000원을 A가 결제
        _expense("2026-10-13", "쇼핑", 57_000, a, False, owner=a, memo="A 개인 쇼핑"),
    ]
    for expense in expenses:
        db.create_expense({"trip_id": trip_id, **expense})
    return trip_id


if __name__ == "__main__":
    seed()
    print("샘플 데이터를 넣었습니다. 기준일을 맞추려면 TRIPFLOW_TODAY=2026-06-20 으로 앱을 실행하세요.")
