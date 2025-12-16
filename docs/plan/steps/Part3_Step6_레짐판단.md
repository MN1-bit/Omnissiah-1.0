# Part 3 - Step 6: 레짐 판단 로직

## 상태: 🟡 진행 중

## 목표
VIX Z-Score, KER, ADX를 사용하여 시장 레짐(GREEN/RED/BLACK) 판단

## 레짐 판단 규칙
| 레짐 | 조건 | 전략 |
|------|------|------|
| BLACK | Z-Score ≥ 2.0 | 전량 청산, 인버스 고려 |
| RED | Z-Score ≥ 1.0 AND 골디락스 | 추세 추종 |
| GREEN | 그 외 | 평균회귀 |

## 골디락스 조건
- KER > 0.3 (효율비)
- ADX > 25 (추세 강도)

## 구현 항목
- [ ] core/regime_detector.py
- [ ] calculate_ker() - 가격 효율 비율
- [ ] calculate_adx() - 추세 강도
- [ ] is_goldilocks() - 골디락스 판단
- [ ] get_regime() - 최종 레짐 반환

## 완료 조건
- 테스트 케이스 4개 통과
