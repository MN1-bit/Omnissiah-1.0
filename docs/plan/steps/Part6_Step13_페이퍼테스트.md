# Part 6 - Step 13: Paper Trading 테스트

## 상태: 🟡 진행 중

## 목표
IBKR Paper Trading 환경에서 전체 시스템 통합 테스트

## ⚠️ 사전 요구사항
→ `Part6_Step13_UserEnd.md` 참조

## 테스트 시나리오

### 1. 연결 테스트
- [ ] IBKR Gateway 연결 확인
- [ ] 계좌 정보 수신 확인
- [ ] 실시간 시세 수신 확인

### 2. 레짐 판단 테스트
- [ ] Z-Score 계산 정상
- [ ] 횡보/상승/위기 표시 정상
- [ ] GUI 색상 변경 정상

### 3. 주문 흐름 테스트
- [ ] 시장가 주문 전송
- [ ] 주문 체결 확인
- [ ] 포지션 업데이트 확인
- [ ] 손익 계산 확인

### 4. 청산 테스트
- [ ] 15:50 청산 경고
- [ ] 레짐별 청산 로직
- [ ] 전량 청산 확인

## 통합 포인트 (main.py 수정 필요)

### 1. OrderExecutor 연결
```python
from core.order_executor import OrderExecutor
self.order_executor = OrderExecutor(risk_manager=self.risk_manager)
```

### 2. Scheduler 연결
```python
from core.scheduler import TradingScheduler
self.scheduler = TradingScheduler()
self.scheduler.pre_close_warn.connect(self._handle_pre_close)
```

### 3. 전략 신호 → 주문 실행
```python
self.green_strategy.signal_generated.connect(self._execute_order)
```

## 검증 항목
- 주문 전송 성공/실패 로그
- 체결 가격 및 수량
- 포지션 변화 GUI 반영
- 손익 계산 정확성

## 완료 조건
- Paper 환경에서 최소 1회 주문 체결
- 레짐 전환 시 GUI 정상 반영
