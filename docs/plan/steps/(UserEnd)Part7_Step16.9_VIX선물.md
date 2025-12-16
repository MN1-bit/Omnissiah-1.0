# Part 7 - Step 16.9: VIX 선물 데이터 연동

## 상태: ✅ 완료

## 목표
IBKR에서 VIX 선물(VX) 실시간 데이터를 가져와 정확한 Term Structure 판단

## 현재 문제
```python
# core/market_data.py line 284-285
return {
    "front_month": spot or 0.0,  # 임시로 현물값 사용
    "back_month": spot or 0.0,   # 임시로 현물값 사용
}
```
- front_month, back_month 모두 동일한 현물값 사용
- 항상 BACKWARDATION 표시 (버그)

## 수정 파일
- `core/market_data.py` - VIX 선물 조회 메서드 추가
- `core/bridge.py` - VX 선물 구독 추가

## 구현 계획

### 1. VIX 선물 계약 정의
```python
from ib_insync import Future

# VX 선물 (CBOE VIX Futures)
vx_front = Future("VX", exchange="CFE", lastTradeDateOrContractMonth="YYYYMM")
vx_back = Future("VX", exchange="CFE", lastTradeDateOrContractMonth="YYYYMM")
```

### 2. 근월물/원월물 만기 계산
- VX 선물은 매월 셋째 주 수요일 만기
- 현재 날짜 기준으로 근월/원월 자동 계산

### 3. bridge.py에 VX 구독 추가
```python
def subscribe_vix_futures(self):
    # 근월, 원월 VX 선물 구독
    # price_update 시그널로 전달
```

### 4. market_data.py에서 실제 값 사용
```python
def get_vix_data(self):
    return {
        "spot": vix_spot,
        "front_month": vx_front_price,  # IBKR에서 수신
        "back_month": vx_back_price,    # IBKR에서 수신
    }
```

## User End 확인 필요
- [ ] IBKR 계정에서 CBOE One 시세 구독 확인
- [ ] Paper Trading에서 VX 선물 시세 수신 가능 여부 확인

## 완료 조건
- [ ] VX 선물 실시간 시세 수신
- [ ] Term Structure 정확하게 표시
- [ ] 킬 스위치 백워데이션 감지 정상 동작
