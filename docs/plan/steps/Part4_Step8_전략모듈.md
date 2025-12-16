# Part 4 - Step 8: 횡보/상승/위기 전략 모듈

## 상태: ✅ 완료

## 목표
레짐별 전략 모듈 구현

## 전략 개요 (모드명 변경됨!)
| 전략 | 레짐 | 색상 | 접근법 |
|------|------|------|--------|
| 횡보 (green_mode.py) | Z < 1.0 | 🟡 Yellow | 평균 회귀 (VWAP 밴드) |
| 상승 (red_mode.py) | 골디락스 | 🔵 Cyan/Teal | 추세 추종 (돌파 진입) |
| 위기 (black_mode.py) | Z ≥ 2.0 | 🔴 Red | 방어 (청산 + 인버스) |

## 구현 항목
- [x] strategy/green_mode.py → 횡보 전략
- [x] strategy/red_mode.py → 상승 전략
- [x] strategy/black_mode.py → 위기 전략

## 모드명 매핑 (2024-12-16 변경)
| 기존 코드 | 신규 이름 | 파일명 (유지) |
|----------|----------|--------------|
| GREEN | 횡보 | green_mode.py |
| RED | 상승 | red_mode.py |
| BLACK | 위기 | black_mode.py |

## 핵심 규칙
⚠️ 모든 주문은 반드시 `approve_order()` 호출 필수!

## 완료 조건
- [x] 각 전략 테스트 통과
- [x] approve_order() 우회 없음
