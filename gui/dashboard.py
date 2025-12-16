"""
============================================
Omnissiah 모니터링 대시보드
============================================
PyQt6 기반 실시간 모니터링 GUI

주요 기능:
- 연결 상태 표시
- 현재 레짐(Green/Red/Black) 표시
- 실시간 로그 출력
- 시작/중지 버튼
============================================
"""

# ============================================
# 필수 라이브러리 임포트
# ============================================
import sys                              # 시스템 관련
from datetime import datetime           # 시간 처리
from PyQt6.QtWidgets import (           # PyQt6 위젯들
    QApplication,                       # 앱 객체
    QMainWindow,                        # 메인 창
    QWidget,                            # 기본 위젯
    QVBoxLayout,                        # 수직 레이아웃
    QHBoxLayout,                        # 수평 레이아웃
    QLabel,                             # 텍스트 라벨
    QPushButton,                        # 버튼
    QTextEdit,                          # 텍스트 에디터 (로그용)
    QFrame,                             # 프레임 (구분선)
    QGroupBox,                          # 그룹 박스
)
from PyQt6.QtCore import Qt, QTimer     # Qt 코어 기능
from PyQt6.QtGui import QFont           # 폰트 설정


class OmnissiahDashboard(QMainWindow):
    """
    Omnissiah 메인 모니터링 대시보드
    
    이 클래스는 전체 GUI의 메인 창을 담당합니다.
    시스템의 상태를 실시간으로 표시하고 제어합니다.
    """
    
    def __init__(self) -> None:
        """대시보드 초기화"""
        super().__init__()
        
        # --- 창 기본 설정 ---
        self.setWindowTitle("Omnissiah Monitor")  # 창 제목
        self.setGeometry(100, 100, 1200, 800)     # 위치(x,y), 크기(w,h)
        self.setMinimumSize(800, 600)             # 최소 크기
        
        # --- 다크 테마 스타일 적용 ---
        self._apply_dark_theme()
        
        # --- UI 구성 ---
        self._setup_ui()
        
        # --- 초기 로그 메시지 ---
        self.add_log("🚀 Omnissiah Monitor 시작됨")
        self.add_log("⏳ 시스템 대기 중...")
    
    def _apply_dark_theme(self) -> None:
        """다크 테마 스타일시트 적용"""
        # PyQt6 네이티브 스타일시트 (qdarktheme 대체)
        dark_style = """
            QMainWindow {
                background-color: #1e1e1e;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Segoe UI', sans-serif;
                font-size: 12px;
            }
            QGroupBox {
                border: 1px solid #3c3c3c;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #0e639c;
                border: none;
                border-radius: 3px;
                padding: 8px 16px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:pressed {
                background-color: #0d5a8c;
            }
            QPushButton:disabled {
                background-color: #3c3c3c;
                color: #808080;
            }
            QTextEdit {
                background-color: #252526;
                border: 1px solid #3c3c3c;
                border-radius: 3px;
                padding: 5px;
                font-family: 'Consolas', monospace;
            }
            QLabel {
                border: none;
            }
        """
        self.setStyleSheet(dark_style)
    
    def _setup_ui(self) -> None:
        """UI 레이아웃 구성"""
        # --- 중앙 위젯 ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # --- 메인 레이아웃 (수평) ---
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # === 왼쪽 패널: 상태 표시 ===
        left_panel = self._create_status_panel()
        main_layout.addWidget(left_panel, stretch=1)
        
        # === 오른쪽 패널: 로그 + 버튼 ===
        right_panel = self._create_log_panel()
        main_layout.addWidget(right_panel, stretch=3)
    
    def _create_status_panel(self) -> QGroupBox:
        """왼쪽 상태 패널 생성"""
        group = QGroupBox("📊 시스템 상태")
        layout = QVBoxLayout(group)
        layout.setSpacing(15)
        
        # --- 연결 상태 ---
        self.connection_label = QLabel("연결: 🔴 끊김")
        self.connection_label.setFont(QFont("Segoe UI", 14))
        layout.addWidget(self.connection_label)
        
        # --- 현재 모드 ---
        self.mode_label = QLabel("모드: ⬜ 대기중")
        self.mode_label.setFont(QFont("Segoe UI", 14))
        layout.addWidget(self.mode_label)
        
        # --- 계좌 잔고 ---
        self.balance_label = QLabel("잔고: $0.00")
        self.balance_label.setFont(QFont("Segoe UI", 14))
        layout.addWidget(self.balance_label)
        
        # --- 구분선 ---
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #3c3c3c;")
        layout.addWidget(line)
        
        # --- VIX 정보 ---
        self.vix_label = QLabel("VIX: --")
        layout.addWidget(self.vix_label)
        
        self.zscore_label = QLabel("Z-Score: --")
        layout.addWidget(self.zscore_label)
        
        self.term_structure_label = QLabel("Term: --")
        layout.addWidget(self.term_structure_label)
        
        # --- 구분선 ---
        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setStyleSheet("background-color: #3c3c3c;")
        layout.addWidget(line2)
        
        # --- 킬 스위치 상태 ---
        self.kill_switch_label = QLabel("킬스위치: ✅ 정상")
        self.kill_switch_label.setStyleSheet("color: #4ec9b0;")
        layout.addWidget(self.kill_switch_label)
        
        # 남은 공간 채우기
        layout.addStretch()
        
        return group
    
    def _create_log_panel(self) -> QWidget:
        """오른쪽 로그 패널 생성"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)
        
        # --- 로그 그룹 ---
        log_group = QGroupBox("📋 실시간 로그")
        log_layout = QVBoxLayout(log_group)
        
        # 로그 텍스트 에디터
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)  # 읽기 전용
        self.log_text.setFont(QFont("Consolas", 10))
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_group, stretch=1)
        
        # --- 버튼 영역 ---
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Start 버튼
        self.start_button = QPushButton("▶ Start")
        self.start_button.setMinimumWidth(100)
        self.start_button.clicked.connect(self._on_start_clicked)
        button_layout.addWidget(self.start_button)
        
        # Stop 버튼
        self.stop_button = QPushButton("⏹ Stop")
        self.stop_button.setMinimumWidth(100)
        self.stop_button.setEnabled(False)  # 초기에는 비활성화
        self.stop_button.clicked.connect(self._on_stop_clicked)
        button_layout.addWidget(self.stop_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        return panel
    
    # ============================================
    # 공개 메서드 (다른 모듈에서 호출)
    # ============================================
    
    def add_log(self, message: str) -> None:
        """
        로그 메시지 추가
        
        Args:
            message: 로그에 표시할 메시지
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {message}"
        self.log_text.append(formatted)
        
        # 자동 스크롤
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def update_connection_status(self, connected: bool) -> None:
        """
        연결 상태 업데이트
        
        Args:
            connected: True면 연결됨, False면 끊김
        """
        if connected:
            self.connection_label.setText("연결: 🟢 연결됨")
            self.connection_label.setStyleSheet("color: #4ec9b0;")
        else:
            self.connection_label.setText("연결: 🔴 끊김")
            self.connection_label.setStyleSheet("color: #f14c4c;")
    
    def update_mode(self, mode: str) -> None:
        """
        현재 모드 업데이트
        
        Args:
            mode: "횡보", "상승", "위기" 중 하나
        """
        mode_colors = {
            "횡보": ("🟡 횡보", "#FFD700"),    # Yellow (저변동성, 평균회귀)
            "상승": ("🔵 상승", "#00CED1"),    # Cyan/Teal (추세 추종)
            "위기": ("🔴 위기", "#FF4444"),    # Red (공포, 방어)
        }
        
        text, color = mode_colors.get(mode, ("⬜ 대기중", "#d4d4d4"))
        self.mode_label.setText(f"모드: {text}")
        self.mode_label.setStyleSheet(f"color: {color};")
    
    def update_balance(self, balance: float) -> None:
        """
        계좌 잔고 업데이트
        
        Args:
            balance: 계좌 잔고 (USD)
        """
        self.balance_label.setText(f"잔고: ${balance:,.2f}")
    
    def update_vix_info(self, vix: float, zscore: float, term: str) -> None:
        """
        VIX 정보 업데이트
        
        Args:
            vix: VIX 현물가
            zscore: VIX Z-Score
            term: "CONTANGO" 또는 "BACKWARDATION"
        """
        self.vix_label.setText(f"VIX: {vix:.2f}")
        self.zscore_label.setText(f"Z-Score: {zscore:.2f}")
        self.term_structure_label.setText(f"Term: {term}")
    
    def update_kill_switch(self, status: str) -> None:
        """
        킬 스위치 상태 업데이트
        
        Args:
            status: "CLEAR", "HALT_ALL", "HALT_LONG", "HALT_NEW" 중 하나
        """
        if status == "CLEAR":
            self.kill_switch_label.setText("킬스위치: ✅ 정상")
            self.kill_switch_label.setStyleSheet("color: #4ec9b0;")
        else:
            self.kill_switch_label.setText(f"킬스위치: ⛔ {status}")
            self.kill_switch_label.setStyleSheet("color: #f14c4c;")
    
    # ============================================
    # 버튼 이벤트 핸들러
    # ============================================
    
    def _on_start_clicked(self) -> None:
        """Start 버튼 클릭 시"""
        self.add_log("▶ 시스템 시작됨")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        # TODO: 실제 시스템 시작 로직 연결
    
    def _on_stop_clicked(self) -> None:
        """Stop 버튼 클릭 시"""
        self.add_log("⏹ 시스템 중지됨")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        # TODO: 실제 시스템 중지 로직 연결


# ============================================
# 단위 테스트 (이 파일을 직접 실행할 때)
# ============================================
if __name__ == "__main__":
    # 앱 생성
    app = QApplication(sys.argv)
    
    # 대시보드 생성 및 표시
    dashboard = OmnissiahDashboard()
    dashboard.show()
    
    # 테스트: 3초 후 상태 변경
    def test_updates():
        dashboard.update_connection_status(True)
        dashboard.update_mode("횡보")
        dashboard.update_balance(10523.45)
        dashboard.update_vix_info(18.5, 0.75, "CONTANGO")
        dashboard.add_log("✅ 테스트 업데이트 완료")
    
    QTimer.singleShot(3000, test_updates)  # 3초 후 실행
    
    # 앱 실행
    sys.exit(app.exec())
