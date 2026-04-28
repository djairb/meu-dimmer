import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QSystemTrayIcon, QMenu
)
from PyQt6.QtCore import Qt, QTimer, QPoint, QElapsedTimer
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QAction


def render_time_icon(text: str, running: bool) -> QIcon:
    """Desenha MM:SS dentro de um ícone 32x32 pro tray.
    Cor muda conforme estado: verde claro rodando, cinza pausado."""
    size = 32
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)

    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    # Fundo arredondado escuro
    p.setBrush(QColor(28, 31, 36))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(0, 0, size, size, 6, 6)

    # Texto
    color = QColor(120, 220, 150) if running else QColor(200, 200, 200)
    p.setPen(color)

    # Fonte condensada que cabe MM:SS em 32px
    font = QFont("Arial Narrow")
    font.setPointSize(9)
    font.setBold(True)
    # Fallback se Arial Narrow não existir
    if not QFont(font).exactMatch():
        font = QFont("Segoe UI")
        font.setPointSize(8)
        font.setBold(True)
    p.setFont(font)

    p.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, text)
    p.end()

    return QIcon(pix)


class FloatingWindow(QWidget):
    """Janela opcional pra ver o tempo grandão. Arrastável."""
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self._drag_pos: QPoint | None = None

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(150, 56)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        body = QWidget()
        body.setObjectName("body")
        body.setStyleSheet("""
            #body {
                background: #1c1f24;
                border: 1px solid #2e333b;
                border-radius: 10px;
            }
        """)
        outer.addWidget(body)

        row = QHBoxLayout(body)
        row.setContentsMargins(10, 6, 8, 6)
        row.setSpacing(6)

        self.time_label = QLabel("00:00")
        self.time_label.setStyleSheet(
            "color: #e6e6e6; font-family: 'Consolas', 'Menlo', monospace; "
            "font-size: 20px; font-weight: 600; background: transparent;"
        )

        btn_style = """
            QPushButton {
                background: #2a2f37; color: #e6e6e6; border: none;
                border-radius: 5px; font-size: 12px; font-weight: bold;
            }
            QPushButton:hover { background: #353b45; }
            QPushButton:pressed { background: #1f242b; }
        """
        self.btn_toggle = QPushButton("▶")
        self.btn_toggle.setFixedSize(26, 26)
        self.btn_toggle.setStyleSheet(btn_style)
        self.btn_toggle.setToolTip("Iniciar / Pausar")
        self.btn_toggle.clicked.connect(self.controller.toggle)

        self.btn_reset = QPushButton("⟲")
        self.btn_reset.setFixedSize(26, 26)
        self.btn_reset.setStyleSheet(btn_style)
        self.btn_reset.setToolTip("Recomeçar")
        self.btn_reset.clicked.connect(self.controller.reset)

        row.addWidget(self.time_label, 1)
        row.addWidget(self.btn_toggle)
        row.addWidget(self.btn_reset)

        # Posição inicial: canto superior direito
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - self.width() - 20, 20)

    def update_display(self, text: str, running: bool):
        self.time_label.setText(text)
        self.btn_toggle.setText("⏸" if running else "▶")

    # Arrastar
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        event.accept()

    def closeEvent(self, event):
        # Fechar a janela só esconde — o app continua no tray
        event.ignore()
        self.hide()


class StopwatchController:
    """Lógica do cronômetro + tray + janela flutuante."""
    def __init__(self, app: QApplication):
        self.app = app
        self.elapsed = QElapsedTimer()
        self.accumulated_ms = 0
        self.running = False

        self.window = FloatingWindow(self)

        # Tray
        self.tray = QSystemTrayIcon()
        self.tray.setIcon(render_time_icon("00:00", False))
        self.tray.setToolTip("Cronômetro: 00:00 (pausado)")

        menu = QMenu()
        menu.setStyleSheet(
            "QMenu { background: #1e1e1e; color: white; border: 1px solid #444; }"
            "QMenu::item:selected { background: #3a3a3a; }"
        )

        self.act_toggle = QAction("Iniciar")
        self.act_toggle.triggered.connect(self.toggle)
        menu.addAction(self.act_toggle)

        act_reset = QAction("Recomeçar")
        act_reset.triggered.connect(self.reset)
        menu.addAction(act_reset)

        menu.addSeparator()

        act_show = QAction("Mostrar janela flutuante")
        act_show.triggered.connect(self.show_window)
        menu.addAction(act_show)

        act_hide = QAction("Esconder janela flutuante")
        act_hide.triggered.connect(self.window.hide)
        menu.addAction(act_hide)

        menu.addSeparator()

        act_quit = QAction("Sair")
        act_quit.triggered.connect(self.app.quit)
        menu.addAction(act_quit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.on_tray_activated)
        self.tray.show()

        # Tick — 4x/seg pra atualização suave do ícone sem gastar CPU
        self.tick = QTimer()
        self.tick.timeout.connect(self.refresh)
        self.tick.start(250)

    def on_tray_activated(self, reason):
        # Clique simples no ícone: alterna play/pause
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle()
        # Clique duplo: mostra/esconde janela flutuante
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.window.isVisible():
                self.window.hide()
            else:
                self.show_window()

    def show_window(self):
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def current_ms(self) -> int:
        if self.running:
            return self.accumulated_ms + self.elapsed.elapsed()
        return self.accumulated_ms

    def format_time(self) -> str:
        total_s = self.current_ms() // 1000
        m = total_s // 60
        s = total_s % 60
        # Pomodoro vai até ~50min, então MM:SS basta. Se passar de 99min, trunca.
        if m > 99:
            m = 99
        return f"{m:02d}:{s:02d}"

    def toggle(self):
        if self.running:
            self.accumulated_ms += self.elapsed.elapsed()
            self.running = False
            self.act_toggle.setText("Iniciar")
        else:
            self.elapsed.restart()
            self.running = True
            self.act_toggle.setText("Pausar")
        self.refresh()

    def reset(self):
        self.running = False
        self.accumulated_ms = 0
        self.act_toggle.setText("Iniciar")
        self.refresh()

    def refresh(self):
        text = self.format_time()
        self.tray.setIcon(render_time_icon(text, self.running))
        status = "rodando" if self.running else "pausado"
        self.tray.setToolTip(f"Cronômetro: {text} ({status})")
        self.window.update_display(text, self.running)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    controller = StopwatchController(app)
    sys.exit(app.exec())