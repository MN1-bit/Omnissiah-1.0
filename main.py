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
            # 연결 성공 시 메인 루프 시작 (하이브리드: 5초 기본)
            self._is_running = True
            self._current_interval = self.BASE_INTERVAL
            self.main_timer.start(self._current_interval)
            self.dashboard.add_log("🔄 하이브리드 루프 시작 (5초 기본, 동적 조절)")
    
    def _on_account_update(self, info: dict) -> None:
        """계좌 정보 업데이트"""
        self._account_balance = info.get("balance", 0.0)
        self.dashboard.update_balance(self._account_balance)
    
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
    
    def _on_kill_switch(self, status: str) -> None:
        """킬 스위치 발동"""
        self.dashboard.update_kill_switch(status)
        if status != "CLEAR":
            self.dashboard.add_log(f"🚨 킬 스위치 발동: {status}")
    
    # ============================================
    # 앱 실행
    # ============================================
    
    def run(self) -> int:
        """앱 실행"""
        self.dashboard.show()
        self.dashboard.add_log("🚀 Omnissiah 시스템 준비 완료")
        self.dashboard.add_log("▶ Start 버튼을 눌러 시작하세요")
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
