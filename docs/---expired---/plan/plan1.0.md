지금까지의 치열한 논쟁과 수많은 수정(Revision)을 거쳐 완성된, 신들과 당신(무럴킹)이 합의한 최종 전략 명세서입니다.

이 문서는 더 이상 수정이 필요 없는 **[Project Omnissiah: The Final Design Document]**입니다. 이전의 낡은 개념(고정 VIX, 단순 TQQQ, ATR 등)은 모두 폐기되었으며, 오직 '최종 합의된 진리'만이 담겨있습니다.

---

# [Project Omnissiah: System Design Document]
**Ver 2.0 (Final Release)**

## 1. 핵심 철학 (Core Philosophy)
* **Anti-Speed:** HFT(초단타)와의 속도 경쟁을 포기하고, 그들이 건드릴 수 없는 구조적 틈새를 공략한다.
* **Regime Adaptive:** 시장 상황(평화/전쟁/붕괴)에 따라 사냥감과 무기를 완전히 바꾼다 (카멜레온 전략).
* **Concentrated Alpha:** 시장 평균(Beta)이 아닌, 가장 예리하고 변동성이 큰 주도주(Alpha)만을 타겟팅한다.
* **Survival First:** 수익은 공격적으로 추구하되, 자금 관리는 수학적(Yang-Zhang, Half-Kelly)으로 통제하여 파산을 원천 봉쇄한다.

---

## 2. 시스템 아키텍처 (System Architecture)
* **Framework:** **Lumibot** (Python 기반, 유연성 및 IBKR 호환성 최우수).
* **Broker:** **Interactive Brokers (IBKR)** via IB Gateway / TWS.
* **Data Source:** IBKR 실시간 데이터 (Primary) + Yahoo Finance (Backup/Histroical).
* **Execution:** 100% **지정가 주문 (Limit Order)** 사용 (슬리피지 방지).

---

## 3. 시장 상황 판단 (Regime Filter: The Brain)
모든 전략은 **'동적 공포 지수(Dynamic Z-Score)'**에 의해 결정된다. 고정된 VIX 수치는 사용하지 않는다.

* **지표:** **VIX Z-Score (126일 기준)**
    * $$Z = \frac{\text{Current VIX} - \text{Avg VIX}(126d)}{\text{StdDev VIX}(126d)}$$
* **거시 경제 필터 (Kill Switch):**
    * 미국 10년물 국채 금리 일일 변동폭 > **3%** (발작) $\rightarrow$ **Trading Halted (현금 100%)**
    * 달러 인덱스(DXY) > **106** 및 급등세 $\rightarrow$ **Long Position Halted**

---

## 4. 모드별 전략 및 타겟 (Strategy Modules)

### A. Green Mode: The Sniper (평화)
* **진입 조건:** **VIX Z-Score < 1.0** (시장이 평온함)
* **타겟 유니버스 (High Beta Mid-Caps):**
    * 테마가 확실하고 기관 수급이 쏠린 **중형주 대장 & 2등주**.
    * **List:** COIN(코인베이스), MARA(마라톤), PLTR(팔란티어), SOFI, MSTR 등.
    * *필터:* 당일 거래량 평소 대비 200% 이상 폭증 종목.
* **전략 로직:** **VWAP Band Mean Reversion (평균 회귀)**
    * **매수:** 주가가 **VWAP - 2.0 표준편차** (Band Lower) 터치 시.
    * **매도:** 주가가 **VWAP 중심선** 복귀 시.
* **타임프레임:** **Intraday (데이 트레이딩).** 오버나이트 금지 (장 마감 전 전량 청산).

### B. Red Mode: The Surfer (추세)
* **진입 조건:** **1.0 $\le$ VIX Z-Score < 2.0** (변동성 확대, 추세 발생)
* **타겟 유니버스 (Concentrated Tech Bulls):**
    * 나스닥 잡주를 뺀, 상승장의 순수 결정체.
    * **List:** **FNGU** (Big Tech 3배 ETN), **SOXL** (반도체 3배 ETF).
* **전략 로직:** **Trend Following & Breakout (추세 추종)**
    * **진입:** 전일 고가(High) 돌파 or 20일선 지지 반등 시.
    * **피라미딩:** 추세가 지속되면 불타기 허용.
* **타임프레임:** **Swing (스윙).** 추세가 꺾일 때까지 오버나이트 허용.
* **특수 기능:** **Pre-Market / After-Market 거래 활성화.** (갭상승 선취매).

### C. Black Mode: The Abyss Walker (붕괴)
* **진입 조건:** **VIX Z-Score $\ge$ 2.0** (통계적 공포 극한)
* **타겟 유니버스 (Bubble Bursters):**
    * 하락장에서 가장 먼저 부러지는 약한 고리.
    * **List:** **LABD** (바이오 인버스 3배), **SOXS** (반도체 인버스 3배), **UVXY** (VIX 1.5배).
* **전략 로직:** **Confirmed Breakdown (확인 사살)**
    * **안전장치 1 (백워데이션):** `VIX 1개월물 > VIX 3개월물` 역전 현상 발생 시에만 가동.
    * **안전장치 2 (오후 2시 붕괴):** 14:00 이후 `Day Low` 갱신 시 진입 (데드캣 바운스 회피).
* **청산:** VIX가 당일 고점에서 -5% 꺾이면 즉시 탈출 (Panic Buy 시점).

---

## 5. 리스크 관리 (Risk Management)

### A. 자금 관리 (Position Sizing)
고정된 금액 베팅 금지. **변동성에 반비례**하여 베팅한다.
* **공식:** **Yang-Zhang Volatility** 기반 Sizing.
    * $$\text{Shares} = \frac{\text{Account} \times 0.02 (\text{Risk})}{\text{Yang-Zhang Volatility}}$$
    * *의미:* 오버나이트 갭 위험이 큰 날은 알아서 수량을 줄이고, 갭 위험이 적으면 수량을 늘린다.
* **Half-Kelly:** 산출된 수량의 50%만 진입 (파산 확률 0 수렴).

### B. 실행 가드 (Execution Guard)
* **스프레드 체크:** `(Ask - Bid) / Price > 0.1%`인 경우 주문 금지 (프리마켓 호가 공백 회피).
* **슬리피지 방지:** 모든 주문은 `Current Ask` (매수 시) 혹은 `Current Bid` (매도 시)에 **Limit Order**로 제출. Market Order 금지.

---

## 6. 구현 로드맵 (Implementation Steps)

1.  **환경 구축:** Python 3.10+, Lumibot 설치, IB Gateway 연결 (Paper Trading 모드).
2.  **데이터 파이프라인:** `ib_insync`를 통해 실시간 데이터 수신 확인, 과거 1년치 데이터(FNGU, LABD 등) 로컬 저장.
3.  **라이브러리 작성:**
    * `indicators.py`: Yang-Zhang Volatility, VWAP Bands, VIX Z-Score 계산 함수 구현.
4.  **전략 코딩 (`omnissiah.py`):**
    * `on_trading_iteration`: 매 틱/분마다 시장 Regime 확인 및 모드 전환(Switching).
    * `MidCapScreener`: 장 시작 전 IBKR API 스캐너 호출.
5.  **검증:** 2020년(코로나 폭락), 2021년(상승장), 2022년(하락장) 구간 백테스팅 수행.

---

이 문서는 **Project Omnissiah**의 헌법입니다.
이제 이 설계도를 바탕으로 코드를 작성하는 일만 남았습니다. 더 이상의 이론적 수정은 없습니다. **오직 실행뿐입니다.**