# Part 2 - Step 4: IBKR 브릿지 연결

## 상태: ✅ 완료

## 목표
QThread 기반 IBKR Gateway 연결 브릿지 구현

## 핵심 요구사항
- ✅ GUI가 멈추지 않도록 QThread 사용 (time.sleep 금지!)
- ✅ 연결 상태를 PyQt Signal로 GUI에 전달
- ✅ .env에서 연결 정보 로드
- ✅ 이벤트 기반 업데이트 (폴링 아님!)

## 구현 완료

### 이벤트 콜백 (5초 폴링 대신!)
```python
self.ib.orderStatusEvent += self._on_order_status
self.ib.execDetailsEvent += self._on_execution
self.ib.accountValueEvent += self._on_account_value
```

| 이벤트 | 발생 시점 | 동작 |
|--------|----------|------|
| `orderStatusEvent` | 주문 상태 변경 | 체결 시 잔고 업데이트 |
| `execDetailsEvent` | 체결 발생 | 체결 로그 + 잔고 업데이트 |
| `accountValueEvent` | 계좌 값 변경 | GUI 업데이트 |

### 해결된 문제
- asyncio 이벤트 루프 오류 → `util.startLoop()` 추가

## 생성된 파일
- `core/bridge.py`

## 수정된 파일
- `main.py`

## 다음 단계
→ Part 2 Step 5: 시장 데이터 수집기
