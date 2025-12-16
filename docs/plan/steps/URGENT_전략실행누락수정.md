# 🚨 긴급수정: 전략 실행 로직 누락

## 상태: ✅ 완료

## 문제 발견
**시간:** 2024-12-16 16:34
**완료:** 2024-12-16 16:38
**긴급도:** 🔴 높음

### 현상
`_trading_iteration()`에서:
- 레짐은 정상 계산됨 ✅
- **전략의 `generate_signal()` 호출 누락** ❌
- 시그널이 발생하지 않아 주문이 안 됨

### 현재 코드 흐름
```python
# main.py _trading_iteration():
1. 킬 스위치 체크 ✅
2. Z-Score 계산 ✅
3. 주기 조절 ✅
4. 레짐 판단 ✅
5. GUI 업데이트 ✅
6. ❌ 전략 generate_signal() 미호출!
```

## 수정 계획

### 수정 파일
- `main.py` - `_trading_iteration()` 메서드

### 추가할 로직
```python
# === 7. 레짐별 전략 실행 ===
if self._current_regime == "횡보":
    # Green Mode: VWAP 밴드 매매
    signal = self.green_strategy.generate_signal(...)
    if signal:
        self.signal_generated.emit(signal)

elif self._current_regime == "상승":
    # Red Mode: 3x 레버리지
    signal = self.red_strategy.generate_signal(...)
    if signal:
        self.signal_generated.emit(signal)

elif self._current_regime == "위기":
    # Black Mode: 방어 (현금화)
    signal = self.black_strategy.generate_signal(...)
    if signal:
        self.signal_generated.emit(signal)
```

### 필요 데이터
| 데이터 | 소스 |
|--------|------|
| current_price | `_last_prices["SPY"]["last"]` |
| vwap, bands | `green_strategy.calculate_vwap_bands()` |
| kill_status | `risk_manager.get_kill_status()` |
| daily_loss | `_daily_loss` |
| account | `_account_balance` |

## 완료 조건
- [ ] `_trading_iteration()`에 전략 실행 로직 추가
- [ ] 레짐별 적절한 전략 호출
- [ ] 시그널 발생 시 `signal_generated` emit
- [ ] 테스트 통과
