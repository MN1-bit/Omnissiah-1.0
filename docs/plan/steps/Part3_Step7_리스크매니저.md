# Part 3 - Step 7: 킬 스위치 & 리스크 매니저

## 상태: 🟡 진행 중

## 목표
시장 위험 감지 및 포지션 사이징 로직 구현

## 핵심 기능
- [ ] check_kill_switch() - 킬 스위치 상태 확인
- [ ] calculate_yang_zhang_volatility() - 변동성 계산
- [ ] calculate_position_size() - Half-Kelly 포지션 사이징
- [ ] apply_volatility_targeting() - 변동성 타겟팅
- [ ] approve_order() - 주문 승인 (필수 게이트)
- [ ] log_decision() - 의사결정 로깅

## 킬 스위치 우선순위
1. HALT_ALL: VIX 백워데이션 (1M > 3M)
2. HALT_LONG: 금리 급등 (TNX > 5%)
3. HALT_NEW: 다이버전스 (SPY↑ + HYG/IEF↓)
4. CLEAR: 정상

## 완료 조건
- 모든 주문이 approve_order() 통과해야 함
