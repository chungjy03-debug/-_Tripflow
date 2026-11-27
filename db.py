# SQLite 테이블 생성과 기본 CRUD 함수를 제공하는 데이터 접근 모듈
import os
import sqlite3
from pathlib import Path

# TRIPFLOW_DB 환경 변수가 있으면 그 경로를 쓴다(테스트용 임시 DB 지정).
DB_PATH = Path(os.environ.get("TRIPFLOW_DB", Path(__file__).parent / "data" / "tripflow.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS trips (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    destination   TEXT NOT NULL,
    currency      TEXT NOT NULL,
    start_date    TEXT NOT NULL,
    end_date      TEXT NOT NULL,
    people        INTEGER NOT NULL,
    style         TEXT NOT NULL CHECK (style IN ('알뜰', '보통', '여유')),
    planned_rate  REAL NOT NULL,
    local_budget  REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS members (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    trip_id  INTEGER NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    name     TEXT NOT NULL,
    savings  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS budget_items (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    trip_id  INTEGER NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    amount   INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS deposits (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    trip_id   INTEGER NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    member_id INTEGER NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    amount    INTEGER NOT NULL,
    date      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS expenses (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    trip_id      INTEGER NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    date         TEXT NOT NULL,
    category     TEXT NOT NULL,
    local_amount REAL NOT NULL,
    rate         REAL NOT NULL,
    krw_amount   INTEGER NOT NULL,
    paid_by      INTEGER REFERENCES members(id) ON DELETE SET NULL,
    is_shared    INTEGER NOT NULL DEFAULT 0 CHECK (is_shared IN (0, 1)),
    owner        INTEGER REFERENCES members(id) ON DELETE SET NULL,
    is_one_time  INTEGER NOT NULL DEFAULT 0 CHECK (is_one_time IN (0, 1)),
    memo         TEXT
);
"""

# 테이블별 저장 가능한 컬럼 목록(화이트리스트). SQL 문자열에 들어가는 이름을 이 목록으로만 제한한다.
COLUMNS = {
    "trips": ["destination", "currency", "start_date", "end_date", "people",
              "style", "planned_rate", "local_budget"],
    "members": ["trip_id", "name", "savings"],
    "budget_items": ["trip_id", "category", "amount"],
    "deposits": ["trip_id", "member_id", "amount", "date"],
    "expenses": ["trip_id", "date", "category", "local_amount", "rate", "krw_amount",
                 "paid_by", "is_shared", "owner", "is_one_time", "memo"],
}


def get_connection(db_path=DB_PATH):
    """외래키 제약을 켠 SQLite 연결을 만들고 행을 dict처럼 읽도록 설정한다."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path=DB_PATH):
    """모든 테이블이 없으면 생성한다."""
    with get_connection(db_path) as conn:
        conn.executescript(SCHEMA)
    conn.close()


def _insert(table, data, db_path):
    """테이블에 한 행을 추가하고 새 id를 돌려준다."""
    cols = [c for c in COLUMNS[table] if c in data]
    sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})"
    conn = get_connection(db_path)
    try:
        with conn:
            cur = conn.execute(sql, [data[c] for c in cols])
        return cur.lastrowid
    finally:
        conn.close()


def _get(table, row_id, db_path):
    """id로 한 행을 dict로 돌려준다. 없으면 None."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (row_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def _list(table, db_path, where=None, params=()):
    """조건에 맞는 행들을 id 순서대로 dict 리스트로 돌려준다."""
    sql = f"SELECT * FROM {table}"
    if where:
        sql += f" WHERE {where}"
    conn = get_connection(db_path)
    try:
        return [dict(r) for r in conn.execute(sql + " ORDER BY id", params).fetchall()]
    finally:
        conn.close()


def _update(table, row_id, data, db_path):
    """한 행의 전달된 컬럼만 수정한다. 수정된 행 수를 돌려준다."""
    cols = [c for c in COLUMNS[table] if c in data]
    if not cols:
        return 0
    sql = f"UPDATE {table} SET {', '.join(f'{c} = ?' for c in cols)} WHERE id = ?"
    conn = get_connection(db_path)
    try:
        with conn:
            cur = conn.execute(sql, [data[c] for c in cols] + [row_id])
        return cur.rowcount
    finally:
        conn.close()


def _delete(table, row_id, db_path):
    """한 행을 삭제한다. 삭제된 행 수를 돌려준다."""
    conn = get_connection(db_path)
    try:
        with conn:
            cur = conn.execute(f"DELETE FROM {table} WHERE id = ?", (row_id,))
        return cur.rowcount
    finally:
        conn.close()


# ---- trips ----
def create_trip(data, db_path=DB_PATH):
    """여행 정보를 추가하고 새 id를 돌려준다."""
    return _insert("trips", data, db_path)


def get_trip(trip_id, db_path=DB_PATH):
    """id로 여행 정보를 조회한다."""
    return _get("trips", trip_id, db_path)


def list_trips(db_path=DB_PATH):
    """모든 여행 정보를 조회한다."""
    return _list("trips", db_path)


def update_trip(trip_id, data, db_path=DB_PATH):
    """여행 정보의 전달된 항목을 수정한다."""
    return _update("trips", trip_id, data, db_path)


def delete_trip(trip_id, db_path=DB_PATH):
    """여행 정보를 삭제한다. 하위 데이터도 함께 삭제된다."""
    return _delete("trips", trip_id, db_path)


# ---- members ----
def create_member(data, db_path=DB_PATH):
    """여행 멤버를 추가하고 새 id를 돌려준다."""
    return _insert("members", data, db_path)


def get_member(member_id, db_path=DB_PATH):
    """id로 멤버를 조회한다."""
    return _get("members", member_id, db_path)


def list_members(trip_id, db_path=DB_PATH):
    """여행의 멤버 목록을 조회한다."""
    return _list("members", db_path, "trip_id = ?", (trip_id,))


def update_member(member_id, data, db_path=DB_PATH):
    """멤버 정보의 전달된 항목을 수정한다."""
    return _update("members", member_id, data, db_path)


def delete_member(member_id, db_path=DB_PATH):
    """멤버를 삭제한다."""
    return _delete("members", member_id, db_path)


# ---- budget_items ----
def create_budget_item(data, db_path=DB_PATH):
    """예산 항목을 추가하고 새 id를 돌려준다."""
    return _insert("budget_items", data, db_path)


def get_budget_item(item_id, db_path=DB_PATH):
    """id로 예산 항목을 조회한다."""
    return _get("budget_items", item_id, db_path)


def list_budget_items(trip_id, db_path=DB_PATH):
    """여행의 예산 항목 목록을 조회한다."""
    return _list("budget_items", db_path, "trip_id = ?", (trip_id,))


def update_budget_item(item_id, data, db_path=DB_PATH):
    """예산 항목의 전달된 항목을 수정한다."""
    return _update("budget_items", item_id, data, db_path)


def delete_budget_item(item_id, db_path=DB_PATH):
    """예산 항목을 삭제한다."""
    return _delete("budget_items", item_id, db_path)


# ---- deposits ----
def create_deposit(data, db_path=DB_PATH):
    """입금 기록을 추가하고 새 id를 돌려준다."""
    return _insert("deposits", data, db_path)


def get_deposit(deposit_id, db_path=DB_PATH):
    """id로 입금 기록을 조회한다."""
    return _get("deposits", deposit_id, db_path)


def list_deposits(trip_id, db_path=DB_PATH):
    """여행의 입금 기록 목록을 조회한다."""
    return _list("deposits", db_path, "trip_id = ?", (trip_id,))


def update_deposit(deposit_id, data, db_path=DB_PATH):
    """입금 기록의 전달된 항목을 수정한다."""
    return _update("deposits", deposit_id, data, db_path)


def delete_deposit(deposit_id, db_path=DB_PATH):
    """입금 기록을 삭제한다."""
    return _delete("deposits", deposit_id, db_path)


# ---- expenses ----
def create_expense(data, db_path=DB_PATH):
    """지출 기록을 추가하고 새 id를 돌려준다."""
    return _insert("expenses", data, db_path)


def get_expense(expense_id, db_path=DB_PATH):
    """id로 지출 기록을 조회한다."""
    return _get("expenses", expense_id, db_path)


def list_expenses(trip_id, db_path=DB_PATH):
    """여행의 지출 기록 목록을 조회한다."""
    return _list("expenses", db_path, "trip_id = ?", (trip_id,))


def update_expense(expense_id, data, db_path=DB_PATH):
    """지출 기록의 전달된 항목을 수정한다."""
    return _update("expenses", expense_id, data, db_path)


def delete_expense(expense_id, db_path=DB_PATH):
    """지출 기록을 삭제한다."""
    return _delete("expenses", expense_id, db_path)
