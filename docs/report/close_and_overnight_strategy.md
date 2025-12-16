# 청산 및 오버나이트 전략 통합 분석

## 작성일: 2024-12-16
## 버전: 2.0 (통합본)

---

## 1. 현재 청산 로직 아키텍처

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ TradingScheduler│────►│    main.py       │────►│   Strategies    │
│  (시간 기반)    │     │ _handle_pre_close │     │ (레짐별 청산)   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

### 레짐별 현재 동작

| 레짐 | 청산 트리거 | 오버나이트 | 파일 |
|------|------------|----------|------|
| 횡보 | 15:50 | ❌ 무조건 청산 | `green_mode.py` |
| 상승 | MA20 이탈 | ✅ 킵 가능 | `red_mode.py` |
| 위기 | 즉시 | ❌ 무조건 청산 | `black_mode.py` |

---

## 2. 발견된 문제점

### 🔴 높은 심각도

| 문제 | 영향 | 위치 |
|------|------|------|
| Scheduler ↔ 전략 연동 미구현 | 청산 명령이 실행 안 됨 | `main.py:379-385` |
| 시간대 불일치 (KST vs EST) | 청산 시점 오류 가능 | 전략 파일 전체 |

### 🟡 중간 심각도

| 문제 | 영향 |
|------|------|
| 포지션 추적 불일치 (전략별 독립 관리) | IBKR 포지션과 동기화 오류 |
| 횡보 Mode 무조건 청산 | 오버나이트 수익 기회 상실 |

---

## 3. 개선된 오버나이트 전략

### 3.1 핵심 원칙: **적응형 (Adaptive) 접근**

> ❌ 고정값 (예: "3% 급등 시 청산") 사용 금지
> ✅ 시장 상황에 따라 동적으로 결정

### 3.2 횡보 Mode - 조건부 킵

**킵 조건 (모두 충족 시):**
```python
def should_keep_overnight_green(self, context: dict) -> bool:
    """횡보 Mode 오버나이트 결정 (적응형)"""
    
    # 1. 금요일은 무조건 청산 (주말 리스크)
    if context["is_friday"]:
        return False
    
    # 2. 손실 중이면 청산
    if context["current_price"] < context["entry_price"]:
        return False
    
    # 3. 목표가(VWAP) 도달 임박 시 청산
    #    → 동적 임계값: 당일 변동성 기반
    vwap_distance_pct = abs(context["current_price"] - context["vwap"]) / context["vwap"]
    daily_volatility = context["daily_range_pct"]  # 당일 고저 변동폭 %
    
    if vwap_distance_pct < daily_volatility * 0.5:  # 변동성의 절반 이내
        return False
    
    # 이익 중이고 목표가와 거리 있으면 킵
    return True
```

### 3.3 상승 Mode - 동적 킵

**킵 조건:**
```python
def should_keep_overnight_red(self, context: dict) -> str:
    """상승 Mode 오버나이트 결정 (적응형)
    
    Returns:
        "KEEP_ALL", "KEEP_HALF", "LIQUIDATE_ALL"
    """
    
    # 1. VIX 역사적 평균 대비 판단 (고정값 25 대신)
    if context["vix"] > context["vix_historical_mean"] + context["vix_historical_std"]:
        return "LIQUIDATE_ALL"  # 1σ 초과 시 청산
    
    # 2. MA20 이탈이면 청산
    if context["current_price"] < context["ma20"]:
        return "LIQUIDATE_ALL"
    
    # 3. 당일 수익이 최근 N일 평균 변동폭 대비 과도한 경우
    #    → ATR(Average True Range) 기반 판단
    if context["daily_return"] > context["atr_20"] * 2:  # ATR의 2배 초과
        return "KEEP_HALF"  # 과열, 절반 청산
    
    # 4. 금요일: 부분 청산
    if context["is_friday"]:
        return "KEEP_HALF"
    
    # 그 외 전량 킵
    return "KEEP_ALL"
```

### 3.4 위기 Mode - 유지 (변경 없음)

```python
# 즉시 전량 청산 유지
return "IMMEDIATE"
```

---

## 4. 적응형 파라미터 정의

### 4.1 필요한 컨텍스트 데이터

| 파라미터 | 계산 방법 | 용도 |
|----------|----------|------|
| `daily_range_pct` | (당일 고가 - 저가) / 시가 | 횡보 VWAP 거리 판단 |
| `vix_historical_mean` | 126일 VIX 평균 | 상승 VIX 판단 |
| `vix_historical_std` | 126일 VIX 표준편차 | 상승 VIX 판단 |
| `atr_20` | 20일 ATR | 상승 과열 판단 |
| `daily_return` | (현재가 - 전일종가) / 전일종가 | 당일 수익률 |

### 4.2 캐싱 전략

```python
# 일봉 통계는 하루 1회만 계산 (기존 하이브리드 캐시 사용)
self._daily_stats_cache = {
    "date": None,
    "vix_mean": 0,
    "vix_std": 0,
    "atr_20": 0
}
```

---

## 5. 구현 계획

### 5.1 수정 파일

| 파일 | 수정 내용 |
|------|----------|
| `core/scheduler.py` | `get_close_action(context)` 파라미터 추가 |
| `strategy/green_mode.py` | `should_keep_overnight()` 추가 |
| `strategy/red_mode.py` | `should_keep_overnight()` 추가, ATR 계산 |
| `main.py` | 컨텍스트 수집 및 전달 |
| `core/market_data.py` | ATR, VIX 통계 제공 |

### 5.2 시간대 통일

```python
# 모든 시간 계산을 US/Eastern으로 통일
import pytz
US_EASTERN = pytz.timezone("US/Eastern")
now = datetime.now(US_EASTERN)
```

---

## 6. 요약

### 변경 전 vs 변경 후

| 항목 | 변경 전 | 변경 후 |
|------|---------|---------|
| 횡보 청산 | 15:50 무조건 | **이익 중 & 목표 미도달 → 킵** |
| 상승 청산 | MA20만 | **VIX/ATR 적응형 판단** |
| 고정값 | 3%, 25 등 사용 | **변동성 기반 동적 계산** |
| 시간대 | 혼용 (KST/EST) | **US/Eastern 통일** |

### 기대 효과

- 상승장에서 오버나이트 수익 캡처
- 시장 변동성에 따른 유연한 대응
- 백테스트 재현성 향상 (파라미터 자동 조정)
