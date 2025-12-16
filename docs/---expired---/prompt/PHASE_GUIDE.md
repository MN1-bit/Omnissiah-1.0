# Phase Guide - AI Implementation Instructions

> **각 Phase 시작 시 해당 섹션을 프롬프트에 추가 주입**

---

## Phase 1: Data Pipeline

### Goal
VIX 현물/선물 수집, Z-Score 계산, 콘탱고/백워데이션 판정

### Implement
```python
class MarketDataManager:
    def get_vix_spot() -> float
    def get_vix_futures() -> Dict[str, float]  # {1M, 3M}
    def get_term_structure() -> Literal["CONTANGO", "BACKWARDATION"]

class VixZScoreCalculator:
    def calculate(window=126) -> float  # Look-ahead bias 금지!
```

### Verify
- [ ] 2020.03 백워데이션 정확 탐지
- [ ] API 재연결 자동화

---

## Phase 2: Regime Detection

### Goal
KER, ADX 계산, 골디락스 존 판정, Hysteresis 적용

### Implement
```python
class RegimeDetectionEngine:
    def calculate_ker(period=20) -> float      # |ΔP| / Σ|ΔP_i|
    def calculate_adx(period=14) -> float      # pandas-ta
    def is_goldilocks() -> bool                # KER>0.3 AND ADX>25
    def get_regime() -> Literal["GREEN", "RED", "BLACK"]
```

### Hysteresis
- Buffer: 0.15
- Cooldown: 5 bars minimum

### Verify
- [ ] 골디락스 외 레버리지 비활성화
- [ ] 모드 전환 ≤ 2회/분

---

## Phase 3: Risk Management

### Goal
킬 스위치, 포지션 사이징, Loss Limits

### Implement
```python
class RiskManager:
    def check_kill_switch() -> Literal["CLEAR", "HALT_ALL", "HALT_LONG", "HALT_NEW"]
    def calculate_position_size(price, yang_zhang_vol) -> int  # Half-Kelly
    def approve_order(order) -> bool  # 모든 주문 통과 필수
    def check_loss_limits() -> bool   # Daily 5%, Weekly 10%
```

### Kill Switch Conditions
1. VIX_1M > VIX_3M → HALT_ALL
2. TNX 5d > 5% → HALT_LONG
3. SPY↑ AND HYG/IEF↓ → HALT_NEW

### Verify
- [ ] RiskManager 우회 경로 없음
- [ ] 2020.03 킬 스위치 작동

---

## Phase 4: Strategy Modules

### Goal
3가지 모드별 전략 구현 (독립 클래스)

### GreenModeStrategy (Z < 1.0)
```python
# VWAP Mean Reversion
entry: price <= VWAP - 2*std
exit: price >= VWAP
target: High Beta Mid-Caps (COIN, PLTR...)
rule: Intraday only, 15:50 청산
```

### RedModeStrategy (골디락스)
```python
# Trend Following 3x Leverage
entry: price > prev_day_high AND is_goldilocks()
pyramid: 3회 (50%, 30%, 20%)
exit: price < MA_20 OR trailing -3%
target: FNGU, SOXL, TQQQ
```

### BlackModeStrategy (Z ≥ 2.0)
```python
# Liquidate or Inverse
action: liquidate_all()
inverse_entry: backwardation AND time > 14:00 AND new_day_low
inverse_exit: VIX < day_high * 0.95
max_hold: 3 days
```

### Verify
- [ ] 각 전략 독립 테스트
- [ ] 인버스 3일 제한

---

## Phase 5: Integration & Backtest

### Goal
메인 컨트롤러, 백테스팅, 성과 검증

### Implement
```python
class OmnissiahStrategy(Strategy):
    def on_trading_iteration(self):
        if self.risk_manager.check_kill_switch() != "CLEAR":
            self.black_mode.execute()
            return
        regime = self.regime_engine.get_regime()
        self.strategies[regime].execute()
```

### Backtest Periods
| Period | Dates | Purpose |
|--------|-------|---------|
| COVID | 2020.02-04 | Black Mode |
| Bull | 2020.05-2021.11 | Red Mode |
| Bear | 2022.01-10 | Transition |
| Recovery | 2023 | Green Mode |

### Target Metrics
- Sharpe ≥ 1.5
- MaxDD ≤ 25%
- All periods: Sharpe ≥ 1.0

---

## Phase 6: GUI & LLM

### Goal
모니터링 대시보드, LLM 분석 도구

### GUI (PyQt6)
```
Panels: Regime Status | Position | Strategy Monitor | LLM Chat
```

### LLM Rules (Phase 1)
- **읽기 전용** - 전략 개입 금지
- **역할:** 분석, 설명, 리포트만
- **Rate Limit:** 10회/분
- **Audit Log:** 모든 상호작용 기록

### Verify
- [ ] LLM 주문 실행 불가
- [ ] 파라미터 변경 시 사용자 승인 필수
