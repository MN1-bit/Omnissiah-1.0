# Part 2 - Step 5.5: 섹터 로테이션 & 종목 스캐너

## 상태: 🟡 진행 중

## 목표
상대 강도(Relative Strength) 기반 ETF 선정 및 성장주 스캐닝

## 핵심 기능
- [ ] UniverseSelector - 레버리지 ETF 모멘텀 스코어 계산
- [ ] GrowthStockScanner - Green Mode용 성장주 필터링
- [ ] 장 시작 전 1회 실행

## 모멘텀 스코어 공식
```
점수 = (1개월 수익률 × 0.5) + (3개월 수익률 × 0.3) + (6개월 수익률 × 0.2)
```

## ETF 유니버스
- TQQQ (나스닥 3x)
- SOXL (반도체 3x)
- TECL (기술 3x)
- FNGU (FANG+ 3x)

## 완료 조건
- 모멘텀 스코어 계산 성공
- 최고 스코어 ETF 반환
