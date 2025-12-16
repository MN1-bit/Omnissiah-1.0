"""
============================================
Project Omnissiah - 메인 컨트롤러 (하이브리드)
============================================
모든 모듈을 통합하여 시스템을 운영합니다.

=== 하이브리드 업데이트 방식 ===
- 기본 루프: 5초 간격
- 동적 주기: |Z-Score| >= 1.0 → 1초
- 이벤트: VIX ±0.5pt → 즉시 업데이트
- 일봉 통계: 캐싱 (1일 1회)

⚠️ 핵심 규칙:
- time.sleep() 절대 금지!
- 킬 스위치가 항상 1순위
============================================
"""

# ============================================
# 필수 라이브러리 임포트
# ============================================
import sys
from typing import Optional
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# --- 프로젝트 내부 모듈 ---
from gui.dashboard import OmnissiahDashboard
from core.bridge import IBKRBridge
from core.market_data import MarketDataManager
from core.regime_detector import RegimeDetector
from core.risk_manager import RiskManager
from core.scanner import UniverseSelector
from core.order_executor import OrderExecutor
from core.scheduler import TradingScheduler
from strategy.green_mode import GreenModeStrategy
from strategy.red_mode import RedModeStrategy
from strategy.black_mode import BlackModeStrategy


class OmnissiahController:
    """
    Omnissiah 메인 컨트롤러
    
    모든 모듈을 연결하고 시스템을 운영합니다.
    매 1초마다 trading_iteration을 실행합니다.
    """
    
    # === 하이브리드 타이머 설정 ===
    BASE_INTERVAL = 5000      # 기본 5초
    FAST_INTERVAL = 1000      # 빠른 1초 (|Z| >= 1.0)
    Z_THRESHOLD = 1.0         # 주기 전환 임계값
    
    def __init__(self) -> None:
        """컨트롤러 초기화"""
        # --- Qt 앱 ---
        self.app = QApplication(sys.argv)
        
        # --- GUI ---
        self.dashboard = OmnissiahDashboard()
        
        # --- Core 모듈 ---
        self.bridge: Optional[IBKRBridge] = None
        self.market_data = MarketDataManager()
        self.regime_detector = RegimeDetector()
        self.risk_manager = RiskManager()
        self.universe_selector = UniverseSelector()
        self.order_executor = OrderExecutor(risk_manager=self.risk_manager)
        self.scheduler = TradingScheduler()
        
        # --- 전략 모듈 ---
        self.green_strategy = GreenModeStrategy(self.risk_manager)
        self.red_strategy = RedModeStrategy(self.risk_manager)
        self.black_strategy = BlackModeStrategy(self.risk_manager)
        
        # --- 상태 변수 ---
        self._is_running = False
        self._current_regime = "횡보"
        self._account_balance = 0.0
        self._daily_loss = 0.0
        self._current_interval = self.BASE_INTERVAL  # 현재 주기
        
        # --- 메인 타이머 (하이브리드: 5초 기본) ---
        self.main_timer = QTimer()
        self.main_timer.timeout.connect(self._trading_iteration)
        
        # --- 시그널 연결 ---
        self._connect_signals()
        
        # --- GUI 버튼 연결 ---
        self._setup_buttons()
    
    def _connect_signals(self) -> None:
        """모듈 시그널 연결"""
        # Market Data
        self.market_data.log_message.connect(self.dashboard.add_log)
        self.market_data.vix_update.connect(self._on_vix_update)
        
        # Regime Detector
        self.regime_detector.regime_changed.connect(self._on_regime_changed)
        self.regime_detector.log_message.connect(self.dashboard.add_log)
        
        # Risk Manager
        self.risk_manager.kill_switch_triggered.connect(self._on_kill_switch)
        self.risk_manager.log_message.connect(self.dashboard.add_log)
        
        # Universe Selector
        self.universe_selector.log_message.connect(self.dashboard.add_log)
        
        # Strategies
        self.green_strategy.log_message.connect(self.dashboard.add_log)
        self.red_strategy.log_message.connect(self.dashboard.add_log)
        self.black_strategy.log_message.connect(self.dashboard.add_log)
        
        # 전략 시그널 → 주문 실행 연결
        self.green_strategy.signal_generated.connect(self._execute_order)
        self.red_strategy.signal_generated.connect(self._execute_order)
        self.black_strategy.signal_generated.connect(self._execute_order)
        
        # OrderExecutor
        self.order_executor.log_message.connect(self.dashboard.add_log)
        self.order_executor.order_filled.connect(self._on_order_filled)
        self.order_executor.order_failed.connect(self._on_order_failed)
        
        # Scheduler
        self.scheduler.log_message.connect(self.dashboard.add_log)
        self.scheduler.pre_close_warn.connect(self._handle_pre_close)
        self.scheduler.market_close.connect(self._handle_market_close)
    
    def _setup_buttons(self) -> None:
        """GUI 버튼 설정"""
        self.dashboard.start_button.clicked.disconnect()
        self.dashboard.start_button.clicked.connect(self._on_start)
        
        self.dashboard.stop_button.clicked.disconnect()
        self.dashboard.stop_button.clicked.connect(self._on_stop)
    
    # ============================================
    # 시작/중지
    # ============================================
    
    def _on_start(self) -> None:
        """Start 버튼 클릭"""
        self.dashboard.add_log("▶ 시스템 시작...")
        self.dashboard.start_button.setEnabled(False)
        self.dashboard.stop_button.setEnabled(True)
        
        # --- IBKR 연결 ---
        self.bridge = IBKRBridge()
        self.bridge.connected.connect(self._on_connected)
        self.bridge.account_update.connect(self._on_account_update)
        self.bridge.error.connect(lambda x: self.dashboard.add_log(x))
        self.bridge.log_message.connect(self.dashboard.add_log)
        self.bridge.start()
        
        # --- 차트에 초기 데이터 로드 (스레드 시작 전!) ---
        self._load_initial_chart_data()
        
        # --- 시장 데이터 초기화 (백그라운드) ---
        self.market_data.start()
        
        # --- 유니버스 선정 ---
        target_etf = self.universe_selector.get_target_etf()
        self.dashboard.add_log(f"🎯 타겟 ETF: {target_etf}")
    
    def _on_stop(self) -> None:
        """Stop 버튼 클릭"""
        self.dashboard.add_log("⏹ 시스템 중지...")
        
        # 타이머 중지
        self.main_timer.stop()
        self._is_running = False
        
        # 스케줄러 중지
        self.scheduler.stop()
        
        # 브릿지 중지
        if self.bridge:
            self.bridge.stop()
            self.bridge = None
        
        self.dashboard.start_button.setEnabled(True)
        self.dashboard.stop_button.setEnabled(False)
        self.dashboard.update_connection_status(False)
    
    def _on_connected(self, connected: bool) -> None:
        """IBKR 연결 상태 변경"""
        self.dashboard.update_connection_status(connected)
        
        if connected:
            # IB 객체를 OrderExecutor에 전달
            if self.bridge and self.bridge.ib:
                self.order_executor.set_ib(self.bridge.ib)
            
            # 실시간 시세 구독 (SPY, QQQ, VIX)
            self.bridge.price_update.connect(self._on_price_update)
            self.bridge.subscribe_market_data(["SPY", "QQQ", "VIX"])
            
            # 스케줄러 시작
            self.scheduler.start()
            
            # 연결 성공 시 메인 루프 시작 (하이브리드: 5초 기본)
            self._is_running = True
            self._current_interval = self.BASE_INTERVAL
            self.main_timer.start(self._current_interval)
            self.dashboard.add_log("🔄 하이브리드 루프 시작 (5초 기본, 동적 조절)")
    
    def _on_account_update(self, info: dict) -> None:
        """계좌 정보 업데이트"""
        self._account_balance = info.get("balance", 0.0)
        self.dashboard.update_balance(self._account_balance)
    
    def _load_initial_chart_data(self) -> None:
        """
        차트에 초기 히스토리 데이터 로드
        
        로컬 DB에서 최근 50일 데이터를 가져와 차트에 표시합니다.
        """
        try:
            # DB에서 SPY 데이터 로드
            self.market_data.initialize_database()
            df = self.market_data.get_historical_prices("SPY", days=50)
            
            if df.empty:
                self.dashboard.add_log("⚠️ 차트 초기 데이터 없음")
                return
            
            # 캔들 데이터 추가
            for idx, (date, row) in enumerate(df.iterrows()):
                self.dashboard.chart_widget.add_candle(
                    time_idx=idx,
                    open_p=row["open"],
                    high=row["high"],
                    low=row["low"],
                    close=row["close"]
                )
            
            # 현재 가격 표시
            if len(df) > 0:
                last_price = df["close"].iloc[-1]
                self.dashboard.chart_widget.update_price(last_price)
            
            self.dashboard.add_log(f"📊 차트 초기 데이터 로드 완료 ({len(df)}일)")
            
        except Exception as e:
            self.dashboard.add_log(f"⚠️ 차트 데이터 로드 실패: {str(e)}")
    
    # ============================================
    # 메인 트레이딩 루프
    # ============================================
    
    def _trading_iteration(self) -> None:
        """
        하이브리드 트레이딩 루프
        
        기본 5초, |Z-Score| >= 1.0 시 1초로 전환
        VIX 급변 시 즉시 업데이트
        """
        if not self._is_running:
            return
        
        try:
            # === 1. 킬 스위치 체크 (1순위!) ===
            vix_data = self.market_data.get_vix_data()
            vix_1m = vix_data.get("front_month", 0)
            vix_3m = vix_data.get("back_month", 0)
            vix_spot = vix_data.get("spot", 0)
            
            kill_status = self.risk_manager.check_kill_switch(
                vix_1m=vix_1m,
                vix_3m=vix_3m
            )
            self.dashboard.update_kill_switch(kill_status)
            
            # === 2. 킬 스위치 발동 시 Black Mode ===
            if kill_status != "CLEAR":
                self._current_regime = "위기"
                self.dashboard.update_mode("위기")
                return
            
            # === 3. 하이브리드 Z-Score 계산 (캐시 사용) ===
            z_score = self.market_data.calculate_z_score_hybrid(vix_spot)
            
            # === 4. 동적 주기 조절 ===
            self._adjust_timer_interval(z_score)
            
            # === 5. SPY 데이터로 KER, ADX 계산 ===
            spy_df = self.market_data.get_historical_prices("SPY", days=30)
            if not spy_df.empty:
                prices = spy_df["close"].tolist()
                ker = self.regime_detector.calculate_ker(prices)
                
                if len(spy_df) >= 14:
                    adx = self.regime_detector.calculate_adx(
                        spy_df["high"].tolist(),
                        spy_df["low"].tolist(),
                        spy_df["close"].tolist()
                    )
                else:
                    adx = 0.0
                
                regime = self.regime_detector.get_regime(z_score, ker, adx)
                self._current_regime = regime
                self.dashboard.update_mode(regime)
            
            # === 6. VIX 정보 GUI 업데이트 ===
            term_structure = self.market_data.get_vix_term_structure()
            self.dashboard.update_vix_info(vix_spot, z_score, term_structure)
            
        except Exception as e:
            self.dashboard.add_log(f"❌ 루프 오류: {str(e)}")
    
    def _adjust_timer_interval(self, z_score: float) -> None:
        """
        Z-Score에 따라 타이머 주기 동적 조절
        
        |Z-Score| >= 1.0: 1초 (레짐 전환 임박)
        |Z-Score| < 1.0: 5초 (안정적)
        """
        if abs(z_score) >= self.Z_THRESHOLD:
            new_interval = self.FAST_INTERVAL
        else:
            new_interval = self.BASE_INTERVAL
        
        # 주기가 변경되었으면 타이머 재시작
        if new_interval != self._current_interval:
            self._current_interval = new_interval
            self.main_timer.setInterval(new_interval)
            interval_sec = new_interval / 1000
            self.dashboard.add_log(f"⏱ 주기 변경: {interval_sec:.0f}초 (Z={z_score:.2f})")
    
    # ============================================
    # 시그널 핸들러
    # ============================================
    
    def _on_vix_update(self, data: dict) -> None:
        """VIX 데이터 업데이트"""
        vix = data.get("spot", 0)
        z_score = data.get("z_score", 0)
        term = data.get("term_structure", "")
        self.dashboard.update_vix_info(vix, z_score, term)
    
    def _on_regime_changed(self, regime: str) -> None:
        """레짐 변경"""
        self._current_regime = regime
        self.dashboard.update_mode(regime)
        self.dashboard.add_log(f"📊 레짐 변경: {regime}")
    
    def _on_price_update(self, data: dict) -> None:
        """
        실시간 시세 업데이트
        
        Args:
            data: {symbol, bid, ask, last, volume, high, low, close}
        """
        symbol = data.get("symbol", "")
        last_price = data.get("last", 0.0)
        
        # 최신 가격 저장
        if not hasattr(self, "_last_prices"):
            self._last_prices = {}
        
        self._last_prices[symbol] = {
            "last": last_price,
            "bid": data.get("bid", 0.0),
            "ask": data.get("ask", 0.0),
        }
        
        # VIX 실시간 업데이트
        if symbol == "VIX" and last_price > 0:
            self.market_data._last_vix = last_price
        
        # 차트 업데이트 (SPY만)
        if symbol == "SPY" and last_price > 0:
            try:
                self.dashboard.chart_widget.update_price(last_price)
            except Exception:
                pass  # 차트 업데이트 실패 무시
    
    def _on_kill_switch(self, status: str) -> None:
        """킬 스위치 발동"""
        self.dashboard.update_kill_switch(status)
        if status != "CLEAR":
            self.dashboard.add_log(f"🚨 킬 스위치 발동: {status}")
    
    # ============================================
    # 주문 실행 핸들러
    # ============================================
    
    def _execute_order(self, signal: dict) -> None:
        """
        전략 시그널 → 실제 주문 실행
        
        Args:
            signal: {action, symbol, quantity, price, reason}
        """
        action = signal.get("action", "")
        symbol = signal.get("symbol", "SPY")  # 기본 심볼
        quantity = signal.get("quantity", 1)
        price = signal.get("price")
        
        self.dashboard.add_log(f"📤 주문 신호: {action} {quantity} {symbol}")
        
        if action == "BUY":
            self.order_executor.place_market_order(
                symbol=symbol,
                action="BUY",
                quantity=quantity,
                kill_status="CLEAR",
                daily_loss=self._daily_loss,
                account_balance=self._account_balance
            )
        elif action == "SELL":
            self.order_executor.place_market_order(
                symbol=symbol,
                action="SELL",
                quantity=quantity,
                kill_status="CLEAR",
                daily_loss=self._daily_loss,
                account_balance=self._account_balance
            )
    
    def _on_order_filled(self, data: dict) -> None:
        """주문 체결 완료"""
        order_id = data.get("order_id")
        fill_price = data.get("fill_price", 0)
        filled_qty = data.get("filled_qty", 0)
        symbol = data.get("symbol", "")
        
        self.dashboard.add_log(
            f"💰 체결: {symbol} {filled_qty}주 @ ${fill_price:.2f}"
        )
    
    def _on_order_failed(self, data: dict) -> None:
        """주문 실패"""
        reason = data.get("reason", "알 수 없음")
        symbol = data.get("symbol", "")
        
        self.dashboard.add_log(f"❌ 주문 실패 ({symbol}): {reason}")
    
    # ============================================
    # 스케줄러 핸들러
    # ============================================
    
    def _handle_pre_close(self) -> None:
        """장 마감 10분 전 처리 (적응형 오버나이트)"""
        self.dashboard.add_log("⏰ 장 마감 10분 전 - 적응형 오버나이트 결정")
        
        # === 위기 모드: 즉시 청산 (기존 유지) ===
        if self._current_regime == "위기":
            self.dashboard.add_log("🌑 위기 모드: 즉시 청산")
            return
        
        # === 컨텍스트 수집 (적응형 파라미터) ===
        try:
            vix_stats = self.market_data.get_vix_stats()
            atr = self.market_data.get_atr("SPY")
            daily_range = self.market_data.get_daily_range_pct("SPY")
            
            # 금요일 체크 (US Eastern)
            import pytz
            from datetime import datetime
            us_eastern = pytz.timezone("US/Eastern")
            is_friday = datetime.now(us_eastern).weekday() == 4
            
        except Exception as e:
            self.dashboard.add_log(f"⚠️ 컨텍스트 수집 실패: {e}")
            return
        
        # === 횡보 모드: 조건부 오버나이트 ===
        if self._current_regime == "횡보" and self.green_strategy.has_position():
            context = {
                "current_price": 0,  # TODO: 실시간 가격
                "entry_price": self.green_strategy._entry_price,
                "vwap": 0,  # TODO: 실시간 VWAP
                "daily_range_pct": daily_range,
                "is_friday": is_friday
            }
            
            keep = self.green_strategy.should_keep_overnight(context)
            if not keep:
                self.dashboard.add_log("🌑 횡보: 청산 실행")
                # TODO: 실제 청산 주문
        
        # === 상승 모드: 조건부 오버나이트 ===
        elif self._current_regime == "상승" and self.red_strategy.has_position():
            context = {
                "current_price": 0,  # TODO: 실시간 가격
                "ma20": 0,  # TODO: MA20
                "vix": self.market_data._last_vix if hasattr(self.market_data, '_last_vix') else 15,
                "vix_mean": vix_stats["mean"],
                "vix_std": vix_stats["std"],
                "daily_return": 0,  # TODO: 당일 수익률
                "atr": atr,
                "is_friday": is_friday
            }
            
            action = self.red_strategy.should_keep_overnight(context)
            if action == "LIQUIDATE_ALL":
                self.dashboard.add_log("🌑 상승: 전량 청산 실행")
                # TODO: 전량 청산 주문
            elif action == "KEEP_HALF":
                self.dashboard.add_log("🌓 상승: 50% 청산 실행")
                # TODO: 50% 청산 주문
    
    def _handle_market_close(self) -> None:
        """장 마감 처리"""
        self.dashboard.add_log("🔔 장 마감 - 일일 정산")
        
        # 전략 리셋
        self.green_strategy.reset()
        self.red_strategy.reset()
        self.black_strategy.reset()
        
        self.dashboard.add_log("🔄 전략 초기화 완료")
    
    # ============================================
    # 앱 실행
    # ============================================
    
    def run(self) -> int:
        """앱 실행"""
        self.dashboard.show()
        self.dashboard.add_log("🚀 Omnissiah 시스템 준비 완료")
        
        # 자동 시작 (500ms 후)
        QTimer.singleShot(500, self._on_start)
        
        return self.app.exec()


# ============================================
# 메인 실행
# ============================================
def main() -> None:
    """메인 함수"""
    controller = OmnissiahController()
    sys.exit(controller.run())


if __name__ == "__main__":
    main()
