# Part 7 - Step 16.6: 주문 및 포지션 패널

## 상태: 🔴 대기

## 목표
미체결 주문(Open Orders)과 현재 포지션(Positions) 패널을 대시보드에 추가

## 구현 항목

### 1. gui/order_panel.py 생성 (신규)

#### OpenOrdersPanel 클래스
- [ ] QTableWidget 기반 미체결 주문 표시
- [ ] 컬럼: 주문ID, 시간, 심볼, 방향, 수량, 가격, 상태
- [ ] 주문 취소 버튼
- [ ] OrderExecutor.get_open_orders()와 연동

#### PositionsPanel 클래스
- [ ] QTableWidget 기반 현재 포지션 표시
- [ ] 컬럼: 심볼, 수량, 평균가, 현재가, 손익, 손익%
- [ ] 손익 색상 (이익: 초록, 손실: 빨강)
- [ ] OrderExecutor.get_positions()와 연동

### 2. 레이아웃 업데이트

**현재:**
```
[상태] | [차트      ]
[로그] | [거래내역  ]
```

**변경 후:**
```
[상태     ] | [차트          ]
[주문/포지션] | [거래내역      ]
[로그     ] | (하단으로 이동) |
```

or 탭 방식:
```
[상태] | [차트]
       | [탭: 거래내역 | 주문 | 포지션]
[로그]
```

### 3. dashboard.py 수정
- [ ] 패널 추가
- [ ] 레이아웃 재구성

### 4. main.py 수정
- [ ] 주기적 업데이트 (1초 간격)
- [ ] OrderExecutor와 연동

## 시그널 연결

| 소스 | → | 타겟 |
|------|---|------|
| OrderExecutor.order_placed | → | OpenOrdersPanel.add_order() |
| OrderExecutor.order_filled | → | OpenOrdersPanel.remove_order() |
| OrderExecutor.order_cancelled | → | OpenOrdersPanel.remove_order() |
| OrderExecutor.position_update | → | PositionsPanel.update() |

## 데이터 구조

### Open Order
```python
{
    "order_id": int,
    "time": datetime,
    "symbol": str,
    "action": "BUY" | "SELL",
    "quantity": int,
    "price": float,
    "status": "PENDING" | "SUBMITTED" | "PARTIAL"
}
```

### Position
```python
{
    "symbol": str,
    "quantity": int,
    "avg_price": float,
    "current_price": float,
    "pnl": float,
    "pnl_pct": float
}
```

## 완료 조건
- 미체결 주문 실시간 표시
- 현재 포지션 실시간 표시
- 손익 색상 구분
- 주문 취소 기능
