# Project Omnissiah: Vibe Coding Master Plan
**Version 1.1 R01 (Revision 1)**

> 이 문서는 AI Agent (Google Antigravity)를 통한 100% Vibe Coding으로 Project Omnissiah를 구현하기 위한 마스터 플랜입니다.  
> **목적:** AI의 할루시네이션 및 설계 이탈(폭주) 방지, 원본 철학과의 정합성 유지

---

## 1. 문서의 목적 및 구조

### 1.1 이 문서가 필요한 이유

Vibe Coding은 강력하지만, AI가 다음과 같은 방식으로 "폭주"할 수 있습니다:

| 폭주 유형 | 예시 |
|----------|------|
| **할루시네이션** | 존재하지 않는 API 함수 호출, 잘못된 라이브러리 사용법 |
| **과도한 창의성** | 요청하지 않은 복잡한 기능 추가, 과최적화된 전략 로직 |
| **설계 이탈** | 원본 철학(예측 → 대응)과 다른 예측 모델 도입 |
| **컨텍스트 손실** | 장기 세션에서 이전 결정사항 망각 |

이 문서는 **AI에게 제공되는 지속적인 컨텍스트**로서, 모든 구현 단계에서 참조되어야 합니다.

### 1.2 문서 구조

```
1. 서론 및 목적
2. 불변 원칙 (Immutable Principles) ← AI가 절대 위반 불가
3. 핵심 검증 체크포인트 ← 각 단계별 철학 정합성 확인
4. 단계별 구현 가이드 ← Phase 1~6 상세 지침
5. AI 지시 템플릿 (Prompt Templates)
6. 오류 복구 프로토콜
7. 참조 문서 및 체크리스트
```

---

## 2. 불변 원칙 (Immutable Principles)

> **이 원칙들은 프로젝트 전체에서 절대 위반할 수 없습니다.**
> AI 에이전트는 모든 코드 작성 시 이 원칙을 준수해야 합니다.

### 2.1 핵심 철학 원칙

| ID | 원칙 | 설명 | 위반 시 결과 |
|----|------|------|-------------|
| **P-01** | **예측보다 대응** | 시장을 예측하려 하지 않는다. 현재 상태(Regime)를 감지하고 대응한다 | 예측 모델(LSTM, Prophet 등) 도입 금지 |
| **P-02** | **속도 경쟁 포기** | HFT와 속도로 경쟁하지 않는다. 분/시간 단위 의사결정 | ms 단위 최적화 불필요 |
| **P-03** | **자본 보존 우선** | 수익보다 생존이 우선이다 | 모든 매수 로직은 RiskManager 승인 필수 |
| **P-04** | **단순함의 가치** | 복잡한 블랙박스 모델 지양, 해석 가능한 규칙 기반 | 딥러닝 전략 모델 금지 |

### 2.2 기술 구현 원칙

| ID | 원칙 | 구현 지침 |
|----|------|----------|
| **T-01** | **Look-ahead Bias 금지** | 백테스팅 시 미래 데이터 참조 절대 불가. 벡터화 연산 지양, 이벤트 기반 루프 사용 |
| **T-02** | **방어적 코딩** | 모든 API 호출에 try-except + Exponential Backoff. NaN/None 체크 필수 |
| **T-03** | **킬 스위치 필수** | 모든 Strategy 클래스는 매 tick마다 `check_kill_switch()` 호출 |
| **T-04** | **지정가 주문만** | Market Order 사용 금지. 모든 주문은 Limit Order 또는 Marketable Limit |
| **T-05** | **부동소수점 안전** | 가격/수량 계산 시 `decimal.Decimal` 사용 권장 |

### 2.3 전략 파라미터 원칙

| 파라미터 | 허용 범위 | 근거 |
|----------|----------|------|
| **VIX Z-Score Window** | 126일 (6개월) ± 20% | 문서2, 문서3 합의값 |
| **KER 임계값** | 0.25 ~ 0.35 | 골디락스 존 진입 기준 |
| **ADX 임계값** | 20 ~ 30 | 추세 존재 판단 |
| **레버리지 최대 보유** | 3일 (인버스), 추세 지속 시 무제한 (정방향) | 변동성 항력 제어 |
| **Half-Kelly** | 50% 적용 | 파산 확률 0 수렴 |

---

## 3. 핵심 검증 체크포인트

> 각 구현 단계 완료 후, 아래 체크포인트를 통해 **원본 설계와의 정합성**을 검증합니다.

### 3.1 Phase 완료 시 필수 검증

```python
# AI 에이전트가 각 Phase 완료 시 스스로 확인해야 할 질문들

VERIFICATION_QUESTIONS = {
    "Phase_1": [
        "VIX 선물 데이터 수집 시 롤오버가 올바르게 처리되는가?",
        "콘탱고/백워데이션 상태가 정확히 분류되는가?",
        "Z-Score 계산에 미래 데이터가 포함되지 않았는가?"
    ],
    "Phase_2": [
        "KER과 ADX가 골디락스 존(KER>0.3 AND ADX>25)을 정확히 탐지하는가?",
        "레짐 전환 시 Hysteresis가 적용되어 잦은 전환을 방지하는가?",
        "Green/Red/Black 모드 분류가 문서2의 정의와 일치하는가?"
    ],
    "Phase_3": [
        "킬 스위치가 TNX 급등, VIX 백워데이션 시 즉시 발동되는가?",
        "모든 매수 주문이 RiskManager를 통과하는가?",
        "포지션 사이징이 Yang-Zhang 변동성에 연동되는가?"
    ],
    "Phase_4": [
        "각 모드별 전략이 독립된 클래스로 분리되어 있는가?",
        "추세 추종 전략이 골디락스 존에서만 가동되는가?",
        "인버스 포지션 보유 기간이 3일로 제한되는가?"
    ],
    "Phase_5": [
        "백테스팅과 라이브 코드가 동일한 로직을 공유하는가?",
        "2020년 3월 데이터에서 킬 스위치가 올바르게 작동하는가?",
        "2022년 하락장에서 레버리지 비중이 자동 축소되는가?"
    ],
    "Phase_6": [
        "GUI에서 모든 전략 내부 상태를 실시간 확인할 수 있는가?",
        "LLM이 전략 의사결정에 개입하지 않고 분석/설명만 수행하는가?",
        "파라미터 변경 시 사용자 승인 절차가 있는가?"
    ]
}
```

### 3.2 철학 정합성 체크리스트

매 Phase 완료 시 아래 항목을 확인:

- [ ] **P-01 준수:** 코드에 "예측(predict)" 함수가 없는가?
- [ ] **P-02 준수:** 밀리초 단위 최적화 코드가 없는가?
- [ ] **P-03 준수:** RiskManager 없이 직접 주문하는 경로가 없는가?
- [ ] **P-04 준수:** 신경망/딥러닝 모델이 전략에 포함되지 않았는가?

---

## 4. 단계별 구현 가이드 (Phase 1~6)

### Phase 1: 데이터 파이프라인 구축 (Week 1-2)

#### 목표
- VIX 현물 및 선물 데이터 수집
- 기간 구조(Term Structure) 분석 모듈
- Z-Score 계산기

#### AI 지시 예시
```
[Antigravity Agent - Phase 1]

다음 모듈을 구현하세요:

1. MarketDataManager 클래스
   - IBKR API를 통해 VIX 현물(^VIX)과 선물(VX) 가격 수집
   - 선물 만기일 계산 및 롤오버 처리
   - 콘탱고/백워데이션 상태 반환

2. VixZScoreCalculator 클래스
   - 126일 롤링 윈도우로 Z-Score 계산
   - 절대로 미래 데이터를 참조하지 마세요 (Look-ahead Bias 금지)

참조할 문서:
- docs/ref/2고알파 전략 최적 복잡도 설계.md (2.1절)
- docs/plan/plan1.0_R01.md (3.1절)

규칙:
- 모든 함수에 type hints 필수
- API 호출 시 try-except + Exponential Backoff 적용
- AGENTS.md 규칙 준수
```

#### 검증 기준
- [ ] 콘탱고/백워데이션 분류 정확도 100% (과거 데이터 대조)
- [ ] Z-Score가 실시간으로 업데이트됨
- [ ] API 연결 끊김 시 자동 재연결

---

### Phase 2: 레짐 탐지 엔진 (Week 3-4)

#### 목표
- RegimeDetectionEngine 클래스
- KER, ADX 지표 계산
- 골디락스 존 탐지

#### AI 지시 예시
```
[Antigravity Agent - Phase 2]

RegimeDetectionEngine 클래스를 구현하세요.

기능:
1. KER (Kaufman Efficiency Ratio) 계산
   - 공식: KER = |Price_t - Price_t-n| / Σ|Price_i - Price_i-1|
   - 기간: 20일

2. ADX (Average Directional Index) 계산
   - pandas-ta 라이브러리 사용 가능

3. 골디락스 존 판정
   - 조건: KER > 0.3 AND ADX > 25
   - 이 조건 충족 시에만 "TREND" 레짐 반환

4. 레짐 전환 Hysteresis
   - 버퍼: 0.15
   - 쿨다운: 최소 5봉 유지 후 전환 가능

주의사항:
- VIX Z-Score와 결합하여 최종 레짐 결정
- Z >= 2.0 → CRISIS (킬 스위치 발동)
- 1.0 <= Z < 2.0 AND 골디락스 → TREND
- Z < 1.0 → CHOP 또는 NORMAL

참조: docs/ref/2고알파 전략 최적 복잡도 설계.md (2.2절)
```

#### 검증 기준
- [ ] KER>0.3 AND ADX>25 구간에서만 TREND 반환
- [ ] Hysteresis로 인해 1분 내 모드 전환 횟수 ≤ 2회
- [ ] VIX Z-Score 2.0 이상에서 즉시 CRISIS 반환

---

### Phase 3: 리스크 관리 및 킬 스위치 (Week 5-6)

#### 목표
- RiskManager 클래스
- 거시 경제 킬 스위치
- 포지션 사이징 (Yang-Zhang)

#### AI 지시 예시
```
[Antigravity Agent - Phase 3]

RiskManager 클래스를 구현하세요.

1. 킬 스위치 조건:
   - VIX 백워데이션 (VIX_1M > VIX_3M)
   - TNX(10년물 국채) 5일 변동 > 5%
   - 하이일드 스프레드 발산 (SPY↑ AND HYG/IEF↓)

2. 포지션 사이징:
   - Yang-Zhang Volatility 기반
   - 공식: Shares = (Account × 2%) / (YZ_Vol × Price)
   - Half-Kelly 적용 (50%만 진입)

3. 계좌 레벨 리스크:
   - Daily Loss Limit: 5%
   - Weekly Loss Limit: 10%
   - 연속 손실 3회 시 당일 거래 중단

중요:
- 모든 매수 주문은 반드시 이 클래스의 approve_order() 메서드를 통과해야 함
- approve_order()가 False 반환 시 주문 차단

참조: docs/plan/plan1.0_R01.md (6절 리스크 관리)
```

#### 검증 기준
- [ ] TNX 급등 시나리오에서 킬 스위치 발동 확인
- [ ] 2020년 3월 데이터 입력 시 즉시 CRISIS 모드 전환
- [ ] RiskManager 우회 경로 없음

---

### Phase 4: 전략 모듈 구현 (Week 7-9)

#### 목표
- GreenModeStrategy (VWAP Mean Reversion)
- RedModeStrategy (Trend Following)
- BlackModeStrategy (현금화/인버스)

#### AI 지시 예시
```
[Antigravity Agent - Phase 4]

세 가지 전략 모듈을 각각 독립된 클래스로 구현하세요.

1. GreenModeStrategy (Z < 1.0, 평온장)
   - VWAP ± 2.0 표준편차 밴드 사용
   - 하단 밴드 터치 시 매수, VWAP 복귀 시 매도
   - 타겟: High Beta Mid-Caps (COIN, PLTR 등)
   - Intraday Only (15:50까지 전량 청산)

2. RedModeStrategy (1.0 <= Z < 2.0, 골디락스)
   - 조건: KER > 0.3 AND ADX > 25
   - 3배 레버리지 ETF (FNGU, SOXL, TQQQ)
   - 전일 고가 돌파 시 진입
   - 피라미딩: 최대 3회 (50% → 30% → 20%)
   - 20일선 이탈 시 전량 청산

3. BlackModeStrategy (Z >= 2.0, 위기)
   - 즉시 모든 롱 포지션 청산
   - VIX 백워데이션 + 오후 2시 이후 저점 갱신 시에만 인버스 진입
   - 인버스 최대 보유: 3일
   - VIX 고점 대비 -5% 시 청산

반드시:
- 각 전략은 Strategy 베이스 클래스 상속
- execute(context) 메서드로 주문 실행
- 전략 내부에서 직접 주문하지 않고in RiskManager를 통해 주문

참조: 
- docs/plan/plan1.0_R01.md (4절 모드별 전략)
- docs/ref/3바이브코딩 시스템 구현 마스터 플랜.md (5.2절)
```

#### 검증 기준
- [ ] 각 전략이 독립적으로 테스트 가능
- [ ] RedMode가 골디락스 존 외에서 비활성화됨
- [ ] 인버스 포지션이 3일 초과 보유되지 않음

---

### Phase 5: 통합 및 백테스팅 (Week 10-12)

#### 목표
- OmnissiahStrategy 메인 컨트롤러
- 백테스팅 프레임워크
- 성과 분석

#### AI 지시 예시
```
[Antigravity Agent - Phase 5]

메인 전략 클래스와 백테스팅 환경을 구현하세요.

1. OmnissiahStrategy (Lumibot Strategy 상속)
   - on_trading_iteration에서:
     a. 먼저 check_kill_switch() 호출
     b. RegimeDetectionEngine으로 현재 레짐 판별
     c. 레짐에 따라 해당 전략 모듈 실행

2. 백테스팅 구간:
   - COVID Crash: 2020.02 ~ 2020.04
   - Bull Run: 2020.05 ~ 2021.11
   - Bear Market: 2022.01 ~ 2022.10
   - Recovery: 2023.01 ~ 2023.12

3. 성과 메트릭:
   - CAGR, Sharpe, MaxDD, Win Rate, Profit Factor
   - 목표: Sharpe >= 1.5, MaxDD <= 25%

주의:
- 백테스팅 코드와 라이브 코드는 동일한 로직 공유
- Look-ahead Bias 발생 여부 검증 필수
- 파라미터 민감도 분석 수행

참조: docs/plan/plan1.0_R01.md (7절 백테스팅 프레임워크)
```

#### 검증 기준
- [ ] 4개 구간 모두에서 Sharpe >= 1.0
- [ ] 2020년 3월에서 킬 스위치 작동 확인
- [ ] 2022년 하락장에서 레버리지 비중 자동 축소

---

### Phase 6: GUI 및 LLM 통합 (Week 13-16)

#### 목표
- GUI 모니터링 대시보드 (PyQt6)
- LLM 어시스턴트 통합

#### AI 지시 예시
```
[Antigravity Agent - Phase 6]

GUI와 LLM 통합 모듈을 구현하세요.

1. GUI (PyQt6):
   - Regime Status 패널 (VIX Z-Score 게이지)
   - Position 패널
   - Strategy Monitor (내부 상태 시각화)
   - LLM Chat 패널

2. LLM 통합:
   - 역할: 분석, 설명, 리포트 생성만
   - 전략 의사결정 개입 금지 (Phase 1)
   - Context Provider를 통해 읽기 전용 접근
   - Rate Limiting: 분당 10회

중요:
- LLM이 주문을 직접 실행할 수 없음
- LLM이 파라미터를 직접 변경할 수 없음
- 모든 LLM 상호작용 로깅

참조: 
- docs/plan/plan1.0_R01.md (10, 11절)
```

#### 검증 기준
- [ ] GUI에서 실시간 레짐 상태 확인 가능
- [ ] LLM이 "주문 실행" 요청 시 거부됨
- [ ] 파라미터 변경은 사용자 승인 후에만 적용

---

## 5. AI 지시 템플릿 (Prompt Templates)

### 5.1 새 모듈 생성 시

```
[Antigravity Agent - New Module]

모듈명: {MODULE_NAME}
파일 경로: omnissiah/{PATH}/{FILENAME}.py

요구사항:
{REQUIREMENTS}

참조 문서:
- docs/ref/2고알파 전략 최적 복잡도 설계.md
- docs/plan/plan1.0_R01.md

불변 원칙 확인:
- P-01 (예측보다 대응): {이 모듈이 예측 모델을 사용하는가? → No}
- T-01 (Look-ahead Bias): {미래 데이터 참조 없음 확인}
- T-02 (방어적 코딩): {try-except 적용}

완료 후:
- 단위 테스트 작성
- docs/plan/plan1.1_R01.md의 해당 Phase 검증 기준 확인
```

### 5.2 버그 수정 시

```
[Antigravity Agent - Bug Fix]

문제:
{PROBLEM_DESCRIPTION}

예상 원인:
{HYPOTHESIS}

수정 지침:
- 최소한의 변경으로 수정
- 기존 로직의 철학을 변경하지 않음
- 수정 후 기존 테스트 통과 확인

주의:
- 새로운 기능 추가 금지
- 문제와 무관한 코드 리팩토링 금지
```

### 5.3 코드 리뷰 요청 시

```
[Antigravity Agent - Code Review]

리뷰 대상: {FILE_PATH}

체크 항목:
1. 불변 원칙(P-01~P-04, T-01~T-05) 위반 여부
2. 참조 문서와의 정합성
3. 엣지 케이스 처리
4. 테스트 커버리지

문제 발견 시:
- 위반 내용과 위치를 명시
- 수정 제안 제시
```

---

## 6. 오류 복구 프로토콜

### 6.1 AI가 설계를 이탈했을 때

```
[복구 절차]

1. 즉시 중단
   - 현재 작업 중인 변경사항 버리기 (git stash 또는 discard)

2. 원인 파악
   - 어떤 불변 원칙이 위반되었는가?
   - 어느 시점에서 이탈이 시작되었는가?

3. 컨텍스트 재설정
   - AGENTS.md 다시 읽기
   - 해당 Phase의 참조 문서 다시 읽기
   - 이 문서(plan1.1_R01.md)의 해당 섹션 다시 읽기

4. 재시작
   - 이탈 직전 지점부터 다시 시작
   - 더 구체적인 지시와 함께 재요청
```

### 6.2 할루시네이션 감지 시

```
[할루시네이션 징후]

- 존재하지 않는 함수/클래스 호출
- 잘못된 라이브러리 API 사용
- 요청하지 않은 복잡한 기능 추가
- "이건 더 나은 방법입니다"라며 원본 설계 변경

[대응]

1. 해당 코드 즉시 삭제
2. 공식 문서 링크와 함께 재요청
   예: "ib_insync 공식 문서(https://ib-insync.readthedocs.io/)를 참조하여 
        올바른 API 사용법으로 재작성하세요"
3. 더 작은 단위로 분할하여 요청
```

---

## 7. 참조 문서 체크리스트

### 7.1 필수 참조 문서

| 문서 | 경로 | 참조 시점 |
|------|------|----------|
| **원본 설계** | `docs/plan/plan1.0.md` | 핵심 철학 확인 |
| **확장 설계 R01** | `docs/plan/plan1.0_R01.md` | 세부 로직 참조 |
| **전략 복잡도 설계** | `docs/ref/2고알파 전략 최적 복잡도 설계.md` | 지표/공식 확인 |
| **바이브코딩 마스터** | `docs/ref/3바이브코딩 시스템 구현 마스터 플랜.md` | 구현 패턴 참조 |
| **AGENTS.md** | 프로젝트 루트 | AI 규칙 (생성 필요) |

### 7.2 각 Phase별 참조 매핑

| Phase | 주요 참조 문서 섹션 |
|-------|-------------------|
| Phase 1 | 문서2: 2.1절 (VIX 기간구조), 문서3: 5.1절 |
| Phase 2 | 문서2: 2.2절 (KER/ADX), R01: 3절 |
| Phase 3 | 문서2: 4절 (킬 스위치), R01: 6절 |
| Phase 4 | 문서2: 3절 (섹터 로테이션), R01: 4절 |
| Phase 5 | 문서3: 5.4절 (검증), R01: 7절 |
| Phase 6 | R01: 10, 11절 (LLM, GUI) |

---

## 8. AGENTS.md 템플릿

> 프로젝트 루트에 `AGENTS.md` 파일을 생성하여 AI 에이전트에게 영구적인 지침을 제공합니다.

```markdown
# AGENTS.md - Project Omnissiah

## 1. Project Philosophy

**Capital Preservation First:** 수익보다 자본 보존이 우선이다. 
모든 매수 주문 로직은 RiskManager의 승인을 받아야 한다.

**Response over Prediction:** 시장을 예측하지 않는다. 
현재 레짐을 감지하고 대응한다. 예측 모델(ML/DL) 사용 금지.

**Defensive Coding:** IBKR API는 불안정하다고 가정한다.
모든 API 호출에 try-except + Exponential Backoff 적용.

## 2. Tech Stack

- **Language:** Python 3.10+
- **Framework:** Lumibot
- **Broker:** Interactive Brokers (IBKR)
- **Indicators:** pandas-ta
- **GUI:** PyQt6 (Phase 6)

## 3. Critical Rules

1. **Look-ahead Bias Zero Tolerance**
   - 백테스팅 시 미래 데이터 참조 금지
   - 벡터화 연산 대신 이벤트 루프 사용

2. **Kill Switch Integration**
   - 모든 Strategy는 매 tick마다 check_kill_switch() 호출
   - TNX/VIX 임계값 초과 시 즉시 liquidate_all()

3. **Order Safety**
   - Market Order 사용 금지
   - 모든 주문은 Limit Order

4. **Type Safety**
   - 모든 함수에 type hints 필수
   - 가격/수량 계산 시 decimal.Decimal 권장

## 4. Reference Documents

구현 시 항상 참조할 문서:
- docs/plan/plan1.1_R01.md (이 마스터 플랜)
- docs/plan/plan1.0_R01.md (세부 설계)
- docs/ref/2고알파 전략 최적 복잡도 설계.md (전략 철학)
```

---

## 9. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.1 R01 | 2024-12-16 | Antigravity | 바이브 코딩 마스터 플랜 초안 작성 |

---

**이 문서는 Project Omnissiah의 Vibe Coding 가이드입니다.**

AI 에이전트는 모든 구현 단계에서 이 문서를 참조하여:
1. 불변 원칙을 준수하고
2. 각 Phase의 검증 기준을 통과하며
3. 원본 설계 철학과의 정합성을 유지해야 합니다.

**"Trust but Verify"** - AI를 신뢰하되, 항상 검증하라.
