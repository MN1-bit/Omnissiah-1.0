# AGENTS.md - Project Omnissiah AI Rules

> **이 파일은 모든 AI 상호작용 시 프롬프트로 주입됩니다.**

## 1. Immutable Principles

### Philosophy (절대 위반 불가)
| ID | Rule |
|----|------|
| P-01 | **Response over Prediction** - 예측 모델(ML/DL) 금지. 레짐 감지 후 대응만 |
| P-02 | **No Speed Competition** - ms 최적화 불필요. 분/시간 단위 의사결정 |
| P-03 | **Capital First** - 모든 매수는 RiskManager.approve_order() 통과 필수 |
| P-04 | **Simplicity** - 블랙박스 모델 금지. 해석 가능한 규칙만 |

### Technical (기술 규칙)
| ID | Rule |
|----|------|
| T-01 | **Look-ahead Bias 금지** - 백테스팅 시 미래 데이터 참조 불가 |
| T-02 | **Defensive Coding** - 모든 API 호출에 try-except + Exponential Backoff |
| T-03 | **Kill Switch 필수** - 매 tick마다 check_kill_switch() 호출 |
| T-04 | **Limit Order Only** - Market Order 사용 금지 |
| T-05 | **Type Safety** - 모든 함수에 type hints. 가격은 Decimal 권장 |

---

## 2. Tech Stack

```
Python 3.10+ | Lumibot | IBKR | pandas-ta | PyQt6
```

---

## 3. Key Parameters

| Param | Value | Note |
|-------|-------|------|
| VIX Z Window | 126일 | 6개월 |
| KER Threshold | 0.3 | 골디락스 진입 |
| ADX Threshold | 25 | 추세 존재 |
| Hysteresis | 0.15 | 모드 전환 버퍼 |
| Half-Kelly | 50% | 파산 방지 |
| Inverse Max Hold | 3일 | 변동성 항력 |

---

## 4. Regime Definition

| Mode | Condition | Strategy |
|------|-----------|----------|
| GREEN | Z < 1.0 | VWAP Mean Reversion |
| RED | 1.0 ≤ Z < 2.0 AND KER>0.3 AND ADX>25 | 3x Leverage Trend |
| BLACK | Z ≥ 2.0 OR Backwardation | Liquidate / Inverse |

---

## 5. Kill Switch Triggers

```python
def check_kill_switch():
    if VIX_1M > VIX_3M:          return "HALT_ALL"   # 백워데이션
    if TNX_5d_change > 0.05:     return "HALT_LONG"  # 국채 급등
    if SPY_up AND HYG_IEF_down:  return "HALT_NEW"   # 신용 발산
    return "CLEAR"
```

---

## 6. Module Structure

```
omnissiah/
├── core/     [regime_detector, risk_manager, data_manager]
├── strategy/ [green_mode, red_mode, black_mode]
├── gui/      [Phase 6]
└── main.py   [OmnissiahStrategy]
```

---

## 7. Critical Rules

1. **RiskManager 우회 금지** - 모든 주문은 approve_order() 통과
2. **인버스 3일 제한** - 보유 기간 초과 시 강제 청산
3. **골디락스 외 레버리지 금지** - KER>0.3 AND ADX>25 아니면 현금/1x만
4. **Intraday 청산** - Green Mode는 15:50까지 전량 청산

---

## 8. Reference Docs

- `docs/plan/plan1.0_R01.md` - 세부 로직
- `docs/ref/2고알파*.md` - 전략 수학
- `docs/prompt/PHASE_GUIDE.md` - Phase별 지시
