# 🚀 Omnissiah: 바이브 코딩 실행 플레이북
**For Non-Coders | Version 2.0**

> **사용법:** 아래 단계(Step)를 순서대로 하나씩 복사하여 AI 채팅창에 붙여넣으세요.
> AI가 코드를 주면, 지정된 파일에 내용을 붙여넣고 저장하세요.

---

## 📋 전체 진행 상황

```
Part 1: 기초 공사 (Infrastructure)
  [ ] Step 1: 환경 설정 및 필수 라이브러리
  [ ] Step 2: IB Gateway 설정 (⚠️ 직접 해야 함)
  [ ] Step 3: GUI 뼈대 만들기

Part 2: 데이터와 연결 (Backend)
  [ ] Step 4: IBKR 브릿지 연결 (QThread)
  [ ] Step 5: 시장 데이터 수집기

Part 3: 두뇌 만들기 (Logic)
  [ ] Step 6: 레짐 판단 로직
  [ ] Step 7: 킬 스위치 & 리스크 매니저

Part 4: 전략 모듈
  [ ] Step 8: Green/Red/Black Mode 전략

Part 5: 통합
  [ ] Step 9: 메인 컨트롤러 통합
  [ ] Step 10: 테스트 및 검증
```

---

# Part 1: 기초 공사 (Infrastructure)

## [Step 0] Python 가상환경 (.venv) 생성

### 왜 필요한가?
가상환경은 프로젝트별로 독립된 Python 환경을 만듭니다.
다른 프로젝트와 패키지 충돌을 방지합니다.


터미널(PowerShell)을 열고 아래 명령어를 **순서대로** 입력하세요:

```powershell
# 1. 프로젝트 폴더로 이동
cd d:\Codes\Omnissiah-1.0

# 2. Python 버전 확인 (3.10 이상 필요)
python --version

# 3. 가상환경 생성 (.venv 폴더가 만들어짐)
python -m venv .venv

# 4. 가상환경 활성화 (프롬프트 앞에 (.venv) 표시됨)
.venv\Scripts\activate

# 5. pip 업그레이드
python -m pip install --upgrade pip
```

### ✅ 성공 확인:
```
(.venv) PS D:\Codes\Omnissiah-1.0>
```
→ 프롬프트 앞에 `(.venv)`가 보이면 성공!

### ❌ 문제 해결:
- "python을 찾을 수 없습니다" → Python 설치 필요 (python.org)
- "Scripts\activate 오류" → PowerShell 실행 정책 변경 필요:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

---

## [Step 1] 환경 설정 및 필수 라이브러리

> ⚠️ **주의:** Step 0을 먼저 완료하고, 가상환경이 활성화된 상태에서 진행하세요!

### AI에게 전달할 프롬프트:
```
프로젝트를 시작합니다.

1. `requirements.txt` 파일을 작성해주세요:
   포함: ib_insync, PyQt6, pyqt6-tools, qdarktheme, pandas, pandas-ta, yfinance, python-dotenv
   제외: tensorflow, torch, keras 등 ML 라이브러리

2. `.env.example` 파일 템플릿을 작성해주세요:
   - IB_HOST=127.0.0.1
   - IB_PORT=4002
   - IB_CLIENT_ID=1
   - IB_ACCOUNT=(계좌번호)
   - RISK_PER_TRADE=0.02
   - DAILY_LOSS_LIMIT=0.05

3. `.gitignore` 파일 작성 (.env 포함)

4. 프로젝트 폴더 구조 생성:
   Root Folder
   ├── .env
   ├── requirements.txt
   ├── main.py
   ├── core/
   ├── strategy/
   ├── gui/
   ├── tests/
   └── docs/
```

### ✅ 사용자가 직접 할 일:
1. AI가 생성한 `requirements.txt` 파일 확인
2. 터미널에서 패키지 설치:
   ```powershell
   # 가상환경 활성화 확인 (앞에 (.venv) 있어야 함)
   pip install -r requirements.txt
   ```
3. `.env.example`을 `.env`로 복사
4. `.env` 파일을 열어 본인의 IBKR 계좌 정보 입력 **(AI가 못해줍니다!)**

### ✅ 설치 확인:
```powershell
pip list
```
→ ib_insync, PyQt6, pandas 등이 보이면 성공!

---

## [Step 2] IBKR Gateway 설정 (⚠️ AI가 해결 불가 - 직접 해야 함!)

### 🔴 필수 사전 작업 (코딩 아님!)

> 이 단계는 **AI가 도와줄 수 없습니다.** 직접 하셔야 합니다.

1. **IB TWS 또는 IB Gateway 설치**
   - [IBKR 다운로드 페이지](https://www.interactivebrokers.com/en/trading/tws.php)에서 다운로드
   - TWS (Trader Workstation) 또는 IB Gateway 설치

2. **TWS 실행 및 로그인**
   - Paper Trading 계정으로 먼저 테스트 권장

3. **API 설정** (가장 중요!)
   - TWS 상단 메뉴: `Edit` → `Global Configuration`
   - 왼쪽 메뉴: `API` → `Settings`
   - ✅ **Enable ActiveX and Socket Clients** 체크
   - ✅ **Socket port:** `4002` (Paper)
   - ✅ **Allow connections from localhost only** 체크
   - ❌ **Read-Only API** 체크 해제

4. **연결 테스트 방법은 Step 4에서 진행**

### ⚠️ 중요 알림:
```
TWS 또는 IB Gateway가 실행 중이고 로그인된 상태여야만
Step 4 이후 코드가 작동합니다!

프로그램을 껐다 켜면 다시 로그인해야 합니다.
```

---

## [Step 3] GUI 뼈대 만들기 (빈 껍데기)

### AI에게 전달할 프롬프트:
```
`gui/dashboard.py`와 `main.py`를 작성하여 빈 GUI 창을 띄워봅시다.

요구사항:
- 창 크기: 1200x800
- 테마: qdarktheme 적용 (다크 모드)
- 레이아웃:
  - 좌측 패널 (200px):
    - 연결 상태: "🔴 연결 안됨" (빨간색)
    - 현재 모드: "⬜ 대기중"
    - 계좌 잔고: "$0.00"
  - 우측 상단: 실시간 로그창 (QTextEdit, 읽기 전용)
  - 우측 하단: 제어 버튼 (Start/Stop)

기능:
- Start 버튼 클릭 시 로그창에 "시스템 시작됨" 출력
- Stop 버튼 클릭 시 로그창에 "시스템 중지됨" 출력
- 상태 업데이트 메서드: update_connection_status(connected: bool)
- 로그 출력 메서드: add_log(message: str)

중요:
- time.sleep() 절대 사용 금지
- 모든 함수에 type hints와 한글 주석
- if __name__ == "__main__": 블록으로 테스트 가능하게
```

### ✅ 확인:
```powershell
python main.py
```
→ 검은색 멋진 창이 뜨면 성공!

---

# Part 2: 데이터와 연결 (Backend)

## [Step 4] IBKR 브릿지 연결 (스레딩 + 이벤트 기반)

### AI에게 전달할 프롬프트:
```
`core/bridge.py`를 작성합니다.

요구사항:
1. `ib_insync`를 사용하여 TWS/Gateway에 연결
2. **필수:** GUI가 멈추지 않도록 QThread를 사용하여 백그라운드 연결
3. 연결 성공/실패를 PyQt Signal로 main GUI에 전달
4. `.env` 파일에서 IB_HOST, IB_PORT, IB_CLIENT_ID 읽기

클래스 구조:
class IBKRBridge(QThread):
    connected = pyqtSignal(bool)
    account_update = pyqtSignal(dict)
    error = pyqtSignal(str)
    log_message = pyqtSignal(str)

이벤트 기반 업데이트 (5초 폴링 금지!):
- self.ib.orderStatusEvent += self._on_order_status
- self.ib.execDetailsEvent += self._on_execution
- self.ib.accountValueEvent += self._on_account_value

체결 시에만 잔고 업데이트:
- 주문 상태 변경 → 로그 출력
- 체결 발생 → 체결 정보 로그 + 잔고 업데이트
- 계좌 값 변경 → GUI 업데이트

중요:
- time.sleep() 절대 금지 → QThread.msleep() 사용
- util.startLoop() 호출 필수 (asyncio 이벤트 루프)
- 연결 실패 시 3회 재시도 (Exponential Backoff)
```

### ⚠️ 테스트 전 확인:
- IB Gateway가 실행 중인가?
- 로그인이 되어 있는가?
- API 포트가 4002(Paper)인가?

### ✅ 확인: 
GUI에서 "🟢 연결됨"으로 바뀌면 성공!

---

## [Step 5] 시장 데이터 수집기 (로컬 DB 캐싱)

### 왜 로컬 DB가 필요한가?
이동평균선, Z-Score, ATR 계산을 위해 **최소 252일치 과거 데이터**가 필요합니다.
매번 252일치를 가져오면 비효율적이므로, **로컬 DB에 저장하고 최신 데이터만 업데이트**합니다.

### AI에게 전달할 프롬프트:
```
`core/market_data.py`를 작성합니다.

클래스: MarketDataManager

=== 로컬 데이터베이스 구조 ===
- SQLite 사용 (data/market_data.db)
- 테이블: historical_prices (symbol, date, open, high, low, close, volume)
- 인덱스: (symbol, date) 복합 인덱스

메서드:

1. initialize_database() -> None
   - DB 파일 존재 여부 확인
   - 없으면: 테이블 생성 후 252일치 전체 다운로드 (최초 1회)
   - 있으면: 마지막 날짜 이후 데이터만 업데이트

2. update_historical_data() -> None (매일 장 시작 전 호출)
   - DB의 마지막 날짜 조회
   - 마지막 날짜 이후 ~ 오늘까지 데이터만 다운로드
   - 새 데이터를 DB에 INSERT
   - GUI 로그: "📊 데이터 업데이트: +N일 추가됨"

3. get_historical_prices(symbol: str, days: int = 252) -> pd.DataFrame
   - DB에서 최근 N일치 데이터 조회
   - DataFrame으로 반환 (지표 계산용)

4. get_vix_data() -> dict
   - VIX 현물: IBKR VIX 인덱스 (심볼: VIX, 거래소: CBOE)
   - VIX 선물: 근월물, 원월물 가격
   - 반환: {"spot": float, "front_month": float, "back_month": float}

5. get_vix_term_structure() -> str
   - "CONTANGO": 근월물 < 원월물
   - "BACKWARDATION": 근월물 > 원월물

6. calculate_z_score(window: int = 126) -> float
   - DB에서 VIX 히스토리 조회
   - 공식: Z = (현재VIX - 평균) / 표준편차

7. subscribe_realtime(symbols: list) -> None
   - 실시간 데이터 스트리밍 (당일 데이터)
   - 가격 업데이트 시 PyQt Signal로 GUI에 전달

=== 하이브리드 업데이트 방식 (신규) ===
1. 일봉 통계 캐싱:
   - 평균/표준편차를 1일 1회만 계산
   - _cached_mean, _cached_std, _cache_date
   
2. 실시간 Z-Score 계산:
   - 현재 VIX만 업데이트하여 Z-Score 계산
   - calculate_z_score_hybrid(realtime_vix: float) -> float
   
3. 동적 업데이트 주기:
   - 기본: 5초 간격
   - |Z-Score| >= 1.0: 1초 간격
   - VIX ±0.5pt 변동: 즉시 업데이트

=== 데이터 흐름 ===
1. 시스템 시작 → initialize_database() (DB 확인/생성)
2. 장 시작 전 → update_historical_data() (최신 데이터만 추가)
3. 장 중 → 일봉 통계 캐싱 (1일 1회)
4. 장 중 → 하이브리드 Z-Score (5초 기본 + 이벤트)

기술적 요구사항:
- IBKR API 실패 시 yfinance로 폴백(Fallback)
- 폴백 시 GUI 로그에 "⚠️ yfinance 폴백 사용 중" 표시
- DB 경로: data/market_data.db (프로젝트 내)
- DB 연결: check_same_thread=False (멀티스레드 허용)
- 데이터 수집은 QThread에서 비동기 실행

예외 처리:
- DB 손상 시 → 경고 후 삭제 및 재생성
- API 권한 없음 → yfinance 폴백
- 네트워크 오류 → 3회 재시도 (Exponential Backoff)
```

---

## [Step 5.5] 동적 유니버스 & 섹터 로테이션 (필수)

### 왜 필수인가?
설계 문서의 핵심인 **'상대 강도(Relative Strength)'** 기반 종목 선정입니다.
Red Mode에서 가장 강한 모멘텀의 ETF를 선택해야 수익이 극대화됩니다.

### AI에게 전달할 프롬프트:
```
`core/scanner.py`를 작성합니다.

설계 문서의 '고효율 종목 선정' 원칙을 구현합니다.

클래스: UniverseSelector

1. 레버리지 ETF 유니버스:
   TQQQ (나스닥 3x), SOXL (반도체 3x), TECL (기술 3x), FNGU (FANG+ 3x)

2. calculate_relative_strength(symbol: str) -> float
   - 모멘텀 스코어 공식:
     (1개월 수익률 × 0.5) + (3개월 수익률 × 0.3) + (6개월 수익률 × 0.2)
   - 수익률 = (현재가 - N개월전가격) / N개월전가격

3. get_target_etf() -> str
   - 위 4개 ETF 중 모멘텀 스코어 최고 1개 선정
   - Red Mode에서 이 ETF에 집중 투자

클래스: GrowthStockScanner (Green Mode 위성 포트폴리오용)

1. scan_growth_stocks() -> list
   다음 필터를 모두 통과한 종목 반환:
   
   - 필터 1 (재무): 영업이익(Operating Income) > 0
     → 적자 기업 제외 (좀비 기업 차단)
     
   - 필터 2 (성장): 매출성장률(Revenue Growth) 상위 20%
     → 고성장 기업만 선별
     
   - 필터 3 (수급): 당일 거래량 > 20일 평균 × 200%
     → 기관 자금 유입 신호
     
   - 필터 4 (기술): 52주 신고가 근접 또는 돌파
     → 상승 모멘텀 확인

2. 실행 시점:
   - 장 시작 전(Pre-market) 1회 실행
   - 결과를 self.target_symbols에 저장
   - GUI에 "오늘의 타겟: [종목리스트]" 표시

데이터 소스:
- IBKR Scanner API 우선 사용
- 불가 시 yfinance 재무제표로 폴백
```

---

# Part 3: 두뇌 만들기 (Logic)

## [Step 6] 레짐 판단 로직

### AI에게 전달할 프롬프트:
```
`core/regime_detector.py`를 작성합니다.

클래스: RegimeDetector

메서드:
1. calculate_ker(prices: list, period: int = 20) -> float
   - 공식: KER = |가격변화| / 총변화량합
   - 결과: 0~1 사이
   
2. calculate_adx(high, low, close, period=14) -> float
   - pandas-ta 사용
   
3. is_goldilocks(ker: float, adx: float) -> bool
   - True: KER > 0.3 AND ADX > 25
   
4. get_regime(z_score, ker, adx) -> str
   - "위기": z_score >= 2.0
   - "상승": z_score >= 1.0 AND is_goldilocks()
   - "횡보": 그 외

테스트 케이스 (if __name__ == "__main__"):
- get_regime(2.5, 0.4, 30) == "위기"
- get_regime(1.5, 0.4, 30) == "상승"
- get_regime(1.5, 0.2, 30) == "횡보"
- get_regime(0.5, 0.4, 30) == "횡보"
```

---

## [Step 7] 킬 스위치 & 리스크 매니저

### AI에게 전달할 프롬프트:
```
`core/risk_manager.py`를 작성합니다.

클래스: RiskManager

메서드:
1. check_kill_switch(vix_1m, vix_3m, tnx_change, spy_up, hyg_ief_down) -> str
   - "HALT_ALL": vix_1m > vix_3m (백워데이션)
   - "HALT_LONG": tnx_change > 0.05
   - "HALT_NEW": spy_up AND hyg_ief_down
   - "CLEAR": 그 외
   - 순서대로 체크 (첫 조건 우선)

2. calculate_yang_zhang_volatility(high, low, close, open, period=20) -> float
   - Yang-Zhang 변동성 공식 (가장 정확한 일중 변동성 측정)
   - 공식: σ² = σ_overnight² + k × σ_open² + (1-k) × σ_close²
   - pandas-ta 사용 가능

3. calculate_position_size(account, price, yang_zhang_vol) -> int
   - 동적 포지션 사이징 (계좌 잔고에 따라 자동 조절)
   - 공식: Shares = (Account × 2%) / (YZ_Vol × Price)
   - Half-Kelly 적용: 결과 × 0.5 (50%만 진입)
   - 최소 1주, 최대 계좌의 25%
   
   예시:
   - 계좌 $10,000, 가격 $100, 변동성 0.02
   - Shares = (10000 × 0.02) / (0.02 × 100) × 0.5 = 50주

4. apply_volatility_targeting(current_volatility, target_vol=0.20) -> float
   - 변동성 타겟팅 (포트폴리오 위험 관리)
   - 현재 변동성이 목표(20%)보다 높으면 비중 축소
   - 공식: Weight = Target_Vol / Current_Vol
   - 예: 변동성 40%면 비중을 50%로 축소

5. approve_order(kill_status, daily_loss, account) -> bool
   - False: kill_status != "CLEAR" OR daily_loss/account > 0.05
   - True: 그 외

6. log_decision(decision: str, reason: str) -> None
   - 모든 의사결정 로깅 (나중에 AI 피드백용)

중요: 모든 주문은 반드시 approve_order() 통과해야 함
```

---

# Part 4: 전략 모듈

## [Step 8] Green/Red/Black Mode 전략

### AI에게 전달할 프롬프트:
```
세 가지 전략 파일을 각각 생성하세요.

1. `strategy/green_mode.py` - GreenModeStrategy
   - 조건: Z-Score < 1.0
   - VWAP ± 2표준편차 밴드
   - BUY: price <= lower_band
   - SELL: price >= vwap
   - 15:50 전량 청산
   - approve_order() 호출 필수

2. `strategy/red_mode.py` - RedModeStrategy
   - 조건: 골디락스 존 (KER>0.3 AND ADX>25)
   - 전일 고가 돌파 진입
   - 피라미딩 최대 3회
   - MA20 이탈 청산
   - approve_order() 호출 필수

3. `strategy/black_mode.py` - BlackModeStrategy
   - 조건: Z-Score >= 2.0 또는 백워데이션
   - 기본: 전량 청산
   - 인버스 진입: 백워데이션 AND 오후2시 AND 신저점
   - 인버스 최대 3일 보유

각 파일에:
- type hints 필수
- if __name__ == "__main__": 테스트 블록
- approve_order() 우회 금지
```

---

# Part 5: 통합

## [Step 9] 메인 컨트롤러 통합

### AI에게 전달할 프롬프트:
```
`main.py`를 수정하여 모든 모듈을 통합합니다.

=== 하이브리드 업데이트 방식 ===

기본 루프 (5초 간격):
1. 킬 스위치 체크 (가장 먼저!)
2. GUI 킬 스위치 상태 업데이트
3. if kill_status != "CLEAR": black_mode.execute() 후 return
4. 일봉 통계 캐시 확인/갱신 (1일 1회)
5. 현재 VIX로 Z-Score 계산 (캐시된 mean/std 사용)
6. 레짐 판단
7. 해당 전략 실행

동적 주기 전환:
- |Z-Score| >= 1.0: 루프 주기 1초로 전환
- |Z-Score| < 1.0: 루프 주기 5초로 복귀

이벤트 트리거:
- VIX ±0.5pt 변동 시 즉시 Z-Score 재계산

중요:
- 메인 루프는 QTimer 사용 (5초 기본)
- 동적 주기: adjust_timer_interval(z_score)
- time.sleep() 절대 금지
- 일봉 통계는 캐싱 (1일 1회만 계산)
- 모든 상태 변경은 GUI에 반영
```

---

## [Step 10] 테스트 및 검증

### AI에게 전달할 프롬프트:
```
전체 시스템 테스트를 도와주세요.

확인 항목:
1. GUI가 멈추지 않음 (time.sleep 없음)
2. TWS 연결/해제 시 GUI 상태 반영
3. 킬 스위치가 가장 먼저 실행됨
4. 모든 주문이 approve_order() 통과
5. 로그에 모든 의사결정 기록됨

테스트 시나리오:
- TWS 꺼진 상태에서 시작 → "연결 실패" 메시지
- TWS 켠 후 시작 → "연결됨" 표시
- 1분간 GUI 멈춤 없이 데이터 업데이트
```

---

# 🆘 오류 발생 시 (Panic Button)

## 에러가 발생하면:

### 1. 터미널 에러 메시지 복사

### 2. AI에게 이렇게 말하세요:
```
[에러 발생]
아래 에러 메시지를 분석하고 수정해주세요.
수정된 **전체 파일 코드**를 다시 작성해주세요.

에러 메시지:
(여기에 붙여넣기)

관련 파일:
(어떤 파일인지 알려주기)
```

### 3. 수정된 코드를 받아서 파일 전체를 교체

---

# 💡 시니어 개발자의 조언

1. **IBKR 설정이 제일 어렵습니다**
   - 코딩보다 TWS API 설정 맞추는 게 더 힘듭니다
   - "IBKR TWS API 설정 방법" 유튜브/블로그 검색 추천

2. **욕심 버리기**
   - 처음 목표: "로그만 잘 찍히는 프로그램"
   - Step 9까지 가서 숫자가 실시간으로 바뀌면 성공!
   - 주문은 그 다음입니다

3. **AI 선택**
   - Claude 4.5 Opus 추천 (코딩 능력 최고)
   - Gemini 3도 괜찮음

4. **막히면**
   - 에러 메시지 전체를 AI에게 던지세요
   - "부분 수정"보다 "전체 파일 다시 작성" 요청

---

**행운을 빕니다! 🚀**
