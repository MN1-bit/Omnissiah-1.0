# 모드명 전역 리팩토링: GREEN/RED/BLACK → 횡보/상승/위기

## 작업 시간: 2024-12-16 13:37

## 변경 개요
| 기존 | 신규 | 색상 | 전략 |
|------|------|------|------|
| GREEN | 횡보 | 🟡 Yellow (#FFD700) | 평균 회귀 (VWAP 밴드) |
| RED | 상승 | 🔵 Cyan/Teal (#00CED1) | 추세 추종 (골디락스) |
| BLACK | 위기 | 🔴 Red (#FF4444) | 방어 (청산 + 인버스) |

---

## 수정된 파일 상세

### 1. core/regime_detector.py
| 라인 | 변경 전 | 변경 후 |
|------|---------|---------|
| 50 | `self._current_regime: str = "GREEN"` | `self._current_regime: str = "횡보"` |
| 179 | `"BLACK", "RED", 또는 "GREEN"` | `"위기", "상승", 또는 "횡보"` |
| 183 | `regime = "BLACK"` | `regime = "위기"` |
| 184 | `⚫ BLACK 모드` | `🔴 위기 모드` |
| 188 | `regime = "RED"` | `regime = "상승"` |
| 189 | `🔴 RED 모드` | `🔵 상승 모드` |
| 193 | `regime = "GREEN"` | `regime = "횡보"` |
| 194 | `🟢 GREEN 모드` | `🟡 횡보 모드` |
| 222-226 | 테스트 케이스 | "위기", "상승", "횡보" 로 변경 |

### 2. gui/dashboard.py
| 라인 | 변경 전 | 변경 후 |
|------|---------|---------|
| 269 | `"GREEN", "RED", "BLACK"` | `"횡보", "상승", "위기"` |
| 272 | `"GREEN": ("🟢 GREEN", "#4ec9b0")` | `"횡보": ("🟡 횡보", "#FFD700")` |
| 273 | `"RED": ("🔴 RED", "#f14c4c")` | `"상승": ("🔵 상승", "#00CED1")` |
| 274 | `"BLACK": ("⚫ BLACK", "#808080")` | `"위기": ("🔴 위기", "#FF4444")` |
| 350 | `update_mode("GREEN")` | `update_mode("횡보")` |

### 3. main.py
| 라인 | 변경 전 | 변경 후 |
|------|---------|---------|
| 74 | `self._current_regime = "GREEN"` | `self._current_regime = "횡보"` |
| 206 | `self._current_regime = "BLACK"` | `self._current_regime = "위기"` |
| 207 | `update_mode("BLACK")` | `update_mode("위기")` |

### 4. docs/plan/STEP_BY_STEP_GUIDE.md
| 라인 | 변경 전 | 변경 후 |
|------|---------|---------|
| 410 | `"BLACK": z_score >= 2.0` | `"위기": z_score >= 2.0` |
| 411 | `"RED": z_score >= 1.0` | `"상승": z_score >= 1.0` |
| 412 | `"GREEN": 그 외` | `"횡보": 그 외` |
| 415-418 | 테스트 케이스 | 모두 한글명으로 변경 |

### 5. docs/plan/steps/Part4_Step8_전략모듈.md
- 제목 및 전체 내용 신규 한글 모드명으로 재작성
- 파일명 매핑 테이블 추가

---

## 테스트 결과
```
✅ get_regime(2.5, 0.4, 30) = 위기 (예상: 위기)
✅ get_regime(1.5, 0.4, 30) = 상승 (예상: 상승)
✅ get_regime(1.5, 0.2, 30) = 횡보 (예상: 횡보)
✅ get_regime(0.5, 0.4, 30) = 횡보 (예상: 횡보)
✅ get_regime(1.2, 0.35, 20) = 횡보 (예상: 횡보)
✅ 모든 테스트 통과!
```

---

## 유지된 항목 (파일명)
⚠️ 전략 파일명은 영어로 유지 (호환성)
- `strategy/green_mode.py` → 횡보 전략
- `strategy/red_mode.py` → 상승 전략
- `strategy/black_mode.py` → 위기 전략

---

## 문제 발생 시 롤백 방법
1. 위 테이블을 참고하여 역방향으로 수정
2. 또는 Git에서 이전 커밋으로 롤백
