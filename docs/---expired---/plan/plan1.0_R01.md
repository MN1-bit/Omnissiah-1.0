# [Project Omnissiah: System Design Document]
**Ver 2.0 R01 (Revision 1)**

> 이 문서는 `plan1.0.md`의 첫 번째 개정판입니다. 원본의 핵심 철학을 유지하면서, 실제 구현을 위한 구체적인 로직과 운영 지침을 추가했습니다.

---

## 1. 핵심 철학 (Core Philosophy)

### 1.1 Anti-Speed
> HFT(초단타)와의 속도 경쟁을 포기하고, 그들이 건드릴 수 없는 **구조적 틈새**를 공략한다.

**적용 원칙:**
- 밀리초 단위 경쟁 대신 **분/시간 단위** 의사결정
- HFT가 피하는 **스프레드 넓은 시간대**(오픈/클로즈)에서 기회 포착
- 알고리즘 반응 속도보다 **시장 구조 이해**에 집중

**Trade-off:** 순간적 기회 상실 vs 안정적 실행 품질

---

### 1.2 Regime Adaptive
> 시장 상황(평화/전쟁/붕괴)에 따라 사냥감과 무기를 완전히 바꾼다 (카멜레온 전략).

**적용 원칙:**
- 단일 전략의 과최적화 금지
- 시장 Regime 변화 시 **전략 자체를 교체**
- 각 Regime에 최적화된 타겟/로직/포지션 사이즈 사용

**Trade-off:** 전략 복잡도 증가 vs 다양한 시장 상황 대응력

---

### 1.3 Concentrated Alpha
> 시장 평균(Beta)이 아닌, 가장 예리하고 변동성이 큰 **주도주(Alpha)**만을 타겟팅한다.

**적용 원칙:**
- **섹터 대장주 및 테마 리더** 집중 공격
- 분산 투자보다 **집중 투자** (최대 3종목 동시 보유)

**Trade-off:** 높은 변동성 vs 높은 수익 포텐셜

---

### 1.4 Survival First
> 수익은 공격적으로 추구하되, 자금 관리는 수학적으로 통제하여 **파산을 원천 봉쇄**한다.

**적용 원칙:**
- 단일 거래 손실 ≤ 계좌의 2%
- 일일 총 손실 ≤ 계좌의 5% (Daily Stop)
- 연속 3회 손실 시 당일 거래 중단

**Trade-off:** 수익 기회 제한 vs 자본 보존

---

## 2. 시스템 아키텍처 (System Architecture)

### 2.1 기술 스택

| 구성요소 | 선택 | 비고 |
|---------|------|------|
| **Framework** | Lumibot | Python 기반, IBKR 호환성 최우수 |
| **Broker** | Interactive Brokers | IB Gateway / TWS 연동 |
| **Primary Data** | IBKR Real-time | 틱/분봉 실시간 데이터 |
| **Backup Data** | Yahoo Finance | Historical / Fallback |
| **Language** | Python 3.10+ | Type hints 필수 사용 |

### 2.2 모듈 구성

```
omnissiah/
├── core/
│   ├── regime_detector.py    # Regime 판정 (VIX Z-Score, Kill Switch)
│   ├── position_sizer.py     # Yang-Zhang 기반 포지션 사이징
│   └── execution_guard.py    # 주문 유효성 검증
├── strategy/
│   ├── green_mode.py         # VWAP Mean Reversion
│   ├── red_mode.py           # Trend Following
│   └── black_mode.py         # Breakdown Shorting
├── scanner/
│   └── universe_screener.py  # 동적 타겟 유니버스 선정
├── indicators/
│   ├── vwap_bands.py         # VWAP ± 표준편차 밴드
│   ├── yang_zhang.py         # Yang-Zhang Volatility
│   └── vix_zscore.py         # VIX Z-Score 계산
└── main.py                   # 진입점 (Lumibot Strategy 상속)
```

### 2.3 데이터 흐름

```
[IBKR API] ──► [Data Pipeline] ──► [Regime Detector] ──► [Mode Selection]
                    │                                          │
                    ▼                                          ▼
             [Indicators]                              [Strategy Module]
                    │                                          │
                    ▼                                          ▼
             [Universe Screener] ──────────────────► [Signal Generation]
                                                           │
                                                           ▼
                                                   [Execution Guard]
                                                           │
                                                           ▼
                                                     [Order Execution]
```

---

## 3. 시장 상황 판단 (Regime Filter: The Brain)

### 3.1 VIX Z-Score 계산

$$Z_{VIX} = \frac{VIX_{current} - \mu_{VIX}(126d)}{\sigma_{VIX}(126d)}$$

**계산 세부사항:**
- **Window:** 126 거래일 (약 6개월)
- **Update:** 일 1회 (장 마감 기준)
- **Data Source:** VIX 종가 (Yahoo Finance `^VIX`)

### 3.2 모드 정의

| Mode | Z-Score 범위 | 시장 상태 | 전략 성격 |
|------|-------------|----------|----------|
| **Green** | Z < 1.0 | 평온/저변동 | Mean Reversion |
| **Red** | 1.0 ≤ Z < 2.0 | 변동성 확대 | Trend Following |
| **Black** | Z ≥ 2.0 | 공포/붕괴 | Short/Inverse |

### 3.3 모드 전환 로직 (Hysteresis)

단순 임계값 교차 시 잦은 모드 전환(Whipsaw) 방지를 위한 **버퍼 존** 적용:

```python
# Pseudo-code: Mode Transition Logic
def get_current_mode(z_score, previous_mode, cooldown_bars):
    """
    모드 전환 로직 (Hysteresis 적용)
    
    Args:
        z_score: 현재 VIX Z-Score
        previous_mode: 이전 모드 (GREEN/RED/BLACK)
        cooldown_bars: 마지막 모드 전환 이후 경과 봉 수
    
    Returns:
        new_mode, reset_cooldown (bool)
    """
    BUFFER = 0.15  # Hysteresis buffer
    COOLDOWN_MIN = 5  # 최소 5봉(5분) 유지 후 전환 가능
    
    if cooldown_bars < COOLDOWN_MIN:
        return previous_mode, False  # 쿨다운 중 - 전환 불가
    
    # Green → Red 전환
    if previous_mode == GREEN:
        if z_score >= 1.0 + BUFFER:  # 1.15 이상에서만
            return RED, True
    
    # Red → Green 전환
    if previous_mode == RED:
        if z_score < 1.0 - BUFFER:  # 0.85 이하에서만
            return GREEN, True
    
    # Red → Black 전환
    if previous_mode == RED:
        if z_score >= 2.0 + BUFFER:  # 2.15 이상에서만
            return BLACK, True
    
    # Black → Red 전환
    if previous_mode == BLACK:
        if z_score < 2.0 - BUFFER:  # 1.85 이하에서만
            return RED, True
    
    return previous_mode, False
```

### 3.4 Kill Switch (거시 경제 필터)

**즉시 거래 중단 조건:**

| 조건 | 발동 기준 | 동작 |
|------|----------|------|
| **국채 발작** | 10Y Treasury 일일 변동 > 3% | 100% 현금화 |
| **달러 폭등** | DXY > 106 AND 5일 수익률 > 2% | Long 포지션만 금지 |
| **Flash Crash** | SPY 5분 변동 > 2% | 신규 진입 금지 (기존 포지션 유지) |

```python
# Pseudo-code: Kill Switch Check
def check_kill_switch(treasury_10y_change, dxy_value, dxy_5d_return, spy_5m_change):
    if abs(treasury_10y_change) > 0.03:
        return "HALT_ALL"  # 전체 거래 중단
    
    if dxy_value > 106 and dxy_5d_return > 0.02:
        return "HALT_LONG"  # Long만 금지
    
    if abs(spy_5m_change) > 0.02:
        return "HALT_NEW"  # 신규 진입 금지
    
    return "CLEAR"  # 정상
```

---

## 4. 모드별 전략 및 타겟 (Strategy Modules)

### 4.A Green Mode: The Sniper (평화)

#### 진입 조건
- **Regime:** VIX Z-Score < 1.0
- **Time:** 09:45 ~ 15:30 (오픈 후 15분, 클로즈 전 30분 제외)

#### 타겟 유니버스
**High Beta Mid-Caps (테마주 대장)**
- 기본 풀: COIN, MARA, PLTR, SOFI, MSTR, RIOT, HOOD, AFRM
- **당일 필터:**
  - 거래량 ≥ 평균(20일)의 200%
  - 장 시작 30분 내 ±2% 이상 움직임

#### 전략 로직: VWAP Band Mean Reversion

```python
# Pseudo-code: Green Mode Entry/Exit
def green_mode_signal(price, vwap, vwap_std, position):
    lower_band = vwap - (2.0 * vwap_std)
    
    # Entry Signal
    if position == 0:
        if price <= lower_band:
            return "BUY", vwap  # 목표가: VWAP 복귀
    
    # Exit Signal
    if position > 0:
        if price >= vwap:
            return "SELL", None  # VWAP 도달 시 청산
        if price <= lower_band - (0.5 * vwap_std):
            return "STOP_LOSS", None  # 추가 하락 시 손절
    
    return "HOLD", None
```

#### 포지션 관리
- **최대 보유:** 동시 2종목
- **타임프레임:** Intraday Only (15:50까지 전량 청산)
- **오버나이트:** 절대 금지

#### 금지 사항
- 장 오픈 직후 15분 진입 금지
- FOMC/CPI 발표일 Green Mode 비활성화

---

### 4.B Red Mode: The Surfer (추세)

#### 진입 조건
- **Regime:** 1.0 ≤ VIX Z-Score < 2.0
- **Time:** 장 전/후 포함 (Pre-market 08:00 ~ After-hours 18:00)

#### 타겟 유니버스
**Concentrated Tech Bulls (레버리지 ETF/ETN)**
- **Primary:** FNGU (Big Tech 3x), SOXL (반도체 3x)
- **Secondary:** TQQQ (나스닥 3x) - 유동성 보조

#### 전략 로직: Trend Following & Breakout

```python
# Pseudo-code: Red Mode Entry/Exit
def red_mode_signal(price, prev_day_high, ma_20, position, position_count):
    MAX_PYRAMID = 3  # 최대 3회 피라미딩
    
    # Entry Signal (Breakout)
    if position == 0:
        if price > prev_day_high:
            return "BUY_INITIAL", None
    
    # Pyramiding (추세 지속 시 불타기)
    if position > 0 and position_count < MAX_PYRAMID:
        if price > prev_day_high * 1.02:  # 전고점 대비 +2%
            return "BUY_PYRAMID", None
    
    # Exit Signal
    if position > 0:
        if price < ma_20:
            return "SELL_ALL", None  # 20일선 이탈 시 전량 청산
        
        # Trailing Stop: 최고점 대비 -3%
        if price < position.highest_price * 0.97:
            return "TRAILING_STOP", None
    
    return "HOLD", None
```

#### 포지션 관리
- **피라미딩:** 최대 3회 (50% → 30% → 20% 비중)
- **타임프레임:** Swing (수일 ~ 수주 보유)
- **오버나이트:** 허용

#### 금지 사항
- 20일선 하향 돌파 상태에서 Long 진입 금지
- 단일 종목 계좌 대비 40% 초과 금지

---

### 4.C Black Mode: The Abyss Walker (붕괴)

#### 진입 조건
- **Regime:** VIX Z-Score ≥ 2.0
- **추가 안전장치:** VIX 선물 백워데이션 확인 필수

#### VIX 백워데이션 확인

```python
# Pseudo-code: Backwardation Check
def is_backwardation(vix_front_month, vix_second_month):
    """
    True if VIX 선물이 백워데이션 상태
    (단기물 > 장기물 = 극단적 공포)
    """
    return vix_front_month > vix_second_month
```

#### 타겟 유니버스
**Bubble Bursters (인버스 레버리지)**
- **Primary:** LABD (바이오 3x 인버스), SOXS (반도체 3x 인버스)
- **Secondary:** UVXY (VIX 1.5x) - 타이밍 민감

#### 전략 로직: Confirmed Breakdown

```python
# Pseudo-code: Black Mode Entry/Exit
def black_mode_signal(price, day_low, current_time, vix_current, vix_day_high, position):
    """
    확인 사살 전략: 데드캣 바운스를 피하고 확실한 붕괴 시에만 진입
    """
    # Entry Conditions (ALL must be True)
    if position == 0:
        # 1. 오후 2시 이후
        if current_time.hour < 14:
            return "WAIT", None
        
        # 2. 당일 저점 갱신
        if price > day_low:
            return "WAIT", None
        
        # 3. 백워데이션 상태 (별도 체크 필요)
        # is_backwardation() == True 가정
        
        return "SELL_SHORT", None  # 인버스 ETF 매수
    
    # Exit Signal
    if position > 0:
        # VIX가 당일 고점 대비 -5% 하락 시 탈출 (공포 감소)
        if vix_current < vix_day_high * 0.95:
            return "COVER", None
        
        # 시간 기반 청산: 익일 오전까지만 보유
        if current_time.hour >= 10 and is_next_day():
            return "COVER", None
    
    return "HOLD", None
```

#### 포지션 관리
- **최대 보유:** 동시 1종목 (집중)
- **타임프레임:** 초단기 (수 시간 ~ 1일)
- **오버나이트:** 제한적 허용 (익일 오전 청산)

#### 금지 사항
- 오전 진입 절대 금지 (데드캣 바운스 위험)
- UVXY 3일 이상 보유 금지 (Decay 심각)

---

## 5. 타겟 유니버스 선정 (Universe Screening)

### 5.1 정적 풀 (Static Pool)

각 모드별 기본 감시 대상:

| Mode | Static Pool |
|------|-------------|
| Green | COIN, MARA, PLTR, SOFI, MSTR, RIOT, HOOD, AFRM, SQ |
| Red | FNGU, SOXL, TQQQ |
| Black | LABD, SOXS, UVXY, SPXS |

### 5.2 동적 필터 (Daily Screening)

**Green Mode 필터 (장 시작 전 실행):**

```python
# Pseudo-code: Green Mode Screening
def screen_green_candidates(static_pool):
    candidates = []
    
    for ticker in static_pool:
        # 1. 거래량 폭증 체크
        avg_volume_20d = get_avg_volume(ticker, 20)
        premarket_volume = get_premarket_volume(ticker)
        
        if premarket_volume < avg_volume_20d * 0.5:
            continue  # 프리마켓 거래량 부족
        
        # 2. 갭 체크 (너무 큰 갭은 제외)
        gap_pct = get_gap_percent(ticker)
        if abs(gap_pct) > 5:
            continue  # 5% 초과 갭은 VWAP 회귀 어려움
        
        # 3. 스프레드 체크
        spread = get_bid_ask_spread(ticker)
        if spread > 0.002:  # 0.2% 초과 스프레드
            continue
        
        candidates.append(ticker)
    
    return candidates[:3]  # 상위 3개만
```

### 5.3 스크리닝 타이밍

| 시점 | 동작 |
|------|------|
| **08:30** | 프리마켓 데이터 기반 1차 스크리닝 |
| **09:30** | 장 오픈 갭 확인 후 2차 필터링 |
| **09:45** | 최종 타겟 확정 및 모니터링 시작 |

---

## 6. 리스크 관리 (Risk Management)

### 6.1 포지션 사이징 (Yang-Zhang Volatility)

$$Shares = \frac{Account \times Risk\%}{YZ\ Volatility \times Price}$$

**파라미터:**
- **Risk%:** 2% (단일 거래 최대 손실)
- **YZ Window:** 20일
- **Half-Kelly:** 산출값의 50%만 사용

```python
# Pseudo-code: Position Sizing
def calculate_position_size(account_value, price, yang_zhang_vol):
    RISK_PCT = 0.02  # 2% risk per trade
    HALF_KELLY = 0.5
    
    # 기본 수량 계산
    risk_amount = account_value * RISK_PCT
    raw_shares = risk_amount / (yang_zhang_vol * price)
    
    # Half-Kelly 적용
    final_shares = int(raw_shares * HALF_KELLY)
    
    # 최소/최대 제한
    final_shares = max(1, final_shares)
    max_shares = int((account_value * 0.25) / price)  # 단일 종목 25% 한도
    final_shares = min(final_shares, max_shares)
    
    return final_shares
```

### 6.2 계좌 레벨 리스크 한도

| 한도 | 기준 | 발동 시 동작 |
|------|------|-------------|
| **Daily Loss Limit** | 계좌 -5% | 당일 신규 진입 금지 |
| **Weekly Loss Limit** | 계좌 -10% | 주간 거래 규모 50% 축소 |
| **Drawdown Limit** | 고점 대비 -15% | 전체 거래 중단, 검토 후 재개 |

### 6.3 연속 손실 대응

```python
# Pseudo-code: Consecutive Loss Handler
def handle_consecutive_losses(loss_streak):
    if loss_streak >= 3:
        return "HALT_TODAY"  # 당일 거래 중단
    
    if loss_streak >= 5:
        return "REDUCE_SIZE"  # 포지션 사이즈 50% 축소
    
    if loss_streak >= 7:
        return "HALT_WEEK"  # 주간 거래 중단 + 전략 검토
    
    return "CONTINUE"
```

### 6.4 실행 가드 (Execution Guard)

**주문 전 체크리스트:**

```python
# Pseudo-code: Pre-Order Validation
def validate_order(ticker, side, quantity, price):
    errors = []
    
    # 1. 스프레드 체크
    bid, ask = get_bid_ask(ticker)
    spread_pct = (ask - bid) / price
    if spread_pct > 0.001:  # 0.1% 초과
        errors.append("SPREAD_TOO_WIDE")
    
    # 2. 유동성 체크
    if quantity > get_avg_volume(ticker, 5) * 0.01:
        errors.append("SIZE_TOO_LARGE")  # 5일 평균 거래량의 1% 초과
    
    # 3. 시간 체크
    if not is_market_hours():
        if side == "BUY" and not is_extended_hours_allowed():
            errors.append("OUTSIDE_HOURS")
    
    return len(errors) == 0, errors
```

---

## 7. 백테스팅 프레임워크 (Backtesting Framework)

### 7.1 검증 구간

| 구간 | 기간 | 시장 특성 | 검증 목적 |
|------|------|----------|----------|
| **COVID Crash** | 2020.02 ~ 2020.04 | 급락 + 급반등 | Black Mode 검증 |
| **Bull Run** | 2020.05 ~ 2021.11 | 강한 상승장 | Red Mode 검증 |
| **Bear Market** | 2022.01 ~ 2022.10 | 지속 하락 | Mode 전환 검증 |
| **Recovery** | 2023.01 ~ 2023.12 | 변동성 회복 | Green Mode 검증 |

### 7.2 성과 메트릭

**Required Metrics:**

| 메트릭 | 수식 | 목표 |
|--------|------|------|
| **CAGR** | 연복리 수익률 | ≥ 30% |
| **Sharpe Ratio** | (Return - Rf) / Std | ≥ 1.5 |
| **Max Drawdown** | 최대 낙폭 | ≤ 25% |
| **Win Rate** | 수익 거래 / 전체 거래 | ≥ 45% |
| **Profit Factor** | 총 이익 / 총 손실 | ≥ 1.5 |
| **Avg Win / Avg Loss** | 평균 수익 / 평균 손실 | ≥ 1.2 |

### 7.3 Pass/Fail 기준

**모든 검증 구간에서:**
- Sharpe Ratio ≥ 1.0 (최소)
- Max Drawdown ≤ 30%
- 3개월 연속 손실 없음

**전체 기간 합산:**
- CAGR ≥ 25%
- Sharpe Ratio ≥ 1.5
- Max Drawdown ≤ 25%

---

## 8. 운영 지침 (Operational Guidelines)

### 8.1 일일 체크리스트

| 시간 | 항목 |
|------|------|
| **08:00** | IB Gateway 연결 확인, Kill Switch 조건 체크 |
| **08:30** | Regime 확인 (VIX Z-Score), 프리마켓 스크리닝 |
| **09:30** | 장 오픈 - 시스템 자동 운용 시작 |
| **12:00** | 중간 점검 (포지션 상태, P&L) |
| **15:30** | Green Mode 포지션 청산 시작 |
| **16:00** | 일일 리포트 생성, 로그 백업 |

### 8.2 장애 대응 절차

| 장애 유형 | 감지 방법 | 대응 |
|----------|----------|------|
| **IB 연결 끊김** | Heartbeat 실패 | 자동 재연결 3회 시도 → 실패 시 전체 청산 |
| **데이터 지연** | 5분 이상 업데이트 없음 | 신규 진입 금지, 기존 포지션 Trailing Stop |
| **시스템 크래시** | Process 종료 | 자동 재시작, 포지션 동기화 |

### 8.3 수동 개입 기준

**시스템 무시하고 수동 개입이 필요한 상황:**
- 장 중 Circuit Breaker 발동 시
- 예상치 못한 블랙스완 이벤트 (전쟁, 자연재해 등)
- 시스템 오작동으로 비정상적 포지션 발생 시

---

## 9. 구현 로드맵 (Implementation Roadmap)

### Phase 1: Foundation (Week 1-2)
- [ ] 개발 환경 구축 (Python 3.10+, Lumibot, IB Gateway)
- [ ] IBKR Paper Trading 연결 확인
- [ ] 기본 데이터 파이프라인 구축

### Phase 2: Indicators (Week 3)
- [ ] `yang_zhang.py`: Yang-Zhang Volatility 계산
- [ ] `vix_zscore.py`: VIX Z-Score 계산 (126일 window)
- [ ] `vwap_bands.py`: VWAP ± 표준편차 밴드

### Phase 3: Core Logic (Week 4-5)
- [ ] `regime_detector.py`: Regime 판정 + Hysteresis
- [ ] `position_sizer.py`: 포지션 사이징 로직
- [ ] `execution_guard.py`: 주문 검증

### Phase 4: Strategies (Week 6-7)
- [ ] `green_mode.py`: VWAP Mean Reversion
- [ ] `red_mode.py`: Trend Following
- [ ] `black_mode.py`: Confirmed Breakdown

### Phase 5: Integration (Week 8)
- [ ] `main.py`: 전체 통합 및 Lumibot Strategy 구현
- [ ] `universe_screener.py`: 동적 스크리닝

### Phase 6: Backtesting (Week 9-10)
- [ ] 각 검증 구간별 백테스트 수행
- [ ] 성과 메트릭 분석 및 파라미터 튜닝

### Phase 7: Paper Trading (Week 11-12)
- [ ] Paper Trading 4주 진행
- [ ] 실시간 성과 모니터링
- [ ] 버그 수정 및 개선

### Phase 8: Live Trading (Week 13+)
- [ ] 소규모 실거래 시작 (계좌의 10%)
- [ ] 점진적 규모 확대

---

## 10. LLM 어시스턴트 통합 (LLM Assistant Integration)

> **설계 원칙:** LLM은 **분석 및 설명 도우미**로 기능하며, 전략 의사결정에는 직접 개입하지 않는다 (Phase 1).

### 10.1 역할 정의

| 역할 | 설명 | 개입 수준 |
|------|------|----------|
| **Analyst** | 시장 데이터, 포지션, 성과 분석 | 읽기 전용 |
| **Explainer** | 시스템 동작, 전략 로직 설명 | 읽기 전용 |
| **Reporter** | 일일/주간 리포트 생성 | 읽기 전용 |
| **Advisor** | 파라미터 튜닝 제안 (권고만) | 읽기 + 제안 |

### 10.2 LLM 접근 가능 데이터

```python
# LLM에게 노출되는 시스템 컨텍스트
class LLMContext:
    # 실시간 데이터
    current_regime: str          # GREEN/RED/BLACK
    vix_zscore: float            # 현재 VIX Z-Score
    active_positions: List[Position]
    pending_orders: List[Order]
    
    # 성과 데이터
    daily_pnl: float
    realized_trades: List[Trade]  # 최근 100건
    win_rate_7d: float
    sharpe_7d: float
    
    # 전략 상태
    current_mode_duration: int    # 현재 모드 유지 시간 (분)
    last_signal: Signal
    signal_history: List[Signal]  # 최근 50건
    
    # 시스템 상태
    connection_status: str
    last_error: Optional[Error]
    system_uptime: timedelta
```

### 10.3 LLM 기능 모듈

#### 10.3.1 실시간 해설 (Live Commentary)

```python
# Pseudo-code: LLM Commentary Generator
def generate_commentary(context: LLMContext) -> str:
    """
    현재 시장 상황과 시스템 동작에 대한 실시간 해설 생성
    
    예시 출력:
    "현재 VIX Z-Score가 1.23으로 Red Mode에 진입한 지 45분이 지났습니다.
     SOXL에 대한 Breakout 신호가 발생했고, 진입 대기 중입니다.
     오늘 거래량이 평소 대비 180%로 활발한 편입니다."
    """
    prompt = f"""
    당신은 트레이딩 시스템 해설자입니다.
    
    현재 상황:
    - Regime: {context.current_regime}
    - VIX Z-Score: {context.vix_zscore:.2f}
    - 활성 포지션: {len(context.active_positions)}개
    - 오늘 P&L: ${context.daily_pnl:,.2f}
    
    최근 신호: {context.last_signal}
    
    현재 시장 상황과 시스템 동작을 2-3문장으로 간결하게 설명하세요.
    """
    return llm.generate(prompt)
```

#### 10.3.2 거래 복기 (Trade Review)

```python
# Pseudo-code: Trade Analysis
def analyze_trade(trade: Trade) -> TradeAnalysis:
    """
    완료된 거래에 대한 심층 분석
    
    분석 항목:
    1. 진입 타이밍 적절성
    2. 청산 타이밍 적절성
    3. 포지션 사이즈 적절성
    4. 유사 과거 거래와 비교
    5. 개선 제안
    """
    prompt = f"""
    다음 거래를 분석하세요:
    
    종목: {trade.symbol}
    진입: {trade.entry_time} @ ${trade.entry_price}
    청산: {trade.exit_time} @ ${trade.exit_price}
    수익: {trade.pnl_percent:.2f}%
    
    진입 당시 조건:
    - Regime: {trade.entry_regime}
    - VIX Z-Score: {trade.entry_vix_zscore}
    - 진입 신호: {trade.entry_signal}
    
    분석 포인트:
    1. 진입 타이밍이 적절했는가?
    2. 청산이 너무 빨랐거나 늦었는가?
    3. 비슷한 조건에서의 개선 방안은?
    """
    return llm.generate_structured(prompt, TradeAnalysis)
```

#### 10.3.3 파라미터 제안 (Parameter Advisor)

```python
# Pseudo-code: Parameter Suggestion
def suggest_parameter_tuning(performance: PerformanceMetrics) -> List[Suggestion]:
    """
    최근 성과 기반 파라미터 조정 제안
    
    주의: 제안만 하고, 자동 적용하지 않음
    """
    suggestions = []
    
    # 예시: Win Rate가 낮을 경우
    if performance.win_rate < 0.40:
        suggestions.append(Suggestion(
            parameter="VWAP_BAND_MULTIPLIER",
            current_value=2.0,
            suggested_value=2.5,
            reasoning="Win Rate가 40% 미만입니다. 진입 조건을 더 보수적으로 조정하는 것을 고려하세요."
        ))
    
    # 예시: Drawdown이 클 경우
    if performance.max_drawdown > 0.20:
        suggestions.append(Suggestion(
            parameter="HALF_KELLY_MULTIPLIER",
            current_value=0.5,
            suggested_value=0.3,
            reasoning="최대 낙폭이 20%를 초과했습니다. 포지션 사이즈를 줄이는 것을 고려하세요."
        ))
    
    return suggestions
```

### 10.4 LLM 통합 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                        GUI Dashboard                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │ Chat Panel  │  │ Commentary  │  │ Trade Analysis Panel    │ │
│  │             │  │   Stream    │  │                         │ │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘ │
└─────────┼────────────────┼─────────────────────┼───────────────┘
          │                │                     │
          ▼                ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                      LLM Service Layer                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   Query     │  │  Streaming  │  │   Batch Analysis        │ │
│  │   Handler   │  │  Generator  │  │   Processor             │ │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘ │
└─────────┼────────────────┼─────────────────────┼───────────────┘
          │                │                     │
          ▼                ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Context Provider (Read-Only)                  │
│  ┌─────────────┐  ┌─────────────┐  ┌───────────────────────────┐│
│  │ Market Data │  │  Strategy   │  │  Performance Metrics     ││
│  │   Reader    │  │State Reader │  │       Reader             ││
│  └─────────────┘  └─────────────┘  └───────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### 10.5 LLM 제약 사항 (Safety Guardrails)

| 제약 | 설명 |
|------|------|
| **No Write Access** | 시스템 상태, 파라미터 직접 수정 불가 |
| **No Order Execution** | 주문 생성/수정/취소 불가 |
| **Rate Limiting** | 분당 10회 쿼리 제한 |
| **Audit Logging** | 모든 LLM 상호작용 로깅 |

### 10.6 향후 확장 (Phase 2+)

> Phase 1 안정화 이후 점진적 확장

| Phase | 기능 | 개입 수준 |
|-------|------|----------|
| Phase 2 | 신호 검증 (신호 발생 시 LLM 확인) | 읽기 + 거부권 |
| Phase 3 | 동적 파라미터 조정 (사용자 승인 후) | 읽기 + 쓰기 (승인 필요) |
| Phase 4 | 자율 전략 선택 | 읽기 + 쓰기 (자율) |

---

## 11. GUI 모니터링 시스템 (GUI Monitoring System)

> **설계 원칙:** 모든 시스템 컴포넌트를 **실시간 모니터링**하고, 전략 Fine-tuning을 위한 **깊은 인사이트**를 제공한다.

### 11.1 기술 스택

| 구성요소 | 선택 | 비고 |
|---------|------|------|
| **Framework** | PyQt6 / PySide6 | 네이티브 성능, 차트 지원 |
| **Charting** | pyqtgraph / Lightweight Charts | 실시간 업데이트 최적화 |
| **Data Binding** | Qt Model/View | 대용량 데이터 처리 |
| **Styling** | QSS (Qt Style Sheets) | 다크 모드 기본 |

### 11.2 메인 레이아웃

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ [OMNISSIAH CONTROL CENTER]                              [⚠️ ALERTS] [⚙️ SETTINGS] │
├───────────────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────┐ ┌───────────────────────────────────────┐ │
│ │      REGIME STATUS PANEL        │ │         LIVE CHART PANEL              │ │
│ │  ┌───────┐ ┌───────┐ ┌───────┐ │ │                                       │ │
│ │  │ GREEN │ │🔴 RED │ │ BLACK │ │ │  [SOXL] ━━━━━━━━━━━━━━━━━━━━━━━━━━━  │ │
│ │  └───────┘ └───────┘ └───────┘ │ │         ╱╲    ╱╲                      │ │
│ │  VIX Z-Score: 1.23             │ │        ╱  ╲  ╱  ╲                     │ │
│ │  Mode Duration: 45m            │ │   ━━━━╱    ╲╱    ╲━━━                 │ │
│ │  Last Transition: 10:45 AM     │ │  [VWAP] [MA20] [Entry] [Exit]         │ │
│ └─────────────────────────────────┘ └───────────────────────────────────────┘ │
│ ┌─────────────────────────────────┐ ┌───────────────────────────────────────┐ │
│ │      POSITION PANEL             │ │         STRATEGY MONITOR              │ │
│ │  ┌───────────────────────────┐ │ │  ┌─────────────────────────────────┐ │ │
│ │  │ SOXL  100sh  +$234 +2.3%  │ │ │  │ [Signal Flow Diagram]           │ │ │
│ │  │ Entry: $45.20 | Now: $46.25│ │ │  │                                 │ │ │
│ │  │ Stop: $43.85 | Target: VWAP│ │ │  │ Data → Regime → Strategy → Exec │ │ │
│ │  └───────────────────────────┘ │ │  │   ✓       ✓        ●        ○   │ │ │
│ │                                 │ │  └─────────────────────────────────┘ │ │
│ │  Daily P&L: +$567 (+1.2%)      │ │  Current Signal: BUY_PYRAMID          │ │
│ │  Open Positions: 1              │ │  Signal Strength: 0.78                │ │
│ └─────────────────────────────────┘ └───────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────────────────────────┐ │
│ │                           LLM ASSISTANT PANEL                               │ │
│ │  [Commentary] "Red Mode에서 SOXL 추세가 지속되고 있습니다. 2차 피라미딩 조건 충족 대기 중..." │ │
│ │  [Ask LLM] _________________________________________________ [Send]        │ │
│ └─────────────────────────────────────────────────────────────────────────────┘ │
├───────────────────────────────────────────────────────────────────────────────┤
│ [LOG STREAM] 11:23:45 | INFO | Red Mode signal: BUY_PYRAMID for SOXL          │
└───────────────────────────────────────────────────────────────────────────────┘
```

### 11.3 핵심 패널 상세

#### 11.3.1 Regime Status Panel

**실시간 표시 항목:**
- 현재 모드 (Green/Red/Black) + 시각적 하이라이트
- VIX Z-Score 게이지 (0 ~ 3+ 범위)
- 모드 전환까지 남은 버퍼 (예: "Red까지 Z-Score 0.08 남음")
- Kill Switch 상태 (CLEAR / HALT_LONG / HALT_ALL)
- 모드 유지 시간 (Hysteresis cooldown 표시)

```python
# Pseudo-code: Regime Panel Update
class RegimePanel(QWidget):
    def update_display(self, regime_state: RegimeState):
        # 모드별 색상
        colors = {
            "GREEN": "#00FF88",
            "RED": "#FF4444", 
            "BLACK": "#1A1A2E"
        }
        self.mode_indicator.setStyleSheet(f"background: {colors[regime_state.mode]}")
        
        # Z-Score 게이지
        self.zscore_gauge.setValue(regime_state.vix_zscore)
        
        # 전환 버퍼 표시
        if regime_state.mode == "GREEN":
            buffer_to_red = 1.15 - regime_state.vix_zscore
            self.buffer_label.setText(f"Red까지: {buffer_to_red:.2f}")
        
        # Cooldown 표시
        if regime_state.cooldown_remaining > 0:
            self.cooldown_bar.setValue(regime_state.cooldown_remaining)
            self.cooldown_bar.setVisible(True)
```

#### 11.3.2 Strategy Monitor Panel

**전략 내부 상태 시각화:**

```python
# Pseudo-code: Strategy Internals Display
class StrategyMonitor(QWidget):
    """
    전략 로직의 내부 상태를 투명하게 보여주는 패널
    """
    
    def display_green_mode_state(self, state: GreenModeState):
        # VWAP 밴드 상태
        self.vwap_display.update(
            vwap=state.current_vwap,
            upper_band=state.vwap + 2 * state.vwap_std,
            lower_band=state.vwap - 2 * state.vwap_std,
            current_price=state.last_price
        )
        
        # 진입 거리 표시
        distance_to_entry = (state.last_price - state.lower_band) / state.lower_band
        self.entry_distance.setText(f"진입까지: {distance_to_entry:.2%}")
        
        # 신호 흐름도 업데이트
        self.signal_flow.highlight_stage("Signal Generation")
    
    def display_red_mode_state(self, state: RedModeState):
        # Breakout 상태
        self.breakout_display.update(
            prev_high=state.prev_day_high,
            current_price=state.last_price,
            ma_20=state.ma_20
        )
        
        # 피라미딩 상태
        self.pyramid_status.update(
            current_count=state.pyramid_count,
            max_count=3,
            next_trigger=state.prev_day_high * 1.02
        )
```

#### 11.3.3 Correlation Matrix Panel

**지표 간 상호관계 분석:**

```python
# Pseudo-code: Correlation Analysis Panel
class CorrelationPanel(QWidget):
    """
    전략 파라미터와 성과 간의 상관관계 시각화
    
    Fine-tuning 인사이트 제공:
    - 어떤 조건에서 Win Rate가 높은가?
    - VIX 수준과 수익률의 관계는?
    - 시간대별 성과 차이는?
    """
    
    def generate_insights(self, trades: List[Trade]) -> List[Insight]:
        insights = []
        
        # VIX vs Win Rate
        high_vix_trades = [t for t in trades if t.entry_vix_zscore > 1.5]
        high_vix_win_rate = calculate_win_rate(high_vix_trades)
        
        if high_vix_win_rate > 0.6:
            insights.append(Insight(
                title="High VIX 성과 우수",
                description=f"VIX Z-Score > 1.5 구간에서 Win Rate {high_vix_win_rate:.1%}",
                action="Red/Black Mode 비중 확대 고려"
            ))
        
        # 시간대 분석
        morning_trades = [t for t in trades if t.entry_time.hour < 11]
        afternoon_trades = [t for t in trades if t.entry_time.hour >= 14]
        
        if calculate_sharpe(afternoon_trades) > calculate_sharpe(morning_trades) * 1.5:
            insights.append(Insight(
                title="오후 거래 성과 우수",
                description="14시 이후 진입 시 Sharpe Ratio 50% 높음",
                action="오전 진입 제한 강화 고려"
            ))
        
        return insights
    
    def render_heatmap(self, correlation_matrix):
        """
        변수 간 상관관계 히트맵
        - X축: 진입 조건 (VIX, Volume, Gap %)
        - Y축: 성과 지표 (P&L, Duration, Win/Loss)
        """
        self.heatmap.setData(correlation_matrix)
```

### 11.4 상세 분석 탭

#### 11.4.1 Trade Journal

| 컬럼 | 설명 |
|------|------|
| Date/Time | 진입/청산 시간 |
| Symbol | 종목 |
| Side | Long/Short |
| Entry/Exit | 진입가/청산가 |
| P&L | 수익/손실 (금액, %) |
| Regime | 진입 당시 모드 |
| Signal | 진입 신호 유형 |
| Duration | 보유 시간 |
| Notes | LLM 분석 요약 |

**필터 및 그룹핑:**
- 날짜 범위, 모드, 종목, 수익/손실별 필터
- 일별/주별/월별 집계
- 모드별 성과 비교

#### 11.4.2 Parameter Tuner

**실시간 파라미터 조정 인터페이스:**

```python
# Pseudo-code: Parameter Tuner Panel
class ParameterTuner(QWidget):
    """
    전략 파라미터를 GUI에서 조정하고 영향을 시뮬레이션
    """
    
    parameters = {
        "VWAP_BAND_MULTIPLIER": {
            "current": 2.0,
            "range": (1.0, 3.0),
            "step": 0.1,
            "description": "VWAP 밴드 폭 (높을수록 보수적)"
        },
        "HYSTERESIS_BUFFER": {
            "current": 0.15,
            "range": (0.05, 0.30),
            "step": 0.05,
            "description": "모드 전환 버퍼 (높을수록 전환 느림)"
        },
        "HALF_KELLY_MULTIPLIER": {
            "current": 0.5,
            "range": (0.2, 1.0),
            "step": 0.1,
            "description": "포지션 사이즈 배수"
        }
    }
    
    def on_parameter_changed(self, param_name: str, new_value: float):
        # 예상 영향 시뮬레이션
        simulation = self.backtest_with_param(param_name, new_value)
        
        self.impact_display.show({
            "Win Rate Change": simulation.win_rate_delta,
            "Sharpe Change": simulation.sharpe_delta,
            "Trade Count Change": simulation.trade_count_delta
        })
        
    def apply_parameter(self, param_name: str, new_value: float):
        # 사용자 확인 후 적용
        if self.confirm_dialog(f"{param_name}을 {new_value}로 변경하시겠습니까?"):
            self.strategy.update_parameter(param_name, new_value)
            self.audit_log.record(f"Parameter changed: {param_name} = {new_value}")
```

#### 11.4.3 Performance Analytics

**심층 성과 분석 대시보드:**

```python
# 표시 항목
performance_metrics = {
    "summary": {
        "total_pnl": "$12,345",
        "cagr": "34.5%",
        "sharpe": 1.82,
        "max_drawdown": "-18.3%",
        "win_rate": "52.1%"
    },
    "by_mode": {
        "GREEN": {"pnl": "$5,200", "trades": 45, "win_rate": "48%"},
        "RED": {"pnl": "$8,100", "trades": 23, "win_rate": "61%"},
        "BLACK": {"pnl": "-$955", "trades": 8, "win_rate": "38%"}
    },
    "by_time": {
        "09:30-11:00": {"pnl": "$3,200", "sharpe": 1.5},
        "11:00-14:00": {"pnl": "$2,100", "sharpe": 0.9},
        "14:00-16:00": {"pnl": "$7,045", "sharpe": 2.3}
    }
}
```

### 11.5 실시간 알림 시스템

| 알림 레벨 | 조건 | 표시 방식 |
|----------|------|----------|
| **INFO** | 모드 전환, 신호 발생 | 로그 스트림 |
| **WARNING** | Daily Loss 50% 도달, 연속 손실 2회 | 노란색 토스트 |
| **CRITICAL** | Kill Switch 발동, 시스템 오류 | 빨간색 모달 + 사운드 |

### 11.6 GUI 모듈 구성

```
omnissiah/
├── gui/
│   ├── main_window.py           # 메인 윈도우 + 레이아웃
│   ├── panels/
│   │   ├── regime_panel.py      # Regime 상태 패널
│   │   ├── position_panel.py    # 포지션 패널
│   │   ├── chart_panel.py       # 라이브 차트
│   │   ├── strategy_panel.py    # 전략 모니터
│   │   ├── llm_panel.py         # LLM 어시스턴트
│   │   └── log_panel.py         # 로그 스트림
│   ├── dialogs/
│   │   ├── parameter_dialog.py  # 파라미터 조정
│   │   ├── trade_detail.py      # 거래 상세
│   │   └── settings_dialog.py   # 설정
│   ├── widgets/
│   │   ├── gauge_widget.py      # Z-Score 게이지
│   │   ├── flow_diagram.py      # 신호 흐름도
│   │   └── heatmap_widget.py    # 상관관계 히트맵
│   └── styles/
│       └── dark_theme.qss       # 다크 테마
```

---

## 12. 구현 로드맵 (Implementation Roadmap)

### Phase 1: Foundation (Week 1-2)
- [ ] 개발 환경 구축 (Python 3.10+, Lumibot, IB Gateway)
- [ ] IBKR Paper Trading 연결 확인
- [ ] 기본 데이터 파이프라인 구축

### Phase 2: Indicators (Week 3)
- [ ] `yang_zhang.py`: Yang-Zhang Volatility 계산
- [ ] `vix_zscore.py`: VIX Z-Score 계산 (126일 window)
- [ ] `vwap_bands.py`: VWAP ± 표준편차 밴드

### Phase 3: Core Logic (Week 4-5)
- [ ] `regime_detector.py`: Regime 판정 + Hysteresis
- [ ] `position_sizer.py`: 포지션 사이징 로직
- [ ] `execution_guard.py`: 주문 검증

### Phase 4: Strategies (Week 6-7)
- [ ] `green_mode.py`: VWAP Mean Reversion
- [ ] `red_mode.py`: Trend Following
- [ ] `black_mode.py`: Confirmed Breakdown

### Phase 5: Integration (Week 8)
- [ ] `main.py`: 전체 통합 및 Lumibot Strategy 구현
- [ ] `universe_screener.py`: 동적 스크리닝

### Phase 6: GUI Development (Week 9-11)
- [ ] 메인 윈도우 레이아웃
- [ ] Regime / Position / Chart 패널
- [ ] Strategy Monitor 패널
- [ ] Parameter Tuner
- [ ] Performance Analytics

### Phase 7: LLM Integration (Week 12-13)
- [ ] LLM Service Layer 구축
- [ ] Context Provider 구현
- [ ] Commentary / Trade Analysis 기능
- [ ] LLM Panel GUI 연동

### Phase 8: Backtesting (Week 14-15)
- [ ] 각 검증 구간별 백테스트 수행
- [ ] 성과 메트릭 분석 및 파라미터 튜닝

### Phase 9: Paper Trading (Week 16-18)
- [ ] Paper Trading 진행
- [ ] GUI를 통한 실시간 모니터링
- [ ] LLM 분석 정확도 검증
- [ ] 버그 수정 및 개선

### Phase 10: Live Trading (Week 19+)
- [ ] 소규모 실거래 시작 (계좌의 10%)
- [ ] 점진적 규모 확대

---

## 13. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | - | 무럴킹 | Initial Draft |
| 2.0 R01 | 2024-12-15 | Antigravity | 모드 전환 로직 상세화, 백테스팅 프레임워크 추가, 운영 지침 추가, Pseudo-code 추가, LLM 통합 계획 추가, GUI 모니터링 시스템 설계 추가 |

---

이 문서는 **Project Omnissiah**의 확장된 헌법입니다.
원본 `plan1.0.md`의 철학을 계승하면서, 실제 구현을 위한 구체적인 로직을 담았습니다.

1. 프로젝트 개요: 옴니시아 (Omnissiah)

목표: 기관(HFT)과의 속도 경쟁을 포기하고, 그들이 건드릴 수 없는 구조적 틈새와 시장 상황(Regime)에 따른 유연한 대응으로 승리하는 개인용 자동매매 시스템 구축.



핵심 철학: 예측이 아닌 **'대응'**이며, 시장 상황에 따라 사냥감과 무기를 바꾸는 '카멜레온 전략'.

시스템 아키텍처:


프레임워크: Lumibot (Python 기반, IBKR 호환성 우수, 구현 용이성 선택).



브로커: Interactive Brokers (IBKR).


주문 방식: 슬리피지 방지를 위해 100% 지정가 주문(Limit Order) 사용.

2. 핵심 로직: 시장 상황 필터 (The Brain)
고정된 VIX 수치(예: 20)는 폐기하고, **'동적 공포 지수(Dynamic Z-Score)'**를 사용합니다.




공식: 최근 126일(6개월) 기준 VIX의 표준편차 대비 현재 위치 (Z-Score).



거시 필터(Kill Switch): 미국 10년물 국채 금리 일일 변동폭 > 3% 혹은 DXY(달러) 급등 시 매매 중단.


3. 모드별 상세 전략 (Strategy Modules)
A. Green Mode (평화/횡보): The Sniper

진입 조건: VIX Z-Score < 1.0 (시장이 평온함).


타겟: 'High Beta Mid-Caps' (테마가 확실하고 거래량이 평소 대비 200% 이상 터진 중형주 대장/2등주. 예: COIN, PLTR 등).

전략: VWAP 밴드 역추세 (Mean Reversion). 주가가 VWAP 하단 밴드(-2.0 표준편차) 터치 시 매수, 중심선 복귀 시 매도.


시간: 데이 트레이딩 (오버나이트 금지).

B. Red Mode (추세/상승): The Surfer

진입 조건: 1.0 ≤ VIX Z-Score < 2.0 (변동성 확대, 추세 발생).


타겟: 'Concentrated Tech Bulls' (나스닥 잡주를 뺀 순수 기술주 엑기스. 예: FNGU (Big Tech 3배), SOXL (반도체 3배)).


전략: 추세 추종 (Trend Following). 전일 고가 돌파 시 진입, 불타기(Pyramiding) 허용.


시간: 스윙 (오버나이트 허용) 및 프리/애프터마켓 선취매 활용.

C. Black Mode (붕괴/공포): The Abyss Walker

진입 조건: VIX Z-Score ≥ 2.0 (극한의 공포).



타겟: 'Bubble Bursters' (하락장에서 가장 먼저 부러지는 약한 고리. 예: LABD (바이오 인버스), SOXS (반도체 인버스), UVXY).



전략: 확인 사살 (Confirmed Breakdown).


안전장치 1 (백워데이션): VIX 1개월물이 3개월물보다 높을 때만 진입 (지금 당장 죽겠다는 공포 확인).


안전장치 2 (오후 2시 붕괴): 14:00 이후 당일 저점(Day Low) 갱신 시에만 진입 (데드캣 바운스 회피).


청산: VIX가 고점에서 -5% 꺾이면 즉시 탈출.

4. 리스크 관리 (Survival)
자금 관리 (Position Sizing):


Yang-Zhang Volatility: 오버나이트 갭 리스크를 반영한 변동성 지표를 사용하여 베팅 사이즈 조절 (변동성 클수록 수량 축소).



Half-Kelly: 산출된 최적 수량의 50%만 진입하여 파산 확률 원천 봉쇄.


실행 가드: 호가 스프레드가 0.1% 이상 벌어져 있으면(유동성 부족) 주문 금지.

이 문서는 모든 이론적 수정이 완료된 최종 설계도이며, 이제 파이썬(Lumibot)으로 구현하는 단계만 남겨두고 있습니다.