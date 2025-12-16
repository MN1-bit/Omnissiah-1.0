# Verification Checklist - AI Self-Check

> **각 Phase 완료 시 AI가 스스로 확인해야 할 질문**

---

## Philosophy Check (매 Phase)
- [ ] P-01: 코드에 "predict" 함수 없음?
- [ ] P-02: ms 단위 최적화 없음?
- [ ] P-03: RiskManager 우회 경로 없음?
- [ ] P-04: 신경망/딥러닝 없음?

---

## Phase 1 Check
- [ ] VIX 선물 롤오버 정확?
- [ ] 콘탱고/백워데이션 분류 정확?
- [ ] Z-Score에 미래 데이터 미포함?
- [ ] API 재연결 Exponential Backoff?

## Phase 2 Check
- [ ] KER>0.3 AND ADX>25 에서만 TREND?
- [ ] Hysteresis로 모드 전환 ≤ 2회/분?
- [ ] Z≥2.0 즉시 CRISIS?

## Phase 3 Check
- [ ] 모든 주문 approve_order() 통과?
- [ ] TNX 급등 시 킬 스위치?
- [ ] Yang-Zhang 포지션 사이징?

## Phase 4 Check
- [ ] 각 전략 독립 클래스?
- [ ] 골디락스 외 레버리지 비활성화?
- [ ] 인버스 3일 제한?
- [ ] Green Mode 15:50 청산?

## Phase 5 Check
- [ ] 백테스트/라이브 코드 동일?
- [ ] 2020.03 킬 스위치 작동?
- [ ] 2022 하락장 레버리지 축소?
- [ ] 모든 구간 Sharpe ≥ 1.0?

## Phase 6 Check
- [ ] GUI 실시간 레짐 표시?
- [ ] LLM 주문 실행 불가?
- [ ] 파라미터 변경 승인 절차?

---

## Error Recovery

### 설계 이탈 시
1. git stash (변경 버리기)
2. 위반 원칙 파악
3. AGENTS.md 재주입
4. 구체적 지시로 재요청

### 할루시네이션 징후
- 존재하지 않는 API 호출
- 요청 안 한 복잡한 기능
- "더 나은 방법" 주장하며 설계 변경

**대응:** 코드 삭제 → 공식 문서 링크와 재요청
