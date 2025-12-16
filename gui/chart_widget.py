"""
============================================
실시간 차트 위젯
============================================
pyqtgraph 기반 실시간 가격 차트입니다.

기능:
- 5분봉 캔들스틱
- VWAP 밴드 오버레이
- 포지션 마커 (진입/청산)
- 레짐별 배경색
============================================
"""

# ============================================
# 필수 라이브러리 임포트
# ============================================
from datetime import datetime
from typing import Optional, List, Dict, Tuple
import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPen, QBrush

import pyqtgraph as pg


# ============================================
# 레짐별 배경색 정의
# ============================================
REGIME_COLORS = {
    "횡보": "#FFF8DC",  # 연노랑 (Cornsilk)
    "상승": "#E0FFFF",  # 연청록 (LightCyan)
    "위기": "#FFE4E1",  # 연빨강 (MistyRose)
}


class LiveChartWidget(QWidget):
    """
    실시간 차트 위젯
    
    5분봉 캔들스틱과 VWAP 밴드를 표시합니다.
    포지션 진입/청산점도 마커로 표시합니다.
    
    Signals:
        chart_clicked(float): 차트 클릭 시 가격 전달
    """
    
    chart_clicked = pyqtSignal(float)
    
    def __init__(self, parent=None) -> None:
        """초기화"""
        super().__init__(parent)
        
        # 데이터 저장소
        self._candles: List[Dict] = []  # {time, open, high, low, close}
        self._vwap_data: List[float] = []
        self._upper_band: List[float] = []
        self._lower_band: List[float] = []
        self._positions: List[Dict] = []  # {time, price, action, pnl}
        
        # 현재 레짐
        self._current_regime = "횡보"
        
        # UI 설정
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # === 상단 정보 바 ===
        info_bar = QHBoxLayout()
        
        self.symbol_label = QLabel("SPY")
        self.symbol_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        info_bar.addWidget(self.symbol_label)
        
        self.price_label = QLabel("$0.00")
        self.price_label.setStyleSheet("font-size: 14px; color: #00C853;")
        info_bar.addWidget(self.price_label)
        
        self.regime_label = QLabel("횡보")
        self.regime_label.setStyleSheet(
            f"padding: 2px 8px; border-radius: 4px; "
            f"background-color: {REGIME_COLORS['횡보']};"
        )
        info_bar.addWidget(self.regime_label)
        
        info_bar.addStretch()
        layout.addLayout(info_bar)
        
        # === pyqtgraph 차트 ===
        pg.setConfigOptions(antialias=True)
        
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("#1e1e1e")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setLabel("left", "Price ($)")
        self.plot_widget.setLabel("bottom", "Time")
        
        layout.addWidget(self.plot_widget)
        
        # === 플롯 아이템들 ===
        # 캔들스틱용 바 차트 (임시로 라인 차트 사용)
        self.price_line = self.plot_widget.plot(
            pen=pg.mkPen(color="#00C853", width=2)
        )
        
        # VWAP 라인
        self.vwap_line = self.plot_widget.plot(
            pen=pg.mkPen(color="#FFEB3B", width=1, style=Qt.PenStyle.DashLine)
        )
        
        # Upper Band
        self.upper_line = self.plot_widget.plot(
            pen=pg.mkPen(color="#FF5722", width=1, style=Qt.PenStyle.DotLine)
        )
        
        # Lower Band
        self.lower_line = self.plot_widget.plot(
            pen=pg.mkPen(color="#2196F3", width=1, style=Qt.PenStyle.DotLine)
        )
        
        # 포지션 마커 (산점도)
        self.buy_markers = pg.ScatterPlotItem(
            symbol="t",  # 삼각형
            size=12,
            brush=pg.mkBrush("#4CAF50")  # 초록
        )
        self.plot_widget.addItem(self.buy_markers)
        
        self.sell_markers = pg.ScatterPlotItem(
            symbol="t1",  # 역삼각형
            size=12,
            brush=pg.mkBrush("#F44336")  # 빨강
        )
        self.plot_widget.addItem(self.sell_markers)
    
    # ============================================
    # 데이터 업데이트
    # ============================================
    
    def update_price(self, price: float, symbol: str = "SPY") -> None:
        """
        현재 가격 업데이트
        
        Args:
            price: 현재 가격
            symbol: 심볼
        """
        self.symbol_label.setText(symbol)
        self.price_label.setText(f"${price:.2f}")
        
        # 가격 변화에 따른 색상
        if len(self._candles) > 0:
            prev_price = self._candles[-1].get("close", price)
            if price > prev_price:
                self.price_label.setStyleSheet("font-size: 14px; color: #00C853;")
            elif price < prev_price:
                self.price_label.setStyleSheet("font-size: 14px; color: #FF5252;")
    
    def add_candle(self, time_idx: int, open_p: float, high: float, 
                   low: float, close: float) -> None:
        """
        캔들 추가
        
        Args:
            time_idx: 시간 인덱스
            open_p, high, low, close: OHLC
        """
        self._candles.append({
            "time": time_idx,
            "open": open_p,
            "high": high,
            "low": low,
            "close": close
        })
        
        # 최근 100개만 유지
        if len(self._candles) > 100:
            self._candles.pop(0)
        
        self._update_chart()
    
    def update_vwap(self, vwap: float, upper: float, lower: float) -> None:
        """
        VWAP 밴드 업데이트
        
        Args:
            vwap: VWAP 값
            upper: Upper band
            lower: Lower band
        """
        self._vwap_data.append(vwap)
        self._upper_band.append(upper)
        self._lower_band.append(lower)
        
        # 최근 100개만 유지
        if len(self._vwap_data) > 100:
            self._vwap_data.pop(0)
            self._upper_band.pop(0)
            self._lower_band.pop(0)
        
        self._update_chart()
    
    def add_position_marker(self, time_idx: int, price: float, 
                           action: str, pnl: float = 0) -> None:
        """
        포지션 마커 추가
        
        Args:
            time_idx: 시간 인덱스
            price: 가격
            action: "BUY" or "SELL"
            pnl: 손익 (SELL의 경우)
        """
        self._positions.append({
            "time": time_idx,
            "price": price,
            "action": action,
            "pnl": pnl
        })
        
        self._update_markers()
    
    def set_regime(self, regime: str) -> None:
        """
        레짐 변경
        
        Args:
            regime: "횡보", "상승", "위기"
        """
        self._current_regime = regime
        color = REGIME_COLORS.get(regime, "#FFFFFF")
        
        self.regime_label.setText(regime)
        self.regime_label.setStyleSheet(
            f"padding: 2px 8px; border-radius: 4px; "
            f"background-color: {color};"
        )
        
        # 배경색 변경 (약간 어둡게)
        bg_color = QColor(color)
        bg_color.setAlpha(30)
        self.plot_widget.setBackground(bg_color)
    
    # ============================================
    # 내부 업데이트 메서드
    # ============================================
    
    def _update_chart(self) -> None:
        """차트 업데이트"""
        if not self._candles:
            return
        
        # 가격 라인 (종가 기준)
        times = [c["time"] for c in self._candles]
        closes = [c["close"] for c in self._candles]
        self.price_line.setData(times, closes)
        
        # VWAP 밴드
        if self._vwap_data:
            x = list(range(len(self._vwap_data)))
            self.vwap_line.setData(x, self._vwap_data)
            self.upper_line.setData(x, self._upper_band)
            self.lower_line.setData(x, self._lower_band)
    
    def _update_markers(self) -> None:
        """마커 업데이트"""
        buy_spots = []
        sell_spots = []
        
        for pos in self._positions:
            spot = {"pos": (pos["time"], pos["price"])}
            
            if pos["action"] == "BUY":
                buy_spots.append(spot)
            else:
                sell_spots.append(spot)
        
        self.buy_markers.setData(buy_spots)
        self.sell_markers.setData(sell_spots)
    
    def clear(self) -> None:
        """차트 초기화"""
        self._candles = []
        self._vwap_data = []
        self._upper_band = []
        self._lower_band = []
        self._positions = []
        
        self.price_line.clear()
        self.vwap_line.clear()
        self.upper_line.clear()
        self.lower_line.clear()
        self.buy_markers.clear()
        self.sell_markers.clear()


# ============================================
# 테스트 코드
# ============================================
if __name__ == "__main__":
    import sys
    import random
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QTimer
    
    app = QApplication(sys.argv)
    
    chart = LiveChartWidget()
    chart.setMinimumSize(800, 400)
    chart.setWindowTitle("Live Chart Test")
    chart.show()
    
    # 테스트 데이터
    price = 450.0
    time_idx = 0
    
    def add_test_candle():
        global price, time_idx
        
        # 랜덤 변동
        change = random.uniform(-2, 2)
        open_p = price
        close = price + change
        high = max(open_p, close) + random.uniform(0, 1)
        low = min(open_p, close) - random.uniform(0, 1)
        
        chart.add_candle(time_idx, open_p, high, low, close)
        chart.update_price(close)
        
        # VWAP 밴드
        vwap = (open_p + close) / 2
        chart.update_vwap(vwap, vwap + 2, vwap - 2)
        
        # 가끔 마커 추가
        if random.random() < 0.1:
            action = "BUY" if random.random() < 0.5 else "SELL"
            chart.add_position_marker(time_idx, close, action)
        
        price = close
        time_idx += 1
        
        # 레짐 변경 테스트
        if time_idx == 20:
            chart.set_regime("상승")
        elif time_idx == 40:
            chart.set_regime("위기")
        elif time_idx == 60:
            chart.set_regime("횡보")
    
    # 500ms마다 캔들 추가
    timer = QTimer()
    timer.timeout.connect(add_test_candle)
    timer.start(500)
    
    sys.exit(app.exec())
