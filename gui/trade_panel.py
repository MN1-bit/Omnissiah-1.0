"""
============================================
거래 내역 패널
============================================
QTableWidget 기반 거래 내역 표시 패널입니다.

기능:
- 실시간 거래 내역 표시
- 일일 요약 (총 거래, 손익, 승률)
- 손익 색상 구분
============================================
"""

# ============================================
# 필수 라이브러리 임포트
# ============================================
from datetime import datetime
from typing import List, Dict, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QLabel, QHeaderView, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont


class TradeHistoryPanel(QWidget):
    """
    거래 내역 패널
    
    실시간으로 거래 내역을 표시하고 일일 요약을 계산합니다.
    
    Signals:
        trade_selected(dict): 거래 선택 시 상세 정보 전달
    """
    
    trade_selected = pyqtSignal(dict)
    
    # === 색상 정의 ===
    COLOR_PROFIT = "#4CAF50"    # 초록 (이익)
    COLOR_LOSS = "#F44336"      # 빨강 (손실)
    COLOR_BUY = "#2196F3"       # 파랑 (매수)
    COLOR_SELL = "#FF9800"      # 주황 (매도)
    
    def __init__(self, parent=None) -> None:
        """초기화"""
        super().__init__(parent)
        
        # 거래 내역 저장
        self._trades: List[Dict] = []
        
        # UI 설정
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # === 제목 ===
        title = QLabel("📋 거래 내역")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        # === 일일 요약 ===
        summary_frame = QFrame()
        summary_frame.setStyleSheet(
            "background-color: #2d2d2d; border-radius: 4px; padding: 8px;"
        )
        summary_layout = QHBoxLayout(summary_frame)
        summary_layout.setContentsMargins(8, 4, 8, 4)
        
        self.total_trades_label = QLabel("거래: 0회")
        self.total_trades_label.setStyleSheet("color: #aaa;")
        summary_layout.addWidget(self.total_trades_label)
        
        self.net_pnl_label = QLabel("순손익: $0.00")
        self.net_pnl_label.setStyleSheet("color: #aaa;")
        summary_layout.addWidget(self.net_pnl_label)
        
        self.win_rate_label = QLabel("승률: 0%")
        self.win_rate_label.setStyleSheet("color: #aaa;")
        summary_layout.addWidget(self.win_rate_label)
        
        summary_layout.addStretch()
        layout.addWidget(summary_frame)
        
        # === 거래 테이블 ===
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "시간", "심볼", "방향", "수량", "가격", "손익"
        ])
        
        # 테이블 스타일
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                border: none;
                color: #ddd;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #3d3d3d;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: #aaa;
                padding: 6px;
                border: none;
            }
        """)
        
        # 헤더 설정
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemClicked.connect(self._on_item_clicked)
        
        layout.addWidget(self.table)
    
    # ============================================
    # 거래 추가
    # ============================================
    
    def add_trade(self, trade: Dict) -> None:
        """
        거래 추가
        
        Args:
            trade: {
                "time": datetime or str,
                "symbol": str,
                "action": "BUY" or "SELL",
                "quantity": int,
                "price": float,
                "pnl": float (optional)
            }
        """
        # 거래 저장
        self._trades.insert(0, trade)  # 최신이 맨 위
        
        # 테이블에 추가
        self._insert_row(0, trade)
        
        # 요약 업데이트
        self._update_summary()
    
    def _insert_row(self, row: int, trade: Dict) -> None:
        """테이블에 행 삽입"""
        self.table.insertRow(row)
        
        # 시간
        time_val = trade.get("time", datetime.now())
        if isinstance(time_val, datetime):
            time_str = time_val.strftime("%H:%M:%S")
        else:
            time_str = str(time_val)
        time_item = QTableWidgetItem(time_str)
        time_item.setFlags(time_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 0, time_item)
        
        # 심볼
        symbol_item = QTableWidgetItem(trade.get("symbol", "SPY"))
        symbol_item.setFlags(symbol_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 1, symbol_item)
        
        # 방향
        action = trade.get("action", "BUY")
        action_item = QTableWidgetItem(action)
        action_item.setFlags(action_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        action_color = self.COLOR_BUY if action == "BUY" else self.COLOR_SELL
        action_item.setForeground(QColor(action_color))
        self.table.setItem(row, 2, action_item)
        
        # 수량
        qty_item = QTableWidgetItem(str(trade.get("quantity", 0)))
        qty_item.setFlags(qty_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        qty_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.table.setItem(row, 3, qty_item)
        
        # 가격
        price = trade.get("price", 0)
        price_item = QTableWidgetItem(f"${price:.2f}")
        price_item.setFlags(price_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.table.setItem(row, 4, price_item)
        
        # 손익
        pnl = trade.get("pnl", 0)
        pnl_str = f"${pnl:+.2f}" if pnl != 0 else "-"
        pnl_item = QTableWidgetItem(pnl_str)
        pnl_item.setFlags(pnl_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        pnl_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        if pnl > 0:
            pnl_item.setForeground(QColor(self.COLOR_PROFIT))
        elif pnl < 0:
            pnl_item.setForeground(QColor(self.COLOR_LOSS))
        
        self.table.setItem(row, 5, pnl_item)
    
    def _update_summary(self) -> None:
        """일일 요약 업데이트"""
        total_trades = len(self._trades)
        
        # 손익 계산 (SELL 거래만)
        pnl_trades = [t for t in self._trades if t.get("action") == "SELL"]
        net_pnl = sum(t.get("pnl", 0) for t in pnl_trades)
        
        # 승률 계산
        wins = len([t for t in pnl_trades if t.get("pnl", 0) > 0])
        win_rate = (wins / len(pnl_trades) * 100) if pnl_trades else 0
        
        # 레이블 업데이트
        self.total_trades_label.setText(f"거래: {total_trades}회")
        
        self.net_pnl_label.setText(f"순손익: ${net_pnl:+.2f}")
        if net_pnl > 0:
            self.net_pnl_label.setStyleSheet(f"color: {self.COLOR_PROFIT};")
        elif net_pnl < 0:
            self.net_pnl_label.setStyleSheet(f"color: {self.COLOR_LOSS};")
        else:
            self.net_pnl_label.setStyleSheet("color: #aaa;")
        
        self.win_rate_label.setText(f"승률: {win_rate:.0f}%")
    
    def _on_item_clicked(self, item: QTableWidgetItem) -> None:
        """거래 클릭 시"""
        row = item.row()
        if 0 <= row < len(self._trades):
            self.trade_selected.emit(self._trades[row])
    
    # ============================================
    # 유틸리티
    # ============================================
    
    def clear(self) -> None:
        """테이블 초기화"""
        self._trades = []
        self.table.setRowCount(0)
        self._update_summary()
    
    def get_trades(self) -> List[Dict]:
        """모든 거래 반환"""
        return self._trades.copy()
    
    def get_daily_summary(self) -> Dict:
        """일일 요약 반환"""
        pnl_trades = [t for t in self._trades if t.get("action") == "SELL"]
        net_pnl = sum(t.get("pnl", 0) for t in pnl_trades)
        wins = len([t for t in pnl_trades if t.get("pnl", 0) > 0])
        win_rate = (wins / len(pnl_trades) * 100) if pnl_trades else 0
        
        return {
            "total_trades": len(self._trades),
            "net_pnl": net_pnl,
            "win_rate": win_rate,
            "wins": wins,
            "losses": len(pnl_trades) - wins
        }


# ============================================
# 테스트 코드
# ============================================
if __name__ == "__main__":
    import sys
    import random
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    panel = TradeHistoryPanel()
    panel.setMinimumSize(500, 400)
    panel.setWindowTitle("Trade History Test")
    panel.show()
    
    # 테스트 데이터 추가
    symbols = ["SPY", "QQQ", "AAPL", "MSFT"]
    
    for i in range(10):
        is_buy = i % 2 == 0
        trade = {
            "time": datetime.now(),
            "symbol": random.choice(symbols),
            "action": "BUY" if is_buy else "SELL",
            "quantity": random.randint(1, 10),
            "price": random.uniform(100, 500),
            "pnl": random.uniform(-50, 100) if not is_buy else 0
        }
        panel.add_trade(trade)
    
    print(f"Daily Summary: {panel.get_daily_summary()}")
    
    sys.exit(app.exec())
