# Part 6 - Step 11: 실제 주문 실행 로직

## 상태: 🟡 진행 중

## 목표
IBKR API를 통한 실제 주문 전송 시스템 구현

## 핵심 기능

### 1. OrderExecutor 클래스
| 메서드 | 기능 |
|--------|------|
| `place_market_order()` | 시장가 주문 |
| `place_limit_order()` | 지정가 주문 |
| `cancel_order()` | 주문 취소 |
| `get_open_orders()` | 미체결 주문 |
| `get_positions()` | 보유 포지션 |

### 2. 안전장치
- ⚠️ 모든 주문은 `approve_order()` 통과 필수!
- 실패 시 재시도 (최대 3회)
- 3회 실패 시 팝업 알림
- 세밀한 실패 원인 로깅

### 3. PyQt Signal 연동
- `order_placed`: 주문 전송됨
- `order_filled`: 주문 체결됨
- `order_failed`: 주문 실패
- `position_update`: 포지션 변경

## 구현 항목
- [ ] core/order_executor.py 생성
- [ ] IBKRBridge와 연동
- [ ] 주문 상태 시그널
- [ ] 재시도 로직
- [ ] 실패 팝업 알림

## 의존성
- `core/bridge.py` (IB 연결)
- `core/risk_manager.py` (approve_order)

## 완료 조건
- 시장가/지정가 주문 전송 성공
- approve_order() 미통과 시 주문 거부
- 포지션 조회 정상
