"""
============================================
주문 및 포지션 패널
============================================
미체결 주문과 현재 포지션을 표시합니다.

기능:
- OpenOrdersPanel: 미체결 주문 표시, 취소 기능
- PositionsPanel: 현재 포지션, 실시간 손익
============================================
"""

# ============================================
# 필수 라이브러리 임포트
# ============================================
from datetime import datetime
from typing import Dict, List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QLabel, QHeaderView, QPushButton,
    QFrame, QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor


class OpenOrdersPanel(QWidget):
    """
    미체결 주문 패널
    
    현재 대기 중인 주문을 표시하고 취소 기능을 제공합니다.
    
    Signals:
        cancel_requested(int): 주문 취소 요청 (주문 ID)
    """
    
    cancel_requested = pyqtSignal(int)
    
    # === 색상 정의 ===
    COLOR_BUY = "#2196F3"       # 파랑 (매수)
    COLOR_SELL = "#FF9800"      # 주황 (매도)
    COLOR_PENDING = "#FFC107"   # 노랑 (대기)
    COLOR_SUBMITTED = "#4CAF50" # 초록 (제출됨)
    
    def __init__(self, parent=None) -> None:
        """초기화"""
        super().__init__(parent)
        
        # 주문 저장소 {order_id: order_data}
        self._orders: Dict[int, Dict] = {}
        
        # UI 설정
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # === 제목 ===
        title = QLabel("📋 미체결 주문")
        title.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(title)
        
        # === 테이블 ===
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "주문ID", "시간", "심볼", "방향", "수량", "가격", "취소"
        ])
        
        # 테이블 스타일
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                border: none;
                color: #ddd;
                font-size: 11px;
            }
            QTableWidget::item { padding: 2px; }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: #aaa;
                padding: 4px;
                border: none;
                font-size: 11px;
            }
        """)
        
        # 헤더 설정
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        
        layout.addWidget(self.table)
    
    def add_order(self, order: Dict) -> None:
        """
        주문 추가
        
        Args:
            order: {
                "order_id": int,
                "time": datetime,
                "symbol": str,
                "action": "BUY" | "SELL",
                "quantity": int,
                "price": float
            }
        """
        order_id = order.get("order_id", 0)
        self._orders[order_id] = order
        self._refresh_table()
    
    def remove_order(self, order_id: int) -> None:
        """주문 제거"""
        if order_id in self._orders:
            del self._orders[order_id]
            self._refresh_table()
    
    def _refresh_table(self) -> None:
        """테이블 갱신"""
        self.table.setRowCount(len(self._orders))
        
        for row, (order_id, order) in enumerate(self._orders.items()):
            # 주문 ID
            id_item = QTableWidgetItem(str(order_id))
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, id_item)
            
            # 시간
            time_val = order.get("time", datetime.now())
            time_str = time_val.strftime("%H:%M:%S") if isinstance(time_val, datetime) else str(time_val)
            time_item = QTableWidgetItem(time_str)
            time_item.setFlags(time_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, time_item)
            
            # 심볼
            symbol_item = QTableWidgetItem(order.get("symbol", ""))
            symbol_item.setFlags(symbol_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 2, symbol_item)
            
            # 방향
            action = order.get("action", "BUY")
            action_item = QTableWidgetItem(action)
            action_item.setFlags(action_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            action_item.setForeground(QColor(self.COLOR_BUY if action == "BUY" else self.COLOR_SELL))
            self.table.setItem(row, 3, action_item)
            
            # 수량
            qty_item = QTableWidgetItem(str(order.get("quantity", 0)))
            qty_item.setFlags(qty_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 4, qty_item)
            
            # 가격
            price_item = QTableWidgetItem(f"${order.get('price', 0):.2f}")
            price_item.setFlags(price_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 5, price_item)
            
            # 취소 버튼
            cancel_btn = QPushButton("✕")
            cancel_btn.setMaximumWidth(30)
            cancel_btn.setStyleSheet("background-color: #c62828; padding: 2px;")
            cancel_btn.clicked.connect(lambda checked, oid=order_id: self.cancel_requested.emit(oid))
            self.table.setCellWidget(row, 6, cancel_btn)
    
    def clear(self) -> None:
        """모든 주문 제거"""
        self._orders = {}
        self.table.setRowCount(0)


class PositionsPanel(QWidget):
    """
    현재 포지션 패널
    
    보유 중인 포지션과 실시간 손익을 표시합니다.
    
    Signals:
        close_requested(str): 포지션 청산 요청 (심볼)
    """
    
    close_requested = pyqtSignal(str)
    
    # === 색상 정의 ===
    COLOR_PROFIT = "#4CAF50"   # 초록 (이익)
    COLOR_LOSS = "#F44336"     # 빨강 (손실)
    
    def __init__(self, parent=None) -> None:
        """초기화"""
        super().__init__(parent)
        
        # 포지션 저장소 {symbol: position_data}
        self._positions: Dict[str, Dict] = {}
        
        # UI 설정
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # === 제목 + 요약 ===
        header_layout = QHBoxLayout()
        
        title = QLabel("📦 현재 포지션")
        title.setStyleSheet("font-weight: bold; font-size: 12px;")
        header_layout.addWidget(title)
        
        self.total_pnl_label = QLabel("총 손익: $0.00")
        self.total_pnl_label.setStyleSheet("color: #aaa; font-size: 11px;")
        header_layout.addWidget(self.total_pnl_label)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # === 테이블 ===
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "심볼", "수량", "평균가", "현재가", "손익", "손익%"
        ])
        
        # 테이블 스타일
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                border: none;
                color: #ddd;
                font-size: 11px;
            }
            QTableWidget::item { padding: 2px; }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: #aaa;
                padding: 4px;
                border: none;
                font-size: 11px;
            }
        """)
        
        # 헤더 설정
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        
        layout.addWidget(self.table)
    
    def update_positions(self, positions: Dict[str, Dict]) -> None:
        """
        포지션 업데이트
        
        Args:
            positions: {
                "SPY": {
                    "quantity": int,
                    "avg_price": float,
                    "current_price": float,
                    "pnl": float,
                    "pnl_pct": float
                }
            }
        """
        self._positions = positions
        self._refresh_table()
    
    def update_position(self, symbol: str, data: Dict) -> None:
        """단일 포지션 업데이트"""
        if data.get("quantity", 0) == 0:
            if symbol in self._positions:
                del self._positions[symbol]
        else:
            self._positions[symbol] = data
        self._refresh_table()
    
    def _refresh_table(self) -> None:
        """테이블 갱신"""
        self.table.setRowCount(len(self._positions))
        
        total_pnl = 0.0
        
        for row, (symbol, pos) in enumerate(self._positions.items()):
            # 심볼
            symbol_item = QTableWidgetItem(symbol)
            symbol_item.setFlags(symbol_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            symbol_item.setFont(symbol_item.font())
            self.table.setItem(row, 0, symbol_item)
            
            # 수량
            qty = pos.get("quantity", 0)
            qty_item = QTableWidgetItem(str(qty))
            qty_item.setFlags(qty_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 1, qty_item)
            
            # 평균가
            avg_price = pos.get("avg_price", 0)
            avg_item = QTableWidgetItem(f"${avg_price:.2f}")
            avg_item.setFlags(avg_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            avg_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 2, avg_item)
            
            # 현재가
            current_price = pos.get("current_price", 0)
            current_item = QTableWidgetItem(f"${current_price:.2f}")
            current_item.setFlags(current_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            current_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 3, current_item)
            
            # 손익
            pnl = pos.get("pnl", 0)
            total_pnl += pnl
            pnl_item = QTableWidgetItem(f"${pnl:+.2f}")
            pnl_item.setFlags(pnl_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            pnl_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            pnl_item.setForeground(QColor(self.COLOR_PROFIT if pnl >= 0 else self.COLOR_LOSS))
            self.table.setItem(row, 4, pnl_item)
            
            # 손익%
            pnl_pct = pos.get("pnl_pct", 0)
            pct_item = QTableWidgetItem(f"{pnl_pct:+.2f}%")
            pct_item.setFlags(pct_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            pct_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            pct_item.setForeground(QColor(self.COLOR_PROFIT if pnl_pct >= 0 else self.COLOR_LOSS))
            self.table.setItem(row, 5, pct_item)
        
        # 총 손익 업데이트
        self.total_pnl_label.setText(f"총 손익: ${total_pnl:+.2f}")
        if total_pnl > 0:
            self.total_pnl_label.setStyleSheet(f"color: {self.COLOR_PROFIT}; font-size: 11px;")
        elif total_pnl < 0:
            self.total_pnl_label.setStyleSheet(f"color: {self.COLOR_LOSS}; font-size: 11px;")
        else:
            self.total_pnl_label.setStyleSheet("color: #aaa; font-size: 11px;")
    
    def clear(self) -> None:
        """모든 포지션 제거"""
        self._positions = {}
        self.table.setRowCount(0)
        self.total_pnl_label.setText("총 손익: $0.00")
        self.total_pnl_label.setStyleSheet("color: #aaa; font-size: 11px;")


class OrderPositionTabs(QWidget):
    """
    주문/포지션 탭 위젯
    
    거래내역, 미체결 주문, 포지션을 탭으로 전환합니다.
    탭에 카운트 표시 + 미확인 시 빨간색 하이라이트
    """
    
    # 탭 인덱스
    TAB_TRADES = 0
    TAB_ORDERS = 1
    TAB_POSITIONS = 2
    
    def __init__(self, trade_panel=None, parent=None) -> None:
        """초기화"""
        super().__init__(parent)
        
        # 미확인 상태 추적
        self._unread_orders = False
        self._unread_positions = False
        
        # 탭별 카운트
        self._order_count = 0
        self._position_count = 0
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 탭 위젯
        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self._on_tab_changed)
        
        self._setup_tab_style()
        
        # 거래 내역 탭 (외부에서 전달받음)
        self.trade_panel = trade_panel
        if trade_panel:
            self.tabs.addTab(trade_panel, "📋 거래내역")
        
        # 미체결 주문 탭
        self.orders_panel = OpenOrdersPanel()
        self.tabs.addTab(self.orders_panel, "🔄 주문")
        
        # 포지션 탭
        self.positions_panel = PositionsPanel()
        self.tabs.addTab(self.positions_panel, "📦 포지션")
        
        layout.addWidget(self.tabs)
    
    def _setup_tab_style(self) -> None:
        """탭 스타일 설정"""
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #3c3c3c;
                background-color: #1e1e1e;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #aaa;
                padding: 6px 12px;
                border: none;
            }
            QTabBar::tab:selected {
                background-color: #0e639c;
                color: white;
            }
        """)
    
    def _on_tab_changed(self, index: int) -> None:
        """탭 변경 시 미확인 상태 해제"""
        if index == self.TAB_ORDERS:
            self._unread_orders = False
            self._update_tab_titles()
        elif index == self.TAB_POSITIONS:
            self._unread_positions = False
            self._update_tab_titles()
    
    def _update_tab_titles(self) -> None:
        """탭 제목 업데이트 (카운트 + 하이라이트)"""
        # 주문 탭 제목
        order_title = "🔄 주문"
        if self._order_count > 0:
            if self._unread_orders:
                order_title = f"🔄 주문 <span style='color: #FF5252; font-weight: bold;'>({self._order_count})</span>"
            else:
                order_title = f"🔄 주문 ({self._order_count})"
        
        # HTML이 적용되지 않으므로 단순 텍스트 사용
        if self._unread_orders and self._order_count > 0:
            self.tabs.setTabText(self.TAB_ORDERS, f"🔄 주문 ({self._order_count}) ●")
        elif self._order_count > 0:
            self.tabs.setTabText(self.TAB_ORDERS, f"🔄 주문 ({self._order_count})")
        else:
            self.tabs.setTabText(self.TAB_ORDERS, "🔄 주문")
        
        # 포지션 탭 제목
        if self._unread_positions and self._position_count > 0:
            self.tabs.setTabText(self.TAB_POSITIONS, f"📦 포지션 ({self._position_count}) ●")
        elif self._position_count > 0:
            self.tabs.setTabText(self.TAB_POSITIONS, f"📦 포지션 ({self._position_count})")
        else:
            self.tabs.setTabText(self.TAB_POSITIONS, "📦 포지션")
    
    def update_order_count(self, count: int, is_new: bool = True) -> None:
        """
        주문 카운트 업데이트
        
        Args:
            count: 현재 주문 수
            is_new: True면 미확인 상태로 표시
        """
        if is_new and count > self._order_count:
            # 현재 주문 탭이 아니면 미확인 표시
            if self.tabs.currentIndex() != self.TAB_ORDERS:
                self._unread_orders = True
        
        self._order_count = count
        self._update_tab_titles()
    
    def update_position_count(self, count: int, is_new: bool = True) -> None:
        """
        포지션 카운트 업데이트
        
        Args:
            count: 현재 포지션 수
            is_new: True면 미확인 상태로 표시
        """
        if is_new and count > self._position_count:
            # 현재 포지션 탭이 아니면 미확인 표시
            if self.tabs.currentIndex() != self.TAB_POSITIONS:
                self._unread_positions = True
        
        self._position_count = count
        self._update_tab_titles()


# ============================================
# 테스트 코드
# ============================================
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # 탭 위젯 테스트
    tabs = OrderPositionTabs()
    tabs.setMinimumSize(500, 300)
    tabs.setWindowTitle("Order & Position Test")
    tabs.show()
    
    # 테스트 데이터
    tabs.orders_panel.add_order({
        "order_id": 1001,
        "time": datetime.now(),
        "symbol": "SPY",
        "action": "BUY",
        "quantity": 10,
        "price": 450.00
    })
    
    tabs.orders_panel.add_order({
        "order_id": 1002,
        "time": datetime.now(),
        "symbol": "QQQ",
        "action": "SELL",
        "quantity": 5,
        "price": 380.50
    })
    
    tabs.positions_panel.update_positions({
        "SPY": {
            "quantity": 20,
            "avg_price": 448.00,
            "current_price": 451.25,
            "pnl": 65.00,
            "pnl_pct": 1.45
        },
        "AAPL": {
            "quantity": 15,
            "avg_price": 182.50,
            "current_price": 180.00,
            "pnl": -37.50,
            "pnl_pct": -1.37
        }
    })
    
    print("✅ 테스트 창 표시됨")
    
    sys.exit(app.exec())
