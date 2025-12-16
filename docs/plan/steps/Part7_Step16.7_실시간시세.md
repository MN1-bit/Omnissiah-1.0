# Part 7 - Step 16.7: 실시간 시세 연동

## 상태: ✅ 완료

## 목표
IBKR의 reqMktData를 통한 실시간 시세 연동

## 구현 항목

### 1. core/bridge.py 수정
- [x] `price_update` 시그널 추가
- [x] `subscribe_market_data(symbols)` 메서드
- [x] `unsubscribe_market_data(symbol)` 메서드
- [x] `_on_price_update(ticker)` 콜백

### 2. main.py 수정
- [x] 연결 시 자동 구독 (SPY, QQQ, VIX)
- [x] `_on_price_update()` 핸들러
- [x] 차트 실시간 업데이트 연결

## 시그널 데이터
```python
price_update = pyqtSignal(dict)
# {
#     "symbol": str,
#     "bid": float,
#     "ask": float,
#     "last": float,
#     "volume": int,
#     "high": float,
#     "low": float,
#     "close": float
# }
```

## 구독 심볼
| 심볼 | 타입 | 용도 |
|------|------|------|
| SPY | Stock | 가격 차트, 전략 |
| QQQ | Stock | 전략 |
| VIX | Index | 레짐 판단 |

## 완료 조건
- [x] IBKR 실시간 시세 수신
- [x] 차트 실시간 업데이트
- [x] VIX 실시간 반영
