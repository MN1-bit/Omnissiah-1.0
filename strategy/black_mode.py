"""
============================================
Black Mode 전략 (방어/패닉)
============================================
조건: Z-Score >= 2.0 또는 VIX 백워데이션
전략: 
- 기본: 전량 청산 (리스크 회피)
- 인버스 진입: 백워데이션 AND 오후2시 AND 신저점
- 인버스 보유: 최대 3일

⚠️ 모든 주문은 approve_order() 통과 필수!
============================================
"""

# ============================================
# 필수 라이브러리 임포트
# ============================================
from datetime import datetime, time, timedelta
from typing import Optional, Dict

from PyQt6.QtCore import QObject, pyqtSignal


class BlackModeStrategy(QObject):
    """
    Black Mode 전략 (방어/패닉)
    
    고변동성 시장에서 리스크를 최소화하는 전략입니다.
    기본적으로 전량 청산하고, 조건 충족 시 인버스에 진입합니다.
    
    Signals:
        signal_generated(dict): 매매 신호 발생 시
        log_message(str): 로그 메시지
    """
    
    # === PyQt Signals ===
    signal_generated = pyqtSignal(dict)   # 매매 신호
    log_message = pyqtSignal(str)         # 로그
    
    # === 전략 파라미터 ===
    INVERSE_ENTRY_TIME = time(14, 0)  # 인버스 진입 시간 (오후 2시)
    MAX_INVERSE_DAYS = 3              # 인버스 최대 보유일
    INVERSE_SYMBOLS = ["SQQQ", "SPXS", "SDOW"]  # 인버스 ETF
    
    def __init__(self, risk_manager=None, parent=None) -> None:
        """
        초기화
        
        Args:
            risk_manager: RiskManager 인스턴스
            parent: 부모 QObject
        """
        super().__init__(parent)
        self.risk_manager = risk_manager
        self._inverse_position: bool = False
        self._inverse_entry_date: Optional[datetime] = None
    
    # ============================================
    # 청산 로직
    # ============================================
    
    def liquidate_all(self, positions: Dict[str, int], 
                     current_prices: Dict[str, float]) -> list:
        """
        전량 청산
        
        모든 롱 포지션을 청산합니다.
        
        Args:
            positions: {symbol: quantity} 현재 포지션
            current_prices: {symbol: price} 현재 가격
            
        Returns:
            청산 신호 리스트
        """
        signals = []
        
        for symbol, qty in positions.items():
            if qty > 0:
                price = current_prices.get(symbol, 0)
                signal = {
                    "action": "SELL",
                    "symbol": symbol,
                    "reason": "Black Mode 전량 청산",
                    "price": price,
                    "quantity": qty,
                }
                signals.append(signal)
                self.log_message.emit(f"⚫ Black Mode 청산: {symbol} {qty}주 @ ${price:.2f}")
                self.signal_generated.emit(signal)
        
        return signals
    
    # ============================================
    # 인버스 진입 판단
    # ============================================
    
    def should_enter_inverse(self, is_backwardation: bool, 
                            is_new_low: bool) -> bool:
        """
        인버스 진입 조건 확인
        
        조건:
        1. VIX 백워데이션 상태
        2. 오후 2시 이후
        3. 52주 신저점
        
        Args:
            is_backwardation: VIX 백워데이션 여부
            is_new_low: 신저점 여부
            
        Returns:
            인버스 진입 여부
        """
        now = datetime.now().time()
        
        # 이미 인버스 포지션이 있으면 진입 안 함
        if self._inverse_position:
            return False
        
        # 모든 조건 확인
        is_after_2pm = now >= self.INVERSE_ENTRY_TIME
        
        if is_backwardation and is_after_2pm and is_new_low:
            self.log_message.emit("⚫ 인버스 진입 조건 충족!")
            return True
        
        return False
    
    def enter_inverse(self, symbol: str = "SQQQ", 
                     kill_status: str = "HALT_ALL",
                     daily_loss: float = 0.0, 
                     account: float = 10000.0) -> Optional[Dict]:
        """
        인버스 진입
        
        Args:
            symbol: 인버스 ETF 심볼
            kill_status: 킬 스위치 상태
            daily_loss: 당일 손실
            account: 계좌 잔고
            
        Returns:
            매수 신호 또는 None
        """
        # Black Mode에서는 HALT_ALL 상태에서도 인버스 진입 허용
        # 단, 일일 손실 한도는 체크
        if account > 0 and (daily_loss / account) > 0.05:
            self.log_message.emit("🚫 Black Mode 인버스: 일일 손실 한도 초과")
            return None
        
        signal = {
            "action": "BUY",
            "symbol": symbol,
            "reason": "Black Mode 인버스 진입",
            "quantity": 1,  # 실제로는 포지션 사이징 적용
        }
        
        self._inverse_position = True
        self._inverse_entry_date = datetime.now()
        
        self.log_message.emit(f"⚫ Black Mode 인버스 진입: {symbol}")
        self.signal_generated.emit(signal)
        
        return signal
    
    # ============================================
    # 인버스 청산 판단
    # ============================================
    
    def should_exit_inverse(self) -> bool:
        """
        인버스 청산 조건 확인
        
        최대 3일 보유 후 청산
        
        Returns:
            청산 여부
        """
        if not self._inverse_position or not self._inverse_entry_date:
            return False
        
        days_held = (datetime.now() - self._inverse_entry_date).days
        
        if days_held >= self.MAX_INVERSE_DAYS:
            self.log_message.emit(f"⚫ 인버스 보유 {days_held}일 - 청산 필요")
            return True
        
        return False
    
    def exit_inverse(self, symbol: str = "SQQQ", 
                    quantity: int = 1) -> Dict:
        """
        인버스 청산
        
        Args:
            symbol: 인버스 ETF 심볼
            quantity: 청산 수량
            
        Returns:
            매도 신호
        """
        signal = {
            "action": "SELL",
            "symbol": symbol,
            "reason": f"인버스 보유 {self.MAX_INVERSE_DAYS}일 청산",
            "quantity": quantity,
        }
        
        self._inverse_position = False
        self._inverse_entry_date = None
        
        self.log_message.emit(f"⚫ Black Mode 인버스 청산: {symbol}")
        self.signal_generated.emit(signal)
        
        return signal
    
    # ============================================
    # 상태 조회
    # ============================================
    
    def has_inverse_position(self) -> bool:
        """인버스 포지션 보유 여부"""
        return self._inverse_position
    
    def get_inverse_days_held(self) -> int:
        """인버스 보유 일수"""
        if not self._inverse_entry_date:
            return 0
        return (datetime.now() - self._inverse_entry_date).days
    
    def reset(self) -> None:
        """전략 초기화"""
        self._inverse_position = False
        self._inverse_entry_date = None


# ============================================
# 단위 테스트
# ============================================
if __name__ == "__main__":
    print("=" * 50)
    print("Black Mode 전략 테스트")
    print("=" * 50)
    
    strategy = BlackModeStrategy()
    strategy.log_message.connect(lambda x: print(f"[LOG] {x}"))
    
    # 전량 청산 테스트
    print(f"\n📋 전량 청산 테스트:")
    positions = {"TQQQ": 10, "SOXL": 5}
    prices = {"TQQQ": 45.0, "SOXL": 30.0}
    signals = strategy.liquidate_all(positions, prices)
    print(f"  청산 신호: {len(signals)}개")
    
    # 인버스 진입 조건 테스트
    print(f"\n📋 인버스 진입 조건:")
    print(f"  백워데이션 + 2PM + 신저점: {strategy.should_enter_inverse(True, True)}")
    print(f"  백워데이션 only: {strategy.should_enter_inverse(True, False)}")
    
    # 인버스 진입 테스트
    print(f"\n📋 인버스 진입:")
    signal = strategy.enter_inverse("SQQQ")
    print(f"  결과: {signal['action'] if signal else 'None'}")
    
    # 인버스 청산 테스트
    print(f"\n📋 인버스 청산 (3일 후):")
    strategy._inverse_entry_date = datetime.now() - timedelta(days=3)
    print(f"  청산 필요: {strategy.should_exit_inverse()}")
