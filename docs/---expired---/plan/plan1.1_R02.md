# Project Omnissiah: 개발자 가이드
**Version 1.1 R02**

> 이 문서는 **사람(개발자)이 알아야 할 개발 과정과 배경 지식**을 담고 있습니다.  
> AI 프롬프트는 `docs/prompt/` 폴더에 별도 관리됩니다.

---

## 1. 프로젝트 개요

### 1.1 목표
- **기관(HFT)과 속도 경쟁 포기** → 구조적 틈새 공략
- 시장 레짐(Regime)에 따른 **'카멜레온 전략'** 자동화
- 100% Vibe Coding으로 AI Agent를 통해 구현

### 1.2 핵심 철학
| 원칙 | 의미 |
|------|------|
| **예측보다 대응** | 시장 예측 모델 사용 안 함. 현재 상태 감지 후 대응 |
| **속도 경쟁 포기** | ms 단위 최적화 불필요. 분/시간 단위 의사결정 |
| **자본 보존 우선** | 수익보다 생존. 모든 주문은 RiskManager 통과 필수 |
| **단순함의 가치** | 블랙박스 모델 지양. 해석 가능한 규칙 기반 |

---

## 2. 시스템 아키텍처

### 2.1 기술 스택
```
Language:    Python 3.10+
Framework:   Lumibot
Broker:      Interactive Brokers (IBKR)
Indicators:  pandas-ta
GUI:         PyQt6 (Phase 6)
```

### 2.2 모듈 구조
```
omnissiah/
├── core/
│   ├── regime_detector.py    # 레짐 탐지 (VIX, KER, ADX)
│   ├── risk_manager.py       # 킬 스위치, 포지션 사이징
│   └── data_manager.py       # 데이터 파이프라인
├── strategy/
│   ├── green_mode.py         # 평온장 (VWAP Mean Reversion)
│   ├── red_mode.py           # 추세장 (3x 레버리지)
│   └── black_mode.py         # 위기 (현금화/인버스)
├── gui/                      # Phase 6
├── llm/                      # Phase 6
└── main.py                   # OmnissiahStrategy
```

### 2.3 데이터 흐름
```
IBKR API → DataManager → RegimeDetector → Mode Selection
                ↓                              ↓
           Indicators                   Strategy Module
                ↓                              ↓
           Screener ─────────────────→ Signal Generation
                                              ↓
                                        RiskManager
                                              ↓
                                       Order Execution
```

---

## 3. 레짐(Regime) 시스템 이해

### 3.1 VIX Z-Score
- **공식:** Z = (VIX현재 - VIX평균) / VIX표준편차
- **Window:** 126일 (6개월)
- **해석:**
  - Z < 1.0 → 평온 (Green Mode)
  - 1.0 ≤ Z < 2.0 → 변동성 확대 (Red Mode 가능)
  - Z ≥ 2.0 → 위기 (Black Mode)

### 3.2 골디락스 존 (Goldilocks Zone)
**레버리지 전략 허용 조건:**
- **KER > 0.3** (추세의 효율성)
- **ADX > 25** (추세의 강도)
- 두 조건 모두 충족 시에만 3x 레버리지 허용

### 3.3 킬 스위치 발동 조건
| 조건 | 기준 | 동작 |
|------|------|------|
| VIX 백워데이션 | VIX_1M > VIX_3M | 전체 청산 |
| 국채 급등 | TNX 5일 변동 > 5% | 롱 포지션 축소 |
| 신용 스프레드 | SPY↑ AND HYG/IEF↓ | 신규 진입 금지 |

---

## 4. 개발 Phase별 가이드

### Phase 1: 데이터 파이프라인 (Week 1-2)
**목표:** VIX 데이터 수집 및 Z-Score 계산

**구현 항목:**
- [ ] MarketDataManager 클래스
- [ ] VIX 현물/선물 수집
- [ ] 콘탱고/백워데이션 판정
- [ ] Z-Score 계산기

**검증:**
- 2020년 3월 데이터에서 백워데이션 정확 탐지
- API 연결 끊김 시 자동 재연결 확인

---

### Phase 2: 레짐 탐지 엔진 (Week 3-4)
**목표:** KER, ADX 계산 및 레짐 분류

**구현 항목:**
- [ ] RegimeDetectionEngine
- [ ] KER 계산 (20일)
- [ ] ADX 계산 (pandas-ta)
- [ ] 골디락스 존 판정
- [ ] Hysteresis (버퍼 0.15, 쿨다운 5봉)

**검증:**
- 골디락스 존에서만 TREND 반환
- 모드 전환 빈도 ≤ 2회/분

---

### Phase 3: 리스크 관리 (Week 5-6)
**목표:** 킬 스위치 및 포지션 사이징

**구현 항목:**
- [ ] RiskManager 클래스
- [ ] 킬 스위치 3종 (VIX, TNX, Credit)
- [ ] Yang-Zhang 포지션 사이징
- [ ] Daily/Weekly Loss Limit

**검증:**
- RiskManager 우회 경로 없음
- 2020년 3월 킬 스위치 작동 확인

---

### Phase 4: 전략 모듈 (Week 7-9)
**목표:** 3가지 모드별 전략 구현

| 모드 | 전략 | 타겟 |
|------|------|------|
| Green | VWAP Mean Reversion | High Beta Mid-Caps |
| Red | Trend Following | FNGU, SOXL, TQQQ |
| Black | 현금화/인버스 | LABD, SOXS |

**검증:**
- 각 전략 독립 테스트 통과
- 인버스 보유 3일 제한 작동

---

### Phase 5: 통합 및 백테스팅 (Week 10-12)
**목표:** 메인 컨트롤러 및 검증

**백테스트 구간:**
| 구간 | 기간 | 목적 |
|------|------|------|
| COVID Crash | 2020.02-04 | Black Mode 검증 |
| Bull Run | 2020.05-2021.11 | Red Mode 검증 |
| Bear Market | 2022.01-10 | 모드 전환 검증 |
| Recovery | 2023 전체 | Green Mode 검증 |

**성과 목표:**
- Sharpe ≥ 1.5
- MaxDD ≤ 25%
- 각 구간 Sharpe ≥ 1.0

---

### Phase 6: GUI & LLM (Week 13-16)
**목표:** 모니터링 및 분석 도구

**GUI 패널:**
- Regime Status (Z-Score 게이지)
- Position 현황
- Strategy Monitor (내부 상태)
- LLM Chat

**LLM 역할 (Phase 1):**
- 분석, 설명, 리포트만
- 전략 개입 금지
- 읽기 전용 접근

---

## 5. 오류 상황 대응

### 5.1 AI가 설계 이탈 시
1. 현재 변경사항 버리기 (git stash)
2. 위반된 원칙 파악
3. `docs/prompt/AGENTS.md` 재주입
4. 더 구체적인 지시로 재요청

### 5.2 할루시네이션 징후
- 존재하지 않는 API 호출
- 요청하지 않은 복잡한 기능 추가
- "더 나은 방법"이라며 원본 설계 변경

**대응:** 해당 코드 삭제 → 공식 문서 링크와 함께 재요청

---

## 6. 참조 문서

| 문서 | 용도 |
|------|------|
| `docs/plan/plan1.0.md` | 원본 철학 |
| `docs/plan/plan1.0_R01.md` | 세부 로직 |
| `docs/ref/2고알파*.md` | 전략 수학 |
| `docs/ref/3바이브코딩*.md` | 구현 패턴 |
| `docs/prompt/AGENTS.md` | AI 규칙 (프롬프트 주입) |
| `docs/prompt/PHASE_GUIDE.md` | Phase별 AI 지시 |

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.1 R02 | 2024-12-16 | R01에서 사람용 가이드 분리 |
