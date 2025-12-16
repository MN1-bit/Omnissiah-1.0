"""
============================================
Green Mode 전략 (평균 회귀)
============================================
조건: VIX Z-Score < 1.0 (저변동성)
전략: VWAP ± 2σ 밴드 기반 평균 회귀
- BUY: 가격 <= Lower Band
- SELL: 가격 >= VWAP
- 15:50 전량 청산 (당일 종가 전)

⚠️ 모든 주문은 approve_order() 통과 필수!
============================================
"""

# ============================================
# 필수 라이브러리 임포트
# ============================================
from datetime import datetime, time
from typing import Optional, Dict, List, Tuple

import numpy as np
import pandas as pd
from PyQt6.QtCore import QObject, pyqtSignal


class GreenModeStrategy(QObject):
    """
    Green Mode 전략 (평균 회귀)
    
    저변동성 시장에서 VWAP 밴드를 활용한 평균 회귀 전략입니다.
    가격이 하단 밴드에서 진입, VWAP에서 청산합니다.
    
    Signals:
        signal_generated(dict): 매매 신호 발생 시
        log_message(str): 로그 메시지
    """
    
    # === PyQt Signals ===
    signal_generated = pyqtSignal(dict)   # 매매 신호
    log_message = pyqtSignal(str)         # 로그
    
    # === 전략 파라미터 ===
    BAND_MULTIPLIER = 2.0     # 밴드 배수 (2σ)
    EXIT_TIME = time(15, 50)  # 청산 시간 (15:50)
    
    def __init__(self, risk_manager=None, parent=None) -> None:
        """
        초기화
        
        Args:
            risk_manager: RiskManager 인스턴스 (approve_order용)
            parent: 부모 QObject
        """
        super().__init__(parent)
        self.risk_manager = risk_manager
        self._position: int = 0      # 현재 포지션 (0=없음, >0=롱)
        self._entry_price: float = 0.0
    
    # ============================================
    # VWAP 밴드 계산
    # ============================================
    
    def calculate_vwap_bands(self, prices: List[float], volumes: List[float]
                            ) -> Tuple[float, float, float]:
        """
        VWAP 및 밴드 계산
        
        VWAP = Σ(Price × Volume) / Σ(Volume)
        Upper Band = VWAP + 2σ
        Lower Band = VWAP - 2σ
        
        Args:
            prices: 가격 리스트 (당일 분봉)
            volumes: 거래량 리스트
            
        Returns:
            (vwap, upper_band, lower_band)
        """
        if not prices or not volumes or len(prices) != len(volumes):
            return (0.0, 0.0, 0.0)
        
        prices_arr = np.array(prices)
        volumes_arr = np.array(volumes)
        
        # VWAP 계산
        total_pv = np.sum(prices_arr * volumes_arr)
        total_volume = np.sum(volumes_arr)
        
        if total_volume == 0:
            return (0.0, 0.0, 0.0)
        
        vwap = total_pv / total_volume
        
        # 표준편차 계산 (VWAP 기준)
        squared_diff = (prices_arr - vwap) ** 2
        weighted_var = np.sum(squared_diff * volumes_arr) / total_volume
        std = np.sqrt(weighted_var)
        
        # 밴드 계산
        upper_band = vwap + (self.BAND_MULTIPLIER * std)
        lower_band = vwap - (self.BAND_MULTIPLIER * std)
        
        return (round(vwap, 2), round(upper_band, 2), round(lower_band, 2))
    
    # ============================================
    # 매매 신호 생성
    # ============================================
    
    def generate_signal(self, current_price: float, vwap: float,
                       lower_band: float, kill_status: str = "CLEAR",
                       daily_loss: float = 0.0, account: float = 10000.0
                       ) -> Optional[Dict]:
        """
        매매 신호 생성
        
        Args:
            current_price: 현재 가격
            vwap: VWAP
            lower_band: 하단 밴드
            kill_status: 킬 스위치 상태
            daily_loss: 당일 손실
            account: 계좌 잔고
            
        Returns:
            매매 신호 딕셔너리 또는 None
        """
        now = datetime.now().time()
        
        # --- 15:50 이후 전량 청산 ---
        if now >= self.EXIT_TIME:
            if self._position > 0:
                signal = {
                    "action": "SELL",
                    "reason": "장 마감 청산 (15:50)",
                    "price": current_price,
                    "quantity": self._position,
                }
                self._position = 0
                self.log_message.emit(f"🌙 장 마감 청산: {signal['quantity']}주 @ ${current_price:.2f}")
                self.signal_generated.emit(signal)
                return signal
            return None
        
        # --- 주문 승인 체크 (필수!) ---
        if self.risk_manager:
            if not self.risk_manager.approve_order(kill_status, daily_loss, account):
                self.log_message.emit("🚫 Green Mode: 주문 거부됨")
                return None
        
        # --- 매수 신호: 가격이 하단 밴드 이하 ---
        if self._position == 0 and current_price <= lower_band:
            signal = {
                "action": "BUY",
                "reason": f"Lower Band 터치 (${lower_band:.2f})",
                "price": current_price,
                "quantity": 1,  # 실제로는 포지션 사이징 적용
            }
            self._position = 1
            self._entry_price = current_price
            self.log_message.emit(f"🟢 Green Mode BUY: ${current_price:.2f} (Band: ${lower_band:.2f})")
            self.signal_generated.emit(signal)
            return signal
        
        # --- 매도 신호: 가격이 VWAP 이상 ---
        if self._position > 0 and current_price >= vwap:
            pnl = (current_price - self._entry_price) * self._position
            signal = {
                "action": "SELL",
                "reason": f"VWAP 도달 (${vwap:.2f})",
                "price": current_price,
                "quantity": self._position,
                "pnl": pnl,
            }
            self._position = 0
            self.log_message.emit(f"🟢 Green Mode SELL: ${current_price:.2f} (VWAP: ${vwap:.2f}), PnL: ${pnl:.2f}")
            self.signal_generated.emit(signal)
            return signal
        
        return None
    
    # ============================================
    # 상태 조회
    # ============================================
    
    def has_position(self) -> bool:
        """포지션 보유 여부"""
        return self._position > 0
    
    def get_position(self) -> int:
        """현재 포지션 수량"""
        return self._position
    
    def reset(self) -> None:
        """전략 초기화 (일일 리셋)"""
        self._position = 0
        self._entry_price = 0.0
    
    # ============================================
    # 적응형 오버나이트 판단
    # ============================================
    
    def should_keep_overnight(self, context: dict) -> bool:
        """
        횡보 Mode 오버나이트 킵 조건 (적응형)
        
        고정값 사용하지 않음:
        - 목표 근접: VWAP 거리 < daily_range × 0.5
        
        Args:
            context: {
                "current_price": float,
                "entry_price": float,
                "vwap": float,
                "daily_range_pct": float,  # 당일 변동폭 %
                "is_friday": bool
            }
            
        Returns:
            True: 오버나이트 킵
            False: 청산
        """
        # 1. 금요일은 무조건 청산 (주말 리스크)
        if context.get("is_friday", False):
            self.log_message.emit("🌑 횡보: 금요일 → 청산")
            return False
        
        # 2. 손실 중이면 청산
        current_price = context.get("current_price", 0)
        entry_price = context.get("entry_price", self._entry_price)
        
        if current_price < entry_price:
            self.log_message.emit("🌑 횡보: 손실 중 → 청산")
            return False
        
        # 3. 목표가(VWAP) 근접 시 청산 (적응형 임계값)
        vwap = context.get("vwap", 0)
        daily_range = context.get("daily_range_pct", 0.01)  # 기본 1%
        
        if vwap > 0:
            vwap_distance_pct = abs(current_price - vwap) / vwap
            threshold = daily_range * 0.5  # 당일 변동폭의 절반
            
            if vwap_distance_pct < threshold:
                self.log_message.emit(f"🌑 횡보: VWAP 근접 ({vwap_distance_pct:.2%}) → 청산")
                return False
        
        # 이익 중이고 목표가와 거리 있으면 킵
        self.log_message.emit("🌙 횡보: 이익 중 & 목표 미도달 → 오버나이트 킵")
        return True


# ============================================
# 단위 테스트
# ============================================
if __name__ == "__main__":
    print("=" * 50)
    print("Green Mode 전략 테스트")
    print("=" * 50)
    
    strategy = GreenModeStrategy()
    strategy.log_message.connect(lambda x: print(f"[LOG] {x}"))
    
    # VWAP 밴드 테스트
    prices = [100, 101, 99, 102, 98, 100, 101, 99]
    volumes = [1000, 1200, 800, 1500, 900, 1100, 1300, 950]
    
    vwap, upper, lower = strategy.calculate_vwap_bands(prices, volumes)
    print(f"\n📊 VWAP 밴드:")
    print(f"  VWAP: ${vwap:.2f}")
    print(f"  Upper: ${upper:.2f}")
    print(f"  Lower: ${lower:.2f}")
    
    # 매수 신호 테스트
    print(f"\n📋 매매 신호 테스트:")
    signal = strategy.generate_signal(lower - 0.5, vwap, lower)
    print(f"  Lower Band 이하: {signal['action'] if signal else 'None'}")
    
    # 매도 신호 테스트
    signal = strategy.generate_signal(vwap + 0.5, vwap, lower)
    print(f"  VWAP 이상: {signal['action'] if signal else 'None'}")
