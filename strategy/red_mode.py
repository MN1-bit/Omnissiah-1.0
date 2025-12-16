"""
============================================
Red Mode 전략 (추세 추종)
============================================
조건: 골디락스 존 (KER > 0.3 AND ADX > 25)
전략: 전일 고가 돌파 진입, 피라미딩 최대 3회
- BUY: 전일 고가 돌파
- SELL: MA20 이탈
- 피라미딩: 추가 1% 상승 시 추가 진입 (최대 3회)

⚠️ 모든 주문은 approve_order() 통과 필수!
============================================
"""

# ============================================
# 필수 라이브러리 임포트
# ============================================
from datetime import datetime
from typing import Optional, Dict, List

import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal


class RedModeStrategy(QObject):
    """
    Red Mode 전략 (추세 추종)
    
    골디락스 존에서 추세를 따라가는 전략입니다.
    전일 고가 돌파 시 진입, MA20 이탈 시 청산합니다.
    
    Signals:
        signal_generated(dict): 매매 신호 발생 시
        log_message(str): 로그 메시지
    """
    
    # === PyQt Signals ===
    signal_generated = pyqtSignal(dict)   # 매매 신호
    log_message = pyqtSignal(str)         # 로그
    
    # === 전략 파라미터 ===
    MAX_PYRAMIDING = 3          # 최대 피라미딩 횟수
    PYRAMID_THRESHOLD = 0.01    # 피라미딩 임계값 (1%)
    MA_PERIOD = 20              # 이동평균 기간
    
    def __init__(self, risk_manager=None, parent=None) -> None:
        """
        초기화
        
        Args:
            risk_manager: RiskManager 인스턴스
            parent: 부모 QObject
        """
        super().__init__(parent)
        self.risk_manager = risk_manager
        self._positions: List[Dict] = []  # 진입 내역 [{price, qty}]
        self._last_pyramid_price: float = 0.0
    
    # ============================================
    # 지표 계산
    # ============================================
    
    def calculate_ma(self, prices: List[float], period: int = None) -> float:
        """
        이동평균 계산
        
        Args:
            prices: 종가 리스트
            period: 기간 (기본 20)
            
        Returns:
            이동평균 값
        """
        if period is None:
            period = self.MA_PERIOD
        
        if len(prices) < period:
            return 0.0
        
        return round(np.mean(prices[-period:]), 2)
    
    # ============================================
    # 매매 신호 생성
    # ============================================
    
    def generate_signal(self, current_price: float, prev_high: float,
                       prices: List[float], kill_status: str = "CLEAR",
                       daily_loss: float = 0.0, account: float = 10000.0
                       ) -> Optional[Dict]:
        """
        매매 신호 생성
        
        Args:
            current_price: 현재 가격
            prev_high: 전일 고가
            prices: 종가 히스토리 (MA 계산용)
            kill_status: 킬 스위치 상태
            daily_loss: 당일 손실
            account: 계좌 잔고
            
        Returns:
            매매 신호 딕셔너리 또는 None
        """
        ma20 = self.calculate_ma(prices)
        position_count = len(self._positions)
        total_qty = sum(p["qty"] for p in self._positions)
        
        # --- 청산 조건: MA20 이탈 ---
        if total_qty > 0 and current_price < ma20:
            avg_entry = sum(p["price"] * p["qty"] for p in self._positions) / total_qty
            pnl = (current_price - avg_entry) * total_qty
            
            signal = {
                "action": "SELL",
                "reason": f"MA{self.MA_PERIOD} 이탈 (${ma20:.2f})",
                "price": current_price,
                "quantity": total_qty,
                "pnl": pnl,
            }
            self._positions = []
            self._last_pyramid_price = 0.0
            self.log_message.emit(f"🔴 Red Mode SELL: ${current_price:.2f} (MA: ${ma20:.2f}), PnL: ${pnl:.2f}")
            self.signal_generated.emit(signal)
            return signal
        
        # --- 주문 승인 체크 (필수!) ---
        if self.risk_manager:
            if not self.risk_manager.approve_order(kill_status, daily_loss, account):
                self.log_message.emit("🚫 Red Mode: 주문 거부됨")
                return None
        
        # --- 신규 진입: 전일 고가 돌파 ---
        if position_count == 0 and current_price > prev_high:
            signal = {
                "action": "BUY",
                "reason": f"전일 고가 돌파 (${prev_high:.2f})",
                "price": current_price,
                "quantity": 1,
            }
            self._positions.append({"price": current_price, "qty": 1})
            self._last_pyramid_price = current_price
            self.log_message.emit(f"🔴 Red Mode BUY: ${current_price:.2f} (Prev High: ${prev_high:.2f})")
            self.signal_generated.emit(signal)
            return signal
        
        # --- 피라미딩: 추가 1% 상승 시 ---
        if 0 < position_count < self.MAX_PYRAMIDING:
            threshold_price = self._last_pyramid_price * (1 + self.PYRAMID_THRESHOLD)
            
            if current_price >= threshold_price:
                signal = {
                    "action": "BUY",
                    "reason": f"피라미딩 #{position_count + 1} (+{self.PYRAMID_THRESHOLD*100:.0f}%)",
                    "price": current_price,
                    "quantity": 1,
                }
                self._positions.append({"price": current_price, "qty": 1})
                self._last_pyramid_price = current_price
                self.log_message.emit(f"🔴 Red Mode PYRAMID #{position_count + 1}: ${current_price:.2f}")
                self.signal_generated.emit(signal)
                return signal
        
        return None
    
    # ============================================
    # 상태 조회
    # ============================================
    
    def has_position(self) -> bool:
        """포지션 보유 여부"""
        return len(self._positions) > 0
    
    def get_position_count(self) -> int:
        """진입 횟수"""
        return len(self._positions)
    
    def get_total_quantity(self) -> int:
        """총 보유 수량"""
        return sum(p["qty"] for p in self._positions)
    
    def reset(self) -> None:
        """전략 초기화"""
        self._positions = []
        self._last_pyramid_price = 0.0
    
    # ============================================
    # 적응형 오버나이트 판단
    # ============================================
    
    def should_keep_overnight(self, context: dict) -> str:
        """
        상승 Mode 오버나이트 킵 조건 (적응형)
        
        고정값 사용하지 않음:
        - VIX 위험: vix > vix_mean + vix_std
        - 과열: daily_return > ATR × 2
        
        Args:
            context: {
                "current_price": float,
                "ma20": float,
                "vix": float,
                "vix_mean": float,
                "vix_std": float,
                "daily_return": float,  # 당일 수익률 (예: 0.02 = 2%)
                "atr": float,           # 20일 ATR
                "is_friday": bool
            }
            
        Returns:
            "KEEP_ALL": 전량 킵
            "KEEP_HALF": 50% 청산
            "LIQUIDATE_ALL": 전량 청산
        """
        current_price = context.get("current_price", 0)
        ma20 = context.get("ma20", 0)
        vix = context.get("vix", 15)
        vix_mean = context.get("vix_mean", 20)
        vix_std = context.get("vix_std", 5)
        daily_return = context.get("daily_return", 0)
        atr = context.get("atr", 0)
        is_friday = context.get("is_friday", False)
        
        # 1. VIX 역사적 1σ 초과 시 청산 (적응형)
        vix_threshold = vix_mean + vix_std
        if vix >= vix_threshold:
            self.log_message.emit(f"🌑 상승: VIX {vix:.1f} >= {vix_threshold:.1f} (1σ) → 전량 청산")
            return "LIQUIDATE_ALL"
        
        # 2. MA20 이탈이면 청산
        if current_price < ma20:
            self.log_message.emit(f"🌑 상승: MA20 이탈 (${current_price:.2f} < ${ma20:.2f}) → 전량 청산")
            return "LIQUIDATE_ALL"
        
        # 3. 당일 수익이 ATR의 2배 초과 시 과열 (적응형)
        if atr > 0 and daily_return > (atr * 2):
            self.log_message.emit(f"🌓 상승: 과열 ({daily_return:.2%} > ATR×2) → 50% 청산")
            return "KEEP_HALF"
        
        # 4. 금요일: 부분 청산
        if is_friday:
            self.log_message.emit("🌓 상승: 금요일 → 50% 청산")
            return "KEEP_HALF"
        
        # 그 외 전량 킵
        self.log_message.emit("🌙 상승: 추세 유지 → 오버나이트 킵")
        return "KEEP_ALL"


# ============================================
# 단위 테스트
# ============================================
if __name__ == "__main__":
    print("=" * 50)
    print("Red Mode 전략 테스트")
    print("=" * 50)
    
    strategy = RedModeStrategy()
    strategy.log_message.connect(lambda x: print(f"[LOG] {x}"))
    
    # 가격 히스토리 (MA 계산용)
    prices = list(range(100, 125))  # 상승 추세
    
    print(f"\n📊 MA20: ${strategy.calculate_ma(prices):.2f}")
    
    # 돌파 진입 테스트
    print(f"\n📋 매매 신호 테스트:")
    prev_high = 120
    
    signal = strategy.generate_signal(121, prev_high, prices)
    print(f"  전일 고가 돌파: {signal['action'] if signal else 'None'}")
    
    # 피라미딩 테스트
    signal = strategy.generate_signal(123, prev_high, prices)
    print(f"  피라미딩 #2: {signal['action'] if signal else 'None'}")
    
    # MA 이탈 청산 테스트
    signal = strategy.generate_signal(105, prev_high, prices)
    print(f"  MA20 이탈: {signal['action'] if signal else 'None'}")
