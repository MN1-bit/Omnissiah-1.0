"""
============================================
IBKR 브릿지 - QThread 기반 연결 관리
============================================
Interactive Brokers Gateway/TWS 연결을 백그라운드에서 처리합니다.
GUI가 멈추지 않도록 별도 스레드에서 실행됩니다.

중요: time.sleep() 대신 QThread.msleep() 사용!
============================================
"""

# ============================================
# 필수 라이브러리 임포트
# ============================================
import os                               # 환경 변수
from typing import Optional, Dict, Any, List  # 타입 힌트
from dotenv import load_dotenv          # .env 파일 로드
from ib_insync import IB, util, Stock, Ticker  # IBKR API
from PyQt6.QtCore import (              # PyQt6 코어
    QThread,                            # 백그라운드 스레드
    pyqtSignal,                         # 시그널 (스레드 → GUI 통신)
)

# .env 파일 로드
load_dotenv()


class IBKRBridge(QThread):
    """
    IBKR 연결 브릿지 (QThread)
    
    백그라운드에서 IBKR Gateway/TWS에 연결하고,
    상태 변화를 PyQt Signal로 GUI에 전달합니다.
    
    Signals:
        connected(bool): 연결 상태 변경 시 발생
        account_update(dict): 계좌 정보 업데이트 시 발생
        price_update(dict): 실시간 시세 업데이트 시 발생
        error(str): 에러 발생 시 발생
        log_message(str): 로그 메시지 발생 시 발생
    """
    
    # === PyQt Signals (GUI와 통신용) ===
    connected = pyqtSignal(bool)        # 연결 상태
    account_update = pyqtSignal(dict)   # 계좌 정보
    price_update = pyqtSignal(dict)     # 실시간 시세 {symbol, bid, ask, last, volume}
    error = pyqtSignal(str)             # 에러 메시지
    log_message = pyqtSignal(str)       # 로그 메시지
    
    def __init__(self, parent=None) -> None:
        """브릿지 초기화"""
        super().__init__(parent)
        
        # --- IB 객체 ---
        self.ib: Optional[IB] = None
        
        # --- 연결 설정 (.env에서 로드) ---
        self.host: str = os.getenv("IB_HOST", "127.0.0.1")
        self.port: int = int(os.getenv("IB_PORT", "4002"))
        self.client_id: int = int(os.getenv("IB_CLIENT_ID", "1"))
        self.account: str = os.getenv("IB_ACCOUNT", "")
        
        # --- 상태 플래그 ---
        self._is_running: bool = False
        self._is_connected: bool = False
        
        # --- 실시간 시세 구독 추적 ---
        self._subscribed_tickers: Dict[str, Ticker] = {}
    
    def run(self) -> None:
        """
        스레드 메인 루프
        
        이 메서드는 start()를 호출하면 자동으로 실행됩니다.
        연결을 시도하고, 연결되면 이벤트 루프를 유지합니다.
        """
        self._is_running = True
        self.log_message.emit("🔌 IBKR 연결 시도 중...")
        
        try:
            # --- ib_insync용 이벤트 루프 시작 (필수!) ---
            util.startLoop()
            
            # --- IB 객체 생성 ---
            self.ib = IB()
            
            # --- 연결 시도 (최대 3회 재시도) ---
            max_retries = 3
            for attempt in range(1, max_retries + 1):
                try:
                    self.log_message.emit(f"📡 연결 시도 {attempt}/{max_retries}...")
                    
                    # 연결 (타임아웃 10초)
                    self.ib.connect(
                        host=self.host,
                        port=self.port,
                        clientId=self.client_id,
                        timeout=10
                    )
                    
                    # 연결 성공!
                    self._is_connected = True
                    self.connected.emit(True)
                    self.log_message.emit(f"✅ IBKR 연결 성공! (포트: {self.port})")
                    
                    # --- 이벤트 콜백 등록 (폴링 대신 이벤트 기반!) ---
                    self.ib.orderStatusEvent += self._on_order_status
                    self.ib.execDetailsEvent += self._on_execution
                    self.ib.accountValueEvent += self._on_account_value
                    
                    # 초기 계좌 정보 1회 조회
                    self._fetch_account_info()
                    
                    break  # 재시도 루프 탈출
                    
                except Exception as e:
                    self.log_message.emit(f"⚠️ 연결 실패: {str(e)}")
                    
                    if attempt < max_retries:
                        # Exponential Backoff (1초, 2초, 4초)
                        wait_time = 2 ** (attempt - 1)
                        self.log_message.emit(f"⏳ {wait_time}초 후 재시도...")
                        QThread.msleep(wait_time * 1000)  # time.sleep 대신!
                    else:
                        raise  # 마지막 시도도 실패하면 예외 발생
            
            # --- 이벤트 루프 유지 (폴링 없이!) ---
            while self._is_running and self.ib.isConnected():
                # IB 이벤트만 처리 (콜백이 자동 호출됨)
                self.ib.sleep(0.1)
                    
        except Exception as e:
            self.error.emit(f"❌ 연결 오류: {str(e)}")
            self._is_connected = False
            self.connected.emit(False)
        
        finally:
            # --- 정리 ---
            self._disconnect()
    
    def _fetch_account_info(self) -> None:
        """계좌 정보 조회 및 GUI에 전달"""
        if not self.ib or not self.ib.isConnected():
            return
        
        try:
            # 계좌 요약 정보 요청
            account_values = self.ib.accountSummary()
            
            # 필요한 정보 추출
            info: Dict[str, Any] = {
                "account": self.account or (self.ib.managedAccounts()[0] if self.ib.managedAccounts() else "N/A"),
                "balance": 0.0,
                "available": 0.0,
            }
            
            for av in account_values:
                if av.tag == "NetLiquidation":
                    info["balance"] = float(av.value)
                elif av.tag == "AvailableFunds":
                    info["available"] = float(av.value)
            
            # GUI에 전달
            self.account_update.emit(info)
            
        except Exception as e:
            self.log_message.emit(f"⚠️ 계좌 정보 조회 실패: {str(e)}")
    
    # ============================================
    # 이벤트 콜백 (체결 시에만 호출됨)
    # ============================================
    
    def _on_order_status(self, trade) -> None:
        """주문 상태 변경 시 (체결, 취소 등)"""
        status = trade.orderStatus.status
        self.log_message.emit(f"📋 주문 상태: {status}")
        
        if status in ("Filled", "PartiallyFilled"):
            # 체결되면 잔고 업데이트
            self._fetch_account_info()
    
    def _on_execution(self, trade, fill) -> None:
        """체결 발생 시"""
        symbol = trade.contract.symbol
        qty = fill.execution.shares
        price = fill.execution.price
        side = fill.execution.side
        
        emoji = "🟢" if side == "BOT" else "🔴"
        self.log_message.emit(f"{emoji} 체결: {symbol} {qty}주 @ ${price:.2f}")
        
        # 체결 후 잔고 업데이트
        self._fetch_account_info()
    
    def _on_account_value(self, value) -> None:
        """계좌 값 변경 시 (NetLiquidation 등)"""
        if value.tag == "NetLiquidation":
            try:
                balance = float(value.value)
                info = {"balance": balance, "available": 0.0, "account": value.account}
                self.account_update.emit(info)
            except ValueError:
                pass
    
    def _disconnect(self) -> None:
        """연결 해제"""
        if self.ib and self.ib.isConnected():
            self.ib.disconnect()
            self.log_message.emit("🔌 IBKR 연결 해제됨")
        
        self._is_connected = False
        self.connected.emit(False)
    
    # ============================================
    # 공개 메서드 (외부에서 호출)
    # ============================================
    
    def stop(self) -> None:
        """연결 중지 및 스레드 종료"""
        self._is_running = False
        self.log_message.emit("⏹ 연결 중지 요청됨...")
        
        # 스레드 종료 대기 (최대 5초)
        self.wait(5000)
    
    def is_connected(self) -> bool:
        """현재 연결 상태 반환"""
        return self._is_connected
    
    def get_ib(self) -> Optional[IB]:
        """IB 객체 반환 (다른 모듈에서 사용)"""
        return self.ib if self._is_connected else None
    
    # ============================================
    # 실시간 시세 구독
    # ============================================
    
    def subscribe_market_data(self, symbols: List[str], outside_rth: bool = True) -> None:
        """
        실시간 시세 구독
        
        Args:
            symbols: 구독할 심볼 리스트 (예: ["SPY", "QQQ", "VIX"])
            outside_rth: True면 Pre/After Market 시세도 수신 (기본값: True)
        """
        if not self.ib or not self.ib.isConnected():
            self.log_message.emit("❌ 시세 구독 실패: IBKR 연결 안됨")
            return
        
        for symbol in symbols:
            if symbol in self._subscribed_tickers:
                continue  # 이미 구독 중
            
            try:
                # VIX는 인덱스
                if symbol.upper() in ["VIX", "^VIX"]:
                    from ib_insync import Index
                    contract = Index("VIX", "CBOE")
                else:
                    contract = Stock(symbol, "SMART", "USD")
                
                # 시세 구독 요청 (outsideRth: Pre/After Market 지원)
                # genericTickList "": 기본 틱, snapshot=False: 스트리밍
                # regulatorySnapshot=False, mktDataOptions=[]
                ticker = self.ib.reqMktData(
                    contract, 
                    "", 
                    False,  # snapshot
                    False,  # regulatorySnapshot
                    []      # mktDataOptions
                )
                
                # 콜백 등록
                ticker.updateEvent += self._on_price_update
                
                self._subscribed_tickers[symbol] = ticker
                
                hours_mode = "Extended Hours" if outside_rth else "Regular Hours"
                self.log_message.emit(f"📡 실시간 시세 구독: {symbol} ({hours_mode})")
                
            except Exception as e:
                self.log_message.emit(f"⚠️ {symbol} 구독 실패: {str(e)}")
    
    def unsubscribe_market_data(self, symbol: str) -> None:
        """실시간 시세 구독 해제"""
        if symbol not in self._subscribed_tickers:
            return
        
        try:
            ticker = self._subscribed_tickers.pop(symbol)
            if self.ib and self.ib.isConnected():
                self.ib.cancelMktData(ticker.contract)
            self.log_message.emit(f"📴 시세 구독 해제: {symbol}")
        except Exception as e:
            self.log_message.emit(f"⚠️ {symbol} 구독 해제 실패: {str(e)}")
    
    def unsubscribe_all(self) -> None:
        """모든 시세 구독 해제"""
        symbols = list(self._subscribed_tickers.keys())
        for symbol in symbols:
            self.unsubscribe_market_data(symbol)
    
    def _on_price_update(self, ticker: Ticker) -> None:
        """실시간 시세 업데이트 콜백"""
        try:
            symbol = ticker.contract.symbol
            
            data = {
                "symbol": symbol,
                "bid": ticker.bid if ticker.bid else 0.0,
                "ask": ticker.ask if ticker.ask else 0.0,
                "last": ticker.last if ticker.last else 0.0,
                "volume": ticker.volume if ticker.volume else 0,
                "high": ticker.high if ticker.high else 0.0,
                "low": ticker.low if ticker.low else 0.0,
                "close": ticker.close if ticker.close else 0.0,
            }
            
            self.price_update.emit(data)
            
        except Exception:
            pass  # 에러 무시 (시세 업데이트가 너무 빈번함)


# ============================================
# 단위 테스트
# ============================================
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QCoreApplication
    
    app = QCoreApplication(sys.argv)
    
    # 브릿지 생성
    bridge = IBKRBridge()
    
    # 시그널 연결
    bridge.connected.connect(lambda x: print(f"연결 상태: {x}"))
    bridge.account_update.connect(lambda x: print(f"계좌 정보: {x}"))
    bridge.error.connect(lambda x: print(f"에러: {x}"))
    bridge.log_message.connect(lambda x: print(f"로그: {x}"))
    
    # 연결 시작
    bridge.start()
    
    # 10초 후 종료
    from PyQt6.QtCore import QTimer
    QTimer.singleShot(10000, lambda: (bridge.stop(), app.quit()))
    
    sys.exit(app.exec())
