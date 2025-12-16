# Z-Score 업데이트 주기 최적화 연구

## 연구 일자: 2024-12-16

## 현재 상태
- **업데이트 방식:** 1초 간격 QTimer 폴링
- **문제점:** 
  - Z-Score는 일봉 기반이므로 1초마다 변하지 않음
  - 불필요한 DB 쿼리 및 CPU 사용

---

## 대안 분석

### 1. 이벤트 기반 업데이트

#### 개념
VIX 가격이 실제로 변경될 때만 업데이트

#### 구현 방법
```python
# IBKR 실시간 시세 이벤트
self.ib.reqMktData(vix_contract)
self.ib.pendingTickersEvent += self._on_vix_tick

def _on_vix_tick(self, tickers):
    for ticker in tickers:
        if ticker.contract.symbol == "VIX":
            self._update_z_score(ticker.last)
```

#### 장점
- VIX 변동 시에만 계산
- 실시간 반응성

#### 단점
- IBKR 실시간 시세 구독 필요
- 시세 데이터 제한 (무료 계정 제한)

---

### 2. 동적 주기 방식

#### 개념
시장 상황에 따라 업데이트 주기 자동 조절

#### 구현 방법
```python
class DynamicTimer:
    def __init__(self):
        self.base_interval = 5000  # 5초 기본
        
    def get_interval(self, z_score: float) -> int:
        if abs(z_score) >= 1.5:
            return 1000   # 고변동성: 1초
        elif abs(z_score) >= 1.0:
            return 3000   # 중간: 3초
        else:
            return 10000  # 저변동성: 10초
```

#### 규칙
| Z-Score 범위 | 업데이트 주기 | 이유 |
|--------------|--------------|------|
| \|Z\| ≥ 1.5 | 1초 | 레짐 전환 임박, 빠른 반응 필요 |
| \|Z\| ≥ 1.0 | 3초 | 경계 상태 모니터링 |
| \|Z\| < 1.0 | 10초 | 안정적, 빈번한 업데이트 불필요 |

#### 장점
- 상황에 맞는 반응성
- 리소스 효율적

#### 단점
- 구현 복잡도 증가
- 주기 전환 시 일시적 불연속

---

### 3. 하이브리드 방식 (권장)

#### 개념
기본 주기 + 이벤트 트리거

#### 구현 방법
```python
class HybridUpdater:
    def __init__(self):
        # 기본 5초 주기
        self.timer = QTimer()
        self.timer.setInterval(5000)
        self.timer.timeout.connect(self._scheduled_update)
        
        # 가격 변동 임계값
        self.last_vix = 0.0
        self.threshold = 0.5  # 0.5pt 이상 변동 시
    
    def _on_vix_price(self, price: float):
        """가격 변동 시 즉시 업데이트"""
        if abs(price - self.last_vix) >= self.threshold:
            self._update_z_score()
            self.last_vix = price
    
    def _scheduled_update(self):
        """정기 업데이트 (백업)"""
        self._update_z_score()
```

#### 장점
- VIX 급변 시 즉시 반응
- 정기 업데이트로 안정성 보장
- 리소스 효율적

#### 단점
- 두 가지 로직 관리 필요

---

## 현재 시스템 적용 권장사항

### 단기 (즉시 적용 가능)
1. **주기 증가:** 1초 → 5초로 변경
   - `ITERATION_INTERVAL = 5000`
   - 리소스 80% 절감

### 중기 (설계 변경)
2. **동적 주기 방식 도입**
   - Z-Score 임계값에 따른 주기 조절
   - 레짐 전환 임박 시에만 빠른 업데이트

### 장기 (IBKR 연동 완성 시)
3. **하이브리드 방식**
   - IBKR 실시간 VIX 시세 구독
   - 가격 변동 이벤트 + 정기 백업

---

## 결론

| 방식 | 복잡도 | 효율성 | 반응성 | 권장도 |
|------|--------|--------|--------|--------|
| 현재 (1초 폴링) | 낮음 | ❌ 낮음 | ✅ 높음 | ⭐ |
| 이벤트 기반 | 중간 | ✅ 높음 | ✅ 높음 | ⭐⭐⭐ |
| 동적 주기 | 중간 | ✅ 높음 | ✅ 적응형 | ⭐⭐⭐⭐ |
| 하이브리드 | 높음 | ✅ 최고 | ✅ 최고 | ⭐⭐⭐⭐⭐ |

**최종 권장:** 단기적으로 5초 주기로 변경 후, 동적 주기 방식 도입 검토
