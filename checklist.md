# 체크리스트

## 계산 모듈 (완료)
- [x] core/budget.py: estimate_trip_cost, savings_plan, recalc_with_new_price, summarize_budget, get_unit_prices, cumulative_savings
- [x] core/fx.py: get_rate, get_average_rate, to_krw, simulate_rate_change, to_local
- [x] core/forecast.py: spending_pace, compare_by_category, trip_progress
- [x] core/fund.py: fund_status
- [x] core/settlement.py: calc_balances, settle
- [x] pytest 32개 통과 (`C:\Users\Chung\anaconda3\envs\vibe\python.exe -m pytest -q`)

## DB / 공통 (완료)
- [x] db.py: 테이블 5개, CRUD, TRIPFLOW_DB 환경 변수로 DB 경로 지정
- [x] ui.py: fmt_krw, fmt_signed, setup, current_rate, pick_trip
- [x] app.py: 제목과 안내 문구만 (자체 메뉴 삭제)

## 화면 (완료, AppTest 검증)
- [x] pages/1_여행전.py: 입력, 예상 여행비, 항공 가격 재계산, 저축계획, 누적 막대그래프, 저장
- [x] pages/2_환율.py: 현재 환율, 슬라이더 시뮬레이션
- [x] pages/3_여행중.py: 지출 입력·저장, 오늘 지출, 소비 현황, 초과 경고
- [x] pages/4_공동자금.py: 멤버 추가, 입금 기록, 진행바, 예상 잔액
- [x] pages/5_정산.py: 지출 분류, 멤버별 표, 송금 카드
- [x] pages/6_리포트.py: 예상 vs 실제, 도넛, 차이 표
- [x] 검증 스크립트로 6개 페이지와 app.py 렌더링 및 여행·지출 저장 확인 (예외 0건)

## 남은 작업
- [ ] 4_공동자금 입금 저장 흐름을 AppTest로 확인 (현재 렌더링만 확인)
- [ ] 5_정산 화면에 실제 데이터를 넣고 송금 카드 확인
- [ ] 실제 브라우저에서 `streamlit run app.py`로 눈으로 확인
