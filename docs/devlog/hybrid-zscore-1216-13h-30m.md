# 하이브리드 Z-Score 업데이트 구현 완료

## 완료 시간: 2024-12-16 13:30

## 수정된 파일

### 1. core/market_data.py
**추가된 캐싱 변수:**
```python
self._cached_mean: Optional[float] = None
self._cached_std: Optional[float] = None
self._cache_date: Optional[datetime] = None
self._last_vix: float = 0.0
self.VIX_CHANGE_THRESHOLD = 0.5
```

**추가된 메서드:**
| 메서드 | 기능 |
|--------|------|
| `_refresh_cache_if_needed()` | 일봉 통계 캐시 갱신 (1일 1회) |
| `calculate_z_score_hybrid()` | 캐시 + 실시간 VIX Z-Score |
| `should_update_on_vix_change()` | VIX ±0.5pt 변동 감지 |
| `get_recommended_interval()` | Z-Score 기반 주기 권장 |

### 2. main.py
**하이브리드 타이머 설정:**
```python
BASE_INTERVAL = 5000   # 기본 5초
FAST_INTERVAL = 1000   # 빠른 1초
Z_THRESHOLD = 1.0      # 전환 임계값
```

**추가된 메서드:**
| 메서드 | 기능 |
|--------|------|
| `_adjust_timer_interval()` | Z-Score에 따른 동적 주기 조절 |

## 동작 방식
```
┌─────────────────────────────────────────────────┐
│ 일봉 통계 (126일)  →  캐싱 (1일 1회)            │
│ 현재 VIX           →  5초 기본                  │
│ |Z-Score| >= 1.0   →  1초 주기로 전환           │
└─────────────────────────────────────────────────┘
```

## 테스트 결과
- GUI 정상 실행
- 하이브리드 루프 시작 메시지 확인
- 동적 주기 조절 동작 확인 예정
