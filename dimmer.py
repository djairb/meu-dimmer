import sys
import ctypes
from ctypes import wintypes, Structure, POINTER, byref, c_float
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSystemTrayIcon, QMenu
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QAction

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
mag = ctypes.windll.LoadLibrary("Magnification.dll")

shcore = ctypes.windll.shcore
try:
    shcore.SetProcessDpiAwareness(2)
except Exception:
    user32.SetProcessDPIAware()

# ---- Magnification API ----
class MAGCOLOREFFECT(Structure):
    _fields_ = [("transform", c_float * 25)]

MagInitialize = mag.MagInitialize
MagInitialize.restype = wintypes.BOOL
MagUninitialize = mag.MagUninitialize
MagUninitialize.restype = wintypes.BOOL
MagSetFullscreenColorEffect = mag.MagSetFullscreenColorEffect
MagSetFullscreenColorEffect.argtypes = [POINTER(MAGCOLOREFFECT)]
MagSetFullscreenColorEffect.restype = wintypes.BOOL

WS_EX_TOPMOST = 0x00000008
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080
WS_POPUP = 0x80000000

CreateWindowExW = user32.CreateWindowExW
CreateWindowExW.argtypes = [
    wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR,
    wintypes.DWORD, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID
]
CreateWindowExW.restype = wintypes.HWND

GetModuleHandleW = kernel32.GetModuleHandleW
GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
GetModuleHandleW.restype = wintypes.HMODULE


def make_dim_matrix(level: float) -> MAGCOLOREFFECT:
    factor = max(0.0, 1.0 - level)
    m = MAGCOLOREFFECT()
    for i in range(25):
        m.transform[i] = 0.0
    m.transform[0]  = factor
    m.transform[6]  = factor
    m.transform[12] = factor
    m.transform[18] = 1.0
    m.transform[24] = 1.0
    return m


def make_tray_icon() -> QIcon:
    """Ícone simples: círculo escuro com um 'D' — gerado em runtime,
    sem depender de arquivo externo."""
    pix = QPixmap(64, 64)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor(20, 20, 20))
    p.setPen(QColor(200, 200, 200))
    p.drawEllipse(4, 4, 56, 56)
    p.setPen(QColor(255, 255, 255))
    f = p.font()
    f.setBold(True)
    f.setPointSize(28)
    p.setFont(f)
    p.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, "D")
    p.end()
    return QIcon(pix)


class ControlPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.opacity = 0.5
        self.host_hwnd = None
        self.tray = None

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setFixedSize(170, 240)
        self.setStyleSheet(
            "background: #121212; border: 2px solid #444; border-radius: 12px; "
            "color: white; font-family: sans-serif;"
        )

        layout = QVBoxLayout()

        # Barra de topo: minimizar + fechar
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)
        btn_min = QPushButton("—")
        btn_min.setFixedSize(24, 24)
        btn_min.setStyleSheet(
            "background: #2a2a2a; border: none; border-radius: 4px; "
            "color: white; font-weight: bold;"
        )
        btn_min.setToolTip("Minimizar para a bandeja")
        btn_min.clicked.connect(self.hide_to_tray)
        top_bar.addStretch()
        top_bar.addWidget(btn_min)
        layout.addLayout(top_bar)

        self.label = QLabel(f"{int(self.opacity * 100)}%")
        self.label.setStyleSheet("font-size: 26px; border: none; font-weight: bold;")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        info = QLabel("Scroll para Dim")
        info.setStyleSheet("font-size: 10px; color: #888; border: none;")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.status = QLabel("inicializando…")
        self.status.setStyleSheet("font-size: 9px; color: #4caf50; border: none;")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_exit = QPushButton("Fechar App")
        btn_exit.setStyleSheet(
            "background: #d32f2f; border: none; padding: 8px; "
            "font-weight: bold; margin-top: 10px; border-radius: 4px;"
        )
        btn_exit.clicked.connect(self._quit)

        layout.addWidget(self.label)
        layout.addWidget(info)
        layout.addStretch()
        layout.addWidget(self.status)
        layout.addWidget(btn_exit)
        self.setLayout(layout)

        self.reposition()
        self.setup_tray()
        self.show()

        QTimer.singleShot(100, self.init_magnification)

    # ---------- Tray ----------
    def setup_tray(self):
        icon = make_tray_icon()
        self.tray = QSystemTrayIcon(icon, self)
        self.tray.setToolTip("Dimmer")

        menu = QMenu()
        menu.setStyleSheet(
            "QMenu { background: #1e1e1e; color: white; border: 1px solid #444; }"
            "QMenu::item:selected { background: #3a3a3a; }"
        )

        act_show = QAction("Mostrar painel", self)
        act_show.triggered.connect(self.show_from_tray)
        menu.addAction(act_show)

        menu.addSeparator()

        # Atalhos rápidos de nível
        for pct in (0, 25, 50, 75, 100):
            a = QAction(f"Dim {pct}%", self)
            a.triggered.connect(lambda checked=False, p=pct: self.set_level(p / 100))
            menu.addAction(a)

        menu.addSeparator()

        act_quit = QAction("Sair", self)
        act_quit.triggered.connect(self._quit)
        menu.addAction(act_quit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.on_tray_activated)
        self.tray.show()

    def on_tray_activated(self, reason):
        # Clique simples ou duplo no ícone -> alterna visibilidade
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            if self.isVisible():
                self.hide_to_tray()
            else:
                self.show_from_tray()

    def hide_to_tray(self):
        self.hide()
        if self.tray:
            self.tray.showMessage(
                "Dimmer",
                "Continuo rodando aqui na bandeja.",
                QSystemTrayIcon.MessageIcon.Information,
                2000,
            )

    def show_from_tray(self):
        self.reposition()
        self.show()
        self.raise_()
        self.activateWindow()

    # ---------- Magnification ----------
    def init_magnification(self):
        if not MagInitialize():
            err = ctypes.get_last_error()
            self.status.setText(f"MagInit falhou ({err})")
            self.status.setStyleSheet("font-size: 9px; color: #f44336; border: none;")
            return

        hinstance = GetModuleHandleW(None)
        self.host_hwnd = CreateWindowExW(
            WS_EX_TOPMOST | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW,
            "Magnifier",
            "DimHost",
            WS_POPUP,
            0, 0, 0, 0,
            None, None, hinstance, None,
        )

        if not self.host_hwnd:
            err = ctypes.get_last_error()
            self.status.setText(f"Host falhou ({err})")
            self.status.setStyleSheet("font-size: 9px; color: #f44336; border: none;")
            return

        if self.apply_dim():
            self.status.setText("ativo")
        else:
            self.status.setText("SetEffect retornou 0")
            self.status.setStyleSheet("font-size: 9px; color: #ff9800; border: none;")

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.apply_dim)
        self.timer.start(500)

    def reposition(self):
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 200, screen.height() - 300)

    def apply_dim(self) -> bool:
        m = make_dim_matrix(self.opacity)
        return bool(MagSetFullscreenColorEffect(byref(m)))

    def set_level(self, value: float):
        self.opacity = max(0.0, min(1.0, value))
        self.label.setText(f"{int(self.opacity * 100)}%")
        self.apply_dim()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        change = 0.02 if delta > 0 else -0.02
        self.set_level(self.opacity + change)

    # ---------- Saída ----------
    def _quit(self):
        self.opacity = 0.0
        self.apply_dim()
        MagUninitialize()
        if self.tray:
            self.tray.hide()
        QApplication.instance().quit()

    def closeEvent(self, event):
        # Fechar (Alt+F4 etc.) -> esconde pra tray em vez de sair
        event.ignore()
        self.hide_to_tray()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # essencial pra ficar vivo na tray
    ctrl = ControlPanel()
    sys.exit(app.exec())