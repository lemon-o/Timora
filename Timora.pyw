"""
Timora - Win11 自动关机工具
支持：指定时间关机 / 倒计时关机 / 取消关机 / 阻止睡眠
"""

import sys
import os
import ctypes
import subprocess
from datetime import datetime, timedelta
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QTabWidget,
    QVBoxLayout, QHBoxLayout, QTimeEdit, QSpinBox, QFrame,
    QGraphicsDropShadowEffect, QCheckBox
)
from PyQt5.QtCore import Qt, QTimer, QTime, pyqtSignal, QRectF
from PyQt5.QtGui import QColor, QIcon, QPainter, QPainterPath

# ─────────────────────────── 颜色常量 ────────────────────────────

BG_DARK      = "#0a0e1a"
BG_CARD      = "#111827"
BG_CARD2     = "#151f30"
BG_CARD3     = "#1a2540"
ACCENT_BLUE  = "#3b82f6"
ACCENT_CYAN  = "#06b6d4"
ACCENT_RED   = "#ef4444"
TEXT_PRIMARY = "#f1f5f9"
TEXT_MUTED   = "#4e6180"
TEXT_DIM     = "#2a3a52"
BORDER       = "#1e2d42"

R = "12px"

# ─────────────────────── 路径辅助 ────────────────────────────────

def _app_dir() -> str:
    """
    返回「程序工作目录」：
    - PyInstaller 打包后：exe 文件所在目录（icon 文件夹需与 exe 同级）
    - 源码直接运行：脚本文件所在目录
    """
    if getattr(sys, "frozen", False):
        # 打包后 sys.executable 就是 exe 本身
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))

# ─────────────────────────── 样式表 ──────────────────────────────

STYLE_SHEET = f"""
QWidget {{
    background-color: {BG_DARK};
    color: {TEXT_PRIMARY};
    font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
}}

QTabWidget::pane {{
    border: none;
    background: transparent;
}}

QTabBar {{
    background: transparent;
}}
QTabBar::tab {{
    background: transparent;
    color: {TEXT_MUTED};
    padding: 11px 36px;
    font-size: 13px;
    font-weight: 600;
    border: none;
    border-bottom: 2px solid transparent;
    letter-spacing: 0.3px;
}}
QTabBar::tab:selected {{
    color: {ACCENT_CYAN};
    border-bottom: 2px solid {ACCENT_CYAN};
}}
QTabBar::tab:hover:!selected {{
    color: {TEXT_PRIMARY};
}}

QTimeEdit, QSpinBox {{
    background: {BG_CARD2};
    border: 1.5px solid {BORDER};
    border-radius: {R};
    color: {TEXT_PRIMARY};
    font-size: 26px;
    font-weight: 700;
    padding: 10px 12px;
    selection-background-color: {ACCENT_BLUE};
}}
QTimeEdit:focus, QSpinBox:focus {{
    border: 1.5px solid {ACCENT_CYAN};
    background: {BG_CARD3};
}}
QTimeEdit::up-button, QTimeEdit::down-button,
QSpinBox::up-button,  QSpinBox::down-button {{
    width: 22px;
    border-radius: 6px;
    background: {BG_CARD};
    border: 1px solid {TEXT_DIM};
    margin: 3px 4px 3px 0;
}}
QTimeEdit::up-button:hover,  QTimeEdit::down-button:hover,
QSpinBox::up-button:hover,   QSpinBox::down-button:hover {{
    background: {ACCENT_BLUE};
    border-color: {ACCENT_BLUE};
}}
QTimeEdit::up-arrow, QSpinBox::up-arrow {{
    image: url({{UP_ARROW_PATH}});
    width: 8px;
    height: 6px;
}}
QTimeEdit::down-arrow, QSpinBox::down-arrow {{
    image: url({{DOWN_ARROW_PATH}});
    width: 8px;
    height: 6px;
}}

QLabel#title {{
    font-size: 21px;
    font-weight: 800;
    color: {TEXT_PRIMARY};
    letter-spacing: 0.5px;
}}
QLabel#subtitle {{
    font-size: 10px;
    color: {TEXT_MUTED};
    letter-spacing: 2.5px;
}}
QLabel#countdown_label {{
    font-size: 50px;
    font-weight: 900;
    color: {TEXT_PRIMARY};
    letter-spacing: 3px;
}}
QLabel#status_label {{
    font-size: 12px;
    color: {TEXT_MUTED};
}}
QLabel#section_label {{
    font-size: 10px;
    font-weight: 700;
    color: {TEXT_MUTED};
    letter-spacing: 2px;
}}

QPushButton#btn_primary {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT_BLUE}, stop:1 {ACCENT_CYAN});
    color: white;
    border: none;
    border-radius: {R};
    font-size: 13px;
    font-weight: 700;
    padding: 0 24px;
    letter-spacing: 0.5px;
}}
QPushButton#btn_primary:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #2563eb, stop:1 #0891b2);
}}
QPushButton#btn_primary:pressed {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #1d4ed8, stop:1 #0e7490);
}}
QPushButton#btn_primary:disabled {{
    background: {BG_CARD2};
    color: {TEXT_DIM};
}}

QPushButton#btn_cancel {{
    background: transparent;
    color: {ACCENT_RED};
    border: 1.5px solid rgba(239,68,68,0.4);
    border-radius: {R};
    font-size: 13px;
    font-weight: 700;
    padding: 0 24px;
}}
QPushButton#btn_cancel:hover {{
    background: rgba(239,68,68,0.08);
    border-color: {ACCENT_RED};
}}
QPushButton#btn_cancel:disabled {{
    color: {TEXT_DIM};
    border-color: {TEXT_DIM};
}}

QFrame#card {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 18px;
}}

QFrame#sleep_bar {{
    background: {BG_CARD2};
    border: 1px solid {BORDER};
    border-radius: {R};
}}

QCheckBox {{
    font-size: 13px;
    font-weight: 600;
    color: {TEXT_PRIMARY};
    spacing: 8px;
    background: transparent;
}}
QCheckBox::indicator {{
    width: 17px;
    height: 17px;
    border-radius: 5px;
    border: 1.5px solid {TEXT_MUTED};
    background: {BG_CARD};
}}
QCheckBox::indicator:checked {{
    background: {ACCENT_CYAN};
    border-color: {ACCENT_CYAN};
}}
QCheckBox::indicator:hover {{
    border-color: {ACCENT_CYAN};
}}

QPushButton#btn_quick {{
    background: {BG_CARD2};
    color: {TEXT_MUTED};
    border: 1px solid {BORDER};
    border-radius: {R};
    font-size: 12px;
    font-weight: 600;
}}
QPushButton#btn_quick:hover {{
    color: {ACCENT_CYAN};
    border-color: {ACCENT_CYAN};
    background: rgba(6,182,212,0.07);
}}
"""

# ──────────────────── 防睡眠 ────────────────────

_ES_AWAKE = 0x80000003

def set_sleep_prevention(enabled: bool):
    try:
        if enabled:
            ctypes.windll.kernel32.SetThreadExecutionState(_ES_AWAKE)
        else:
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
    except Exception:
        pass

def make_sleep_bar():
    frame = QFrame()
    frame.setObjectName("sleep_bar")
    frame.setFixedHeight(46)
    row = QHBoxLayout(frame)
    row.setContentsMargins(14, 0, 14, 0)
    row.setSpacing(10)
    # moon = QLabel("🌙")
    # moon.setStyleSheet("font-size:14px; background:transparent;")
    # row.addWidget(moon)
    cb = QCheckBox("阻止电脑进入睡眠")
    row.addWidget(cb)
    row.addStretch()
    hint = QLabel("计划期间保持唤醒")
    hint.setStyleSheet(f"font-size:11px; color:{TEXT_MUTED}; background:transparent;")
    row.addWidget(hint)
    return frame, cb

# ─────────────────────── 指定时间 Tab ─────────────────────────

class ScheduleTab(QWidget):
    shutdown_requested = pyqtSignal(int)
    cancel_requested   = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._active    = False
        self._remaining = 0
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(12)

        # 标签
        lbl = QLabel("选择关机时刻")
        lbl.setObjectName("section_label")
        root.addWidget(lbl)

        # 时间选择器
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH : mm : ss")
        self.time_edit.setTime(QTime.currentTime().addSecs(600))
        self.time_edit.setAlignment(Qt.AlignCenter)
        self.time_edit.setFixedHeight(64)
        root.addWidget(self.time_edit)

        # 当前时间提示
        self.now_label = QLabel()
        self.now_label.setObjectName("status_label")
        self.now_label.setAlignment(Qt.AlignCenter)
        root.addWidget(self.now_label)

        root.addSpacing(16)

        # 倒计时大字
        self.countdown_label = QLabel("--:--:--")
        self.countdown_label.setObjectName("countdown_label")
        self.countdown_label.setAlignment(Qt.AlignCenter)
        root.addWidget(self.countdown_label)

        self.status_label = QLabel("尚未设置关机计划")
        self.status_label.setObjectName("status_label")
        self.status_label.setAlignment(Qt.AlignCenter)
        root.addWidget(self.status_label)

        root.addStretch()

        # 防睡眠
        sleep_frame, self.sleep_cb = make_sleep_bar()
        self.sleep_cb.stateChanged.connect(self._on_sleep_toggled)
        root.addWidget(sleep_frame)
        root.addSpacing(10)

        # 按钮
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        self.btn_start = QPushButton("⏻   立即设定")
        self.btn_start.setObjectName("btn_primary")
        self.btn_start.setFixedHeight(48)
        self.btn_start.clicked.connect(self._on_start)

        self.btn_cancel = QPushButton("✕   取消关机")
        self.btn_cancel.setObjectName("btn_cancel")
        self.btn_cancel.setFixedHeight(48)
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self._on_cancel)

        btn_row.addWidget(self.btn_start)
        btn_row.addWidget(self.btn_cancel)
        root.addLayout(btn_row)

        self._clock_timer = QTimer(self)
        self._clock_timer.setInterval(1000)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start()
        self._update_clock()

    def _on_sleep_toggled(self, state):
        if self._active:
            set_sleep_prevention(state == Qt.Checked)

    def _update_clock(self):
        self.now_label.setText(f"当前时间  {datetime.now().strftime('%H:%M:%S')}")

    def _on_start(self):
        t = self.time_edit.time()
        target = datetime.now().replace(
            hour=t.hour(), minute=t.minute(), second=t.second(), microsecond=0
        )
        if target <= datetime.now():
            target += timedelta(days=1)
        self._remaining = int((target - datetime.now()).total_seconds())
        self._active = True
        self._timer.start()
        if self.sleep_cb.isChecked():
            set_sleep_prevention(True)
        self.btn_start.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.time_edit.setEnabled(False)
        self.sleep_cb.setEnabled(False)
        self._freeze_tabs(True)
        h = self._remaining // 3600
        m = (self._remaining % 3600) // 60
        s = self._remaining % 60
        self.countdown_label.setText(f"{h:02d}:{m:02d}:{s:02d}")
        self.status_label.setText(f"将在 {t.toString('HH:mm:ss')} 自动关机")
        self.shutdown_requested.emit(self._remaining)

    def _on_cancel(self):
        self._active = False
        self._timer.stop()
        self._remaining = 0
        set_sleep_prevention(False)
        self.countdown_label.setText("--:--:--")
        self.status_label.setText("关机计划已取消")
        self.btn_start.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.time_edit.setEnabled(True)
        self.sleep_cb.setEnabled(True)
        self._freeze_tabs(False)
        self.cancel_requested.emit()

    def _freeze_tabs(self, frozen: bool):
        """冻结/解冻 Tab 切换"""
        try:
            tab_widget = self.parent().parent()
            if hasattr(tab_widget, 'tabBar'):
                tab_widget.tabBar().setEnabled(not frozen)
        except Exception:
            pass

    def _tick(self):
        self._remaining -= 1
        if self._remaining <= 0:
            self._timer.stop()
            set_sleep_prevention(False)
            self.countdown_label.setText("00:00:00")
            self.status_label.setText("正在关机…")
            return
        h = self._remaining // 3600
        m = (self._remaining % 3600) // 60
        s = self._remaining % 60
        self.countdown_label.setText(f"{h:02d}:{m:02d}:{s:02d}")


# ─────────────────────── 倒计时 Tab ──────────────────────────

class CountdownTab(QWidget):
    shutdown_requested = pyqtSignal(int)
    cancel_requested   = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._active    = False
        self._total     = 0
        self._remaining = 0
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(12)

        lbl = QLabel("设置倒计时时长")
        lbl.setObjectName("section_label")
        root.addWidget(lbl)

        # 时 / 分 / 秒
        hms = QHBoxLayout()
        hms.setSpacing(8)

        def make_spin(max_val, suffix):
            sp = QSpinBox()
            sp.setRange(0, max_val)
            sp.setSuffix(suffix)
            sp.setFixedHeight(64)
            sp.setAlignment(Qt.AlignCenter)
            return sp

        self.h_spin = make_spin(999, " 时")
        self.m_spin = make_spin(59,  " 分")
        self.s_spin = make_spin(59,  " 秒")
        self.m_spin.setValue(30)
        hms.addWidget(self.h_spin)
        hms.addWidget(self.m_spin)
        hms.addWidget(self.s_spin)
        root.addLayout(hms)

        root.addSpacing(8)

        # 快捷按钮
        self._quick_btns = []
        quick_row = QHBoxLayout()
        quick_row.setSpacing(8)
        for label, mins in [("15 分", 15), ("30 分", 30), ("1 小时", 60), ("2 小时", 120)]:
            btn = QPushButton(label)
            btn.setObjectName("btn_quick")
            btn.setFixedHeight(34)
            btn.clicked.connect(lambda _, m=mins: self._set_quick(m))
            quick_row.addWidget(btn)
            self._quick_btns.append(btn)
        root.addLayout(quick_row)

        root.addSpacing(20)

        # 倒计时大字
        self.countdown_label = QLabel("--:--:--")
        self.countdown_label.setObjectName("countdown_label")
        self.countdown_label.setAlignment(Qt.AlignCenter)
        root.addWidget(self.countdown_label)

        self.status_label = QLabel("尚未开始倒计时")
        self.status_label.setObjectName("status_label")
        self.status_label.setAlignment(Qt.AlignCenter)
        root.addWidget(self.status_label)

        root.addStretch()

        # 防睡眠
        sleep_frame, self.sleep_cb = make_sleep_bar()
        self.sleep_cb.stateChanged.connect(self._on_sleep_toggled)
        root.addWidget(sleep_frame)
        root.addSpacing(10)

        # 按钮
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        self.btn_start = QPushButton("⏻   开始倒计时")
        self.btn_start.setObjectName("btn_primary")
        self.btn_start.setFixedHeight(48)
        self.btn_start.clicked.connect(self._on_start)

        self.btn_cancel = QPushButton("✕   取消关机")
        self.btn_cancel.setObjectName("btn_cancel")
        self.btn_cancel.setFixedHeight(48)
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self._on_cancel)

        btn_row.addWidget(self.btn_start)
        btn_row.addWidget(self.btn_cancel)
        root.addLayout(btn_row)

    def _on_sleep_toggled(self, state):
        if self._active:
            set_sleep_prevention(state == Qt.Checked)

    def _set_quick(self, mins):
        self.h_spin.setValue(mins // 60)
        self.m_spin.setValue(mins % 60)
        self.s_spin.setValue(0)

    def _on_start(self):
        total = (self.h_spin.value() * 3600
                 + self.m_spin.value() * 60
                 + self.s_spin.value())
        if total <= 0:
            self.status_label.setText("⚠  请设置大于 0 的时长")
            return
        self._total     = total
        self._remaining = total
        self._active    = True
        self._timer.start()
        if self.sleep_cb.isChecked():
            set_sleep_prevention(True)
        self.btn_start.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.h_spin.setEnabled(False)
        self.m_spin.setEnabled(False)
        self.s_spin.setEnabled(False)
        self.sleep_cb.setEnabled(False)
        self._freeze_tabs(True)
        for btn in self._quick_btns:
            btn.setEnabled(False)
        h, m, s = total // 3600, (total % 3600) // 60, total % 60
        self.countdown_label.setText(f"{h:02d}:{m:02d}:{s:02d}")
        self.status_label.setText(f"将在 {h:02d}:{m:02d}:{s:02d} 后关机")
        self.shutdown_requested.emit(total)

    def _on_cancel(self):
        self._active = False
        self._timer.stop()
        self._remaining = 0
        set_sleep_prevention(False)
        self.countdown_label.setText("--:--:--")
        self.status_label.setText("倒计时已取消")
        self.btn_start.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.h_spin.setEnabled(True)
        self.m_spin.setEnabled(True)
        self.s_spin.setEnabled(True)
        self.sleep_cb.setEnabled(True)
        self._freeze_tabs(False)
        for btn in self._quick_btns:
            btn.setEnabled(True)
        self.cancel_requested.emit()

    def _freeze_tabs(self, frozen: bool):
        try:
            tab_widget = self.parent().parent()
            if hasattr(tab_widget, 'tabBar'):
                tab_widget.tabBar().setEnabled(not frozen)
        except Exception:
            pass

    def _tick(self):
        self._remaining -= 1
        if self._remaining <= 0:
            self._timer.stop()
            set_sleep_prevention(False)
            self.countdown_label.setText("00:00:00")
            self.status_label.setText("正在关机…")
            return
        h = self._remaining // 3600
        m = (self._remaining % 3600) // 60
        s = self._remaining % 60
        self.countdown_label.setText(f"{h:02d}:{m:02d}:{s:02d}")


# ─────────────────── 抗锯齿圆角卡片容器 ─────────────────────────────

class RoundedCard(QFrame):
    """
    setMask 裁剪子控件（解决底部直角），paintEvent 抗锯齿重绘边缘（消除锯齿）。
    两者配合：mask 保证子控件不溢出圆角，paintEvent 用平滑路径覆盖 mask 的阶梯边缘。
    """
    RADIUS = 18

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # setMask 裁剪所有子控件，使其不超出圆角范围
        from PyQt5.QtGui import QBitmap
        bm = QBitmap(self.size())
        bm.fill(Qt.color0)
        p = QPainter(bm)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setBrush(Qt.color1)
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(self.rect(), self.RADIUS, self.RADIUS)
        p.end()
        self.setMask(bm)

    def paintEvent(self, event):
        # 用抗锯齿重绘，覆盖 mask 边缘的锯齿像素
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), self.RADIUS, self.RADIUS)
        painter.setClipPath(path)
        painter.fillPath(path, QColor(BG_CARD))
        painter.setPen(QColor(BORDER))
        painter.drawPath(path)
        painter.end()


# ──────────────────────────── 主窗口 ──────────────────────────────

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Timora")
        self.setFixedSize(500, 590)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._drag_pos = None
        icon_path = os.path.join(_app_dir(), "icon", "Timora.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 32)  # 底部多留空间显示圆角阴影

        card = RoundedCard()
        card.setObjectName("card")
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(32)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 0)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        # 顶栏
        topbar = QWidget()
        topbar.setFixedHeight(62)
        topbar.setStyleSheet("background: transparent;")
        tb_row = QHBoxLayout(topbar)
        tb_row.setContentsMargins(10, 10, 14, 10)
        tb_row.setSpacing(12)

        icon_lbl = QLabel()
        icon_lbl.setFixedSize(32, 32)
        icon_lbl.setScaledContents(True)
        icon_lbl.setStyleSheet("background: transparent; border: none;")
        _base = _app_dir()
        _icon_loaded = False
        for _name in ("Timora.png",):
            _p = os.path.join(_base, "icon", _name)
            if os.path.exists(_p):
                from PyQt5.QtGui import QPixmap
                icon_lbl.setPixmap(QPixmap(_p))
                _icon_loaded = True
                break
        if not _icon_loaded:
            icon_lbl.setText("⏻")
            icon_lbl.setStyleSheet(f"font-size:18px; color:{ACCENT_CYAN}; background:transparent; border:none;")
        tb_row.addWidget(icon_lbl)

        title_col = QVBoxLayout()
        title_col.setSpacing(1)
        title = QLabel("Timora")
        title.setObjectName("title")
        sub = QLabel("AUTO SHUTDOWN 自动关机")
        sub.setObjectName("subtitle")
        title_col.addWidget(title)
        title_col.addWidget(sub)
        tb_row.addLayout(title_col)
        tb_row.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {TEXT_MUTED};
                border: none; font-size: 13px; border-radius: 8px;
            }}
            QPushButton:hover {{ background: {ACCENT_RED}; color: white; }}
        """)
        close_btn.clicked.connect(self.close)
        tb_row.addWidget(close_btn)
        card_layout.addWidget(topbar)

        # Tabs
        self.tabs = QTabWidget()
        self.sched_tab     = ScheduleTab()
        self.countdown_tab = CountdownTab()
        self.tabs.addTab(self.sched_tab,     "指定时间")
        self.tabs.addTab(self.countdown_tab, "倒计时")

        self.sched_tab.shutdown_requested.connect(self._do_shutdown)
        self.sched_tab.cancel_requested.connect(self._do_cancel)
        self.countdown_tab.shutdown_requested.connect(self._do_shutdown)
        self.countdown_tab.cancel_requested.connect(self._do_cancel)

        card_layout.addWidget(self.tabs)
        outer.addWidget(card)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag_pos = e.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.LeftButton and self._drag_pos:
            self.move(e.globalPos() - self._drag_pos)

    def mouseReleaseEvent(self, e):
        self._drag_pos = None

    def closeEvent(self, e):
        set_sleep_prevention(False)
        if hasattr(self, "_bat_timer") and self._bat_timer.isActive():
            self._bat_timer.stop()
        if hasattr(self, "_shutdown_delay_timer") and self._shutdown_delay_timer.isActive():
            self._shutdown_delay_timer.stop()
        self._remove_shutdown_bat()
        super().closeEvent(e)

    _BAT_PATH = ""  # 运行时在 __init__ 后由 _get_bat_path() 动态确定

    @staticmethod
    def _get_bat_path() -> str:
        return os.path.join(_app_dir(), "shutdown.bat")

    def _run_cmd(self, args):
        """在后台线程执行命令，避免阻塞 UI；CREATE_NO_WINDOW 防止闪现黑窗口"""
        CREATE_NO_WINDOW = 0x08000000
        def _worker():
            subprocess.run(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=CREATE_NO_WINDOW,
            )
        t = QThread(self)
        t.run = _worker
        t.start()

    def _write_shutdown_bat(self):
        """在工作目录创建 shutdown.bat（仅执行关机，需管理员权限）"""
        bat_content = (
            "@echo off\r\n"
            "shutdown /s /t 0 /c \"Timora 自动关机\"\r\n"
        )
        with open(self._get_bat_path(), "w", encoding="mbcs") as f:
            f.write(bat_content)

    def _remove_shutdown_bat(self):
        """删除 shutdown.bat（如果存在）"""
        try:
            p = self._get_bat_path()
            if os.path.exists(p):
                os.remove(p)
        except Exception:
            pass

    def _close_foreground_window(self):
        """在用户会话中关闭当前前台窗口，排除标题含 Timora 的窗口"""
        WM_CLOSE = 0x0010
        try:
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            if not hwnd:
                return
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
            if "Timora" in buf.value:
                return
            ctypes.windll.user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
        except Exception:
            pass

    def _run_shutdown_bat(self):
        """以管理员身份（runas）运行 shutdown.bat"""
        bat = self._get_bat_path()
        def _worker():
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", "cmd.exe",
                f"/c \"{bat}\"",
                None, 0,
            )
        t = QThread(self)
        t.run = _worker
        t.start()

    def _do_shutdown(self, seconds: int):
        """写入 bat 文件（后台线程），倒计时结束后触发关机"""
        self._bat_timer = QTimer(self)
        self._bat_timer.setSingleShot(True)
        self._bat_timer.timeout.connect(self._on_bat_trigger)
        self._bat_timer.start(seconds * 1000)

        def _write():
            self._write_shutdown_bat()
        t = QThread(self)
        t.run = _write
        t.start()

    def _on_bat_trigger(self):
        """时间到：先关前台窗口，等待后再关机"""
        # 1. 在用户会话中发送 WM_CLOSE 给前台窗口
        self._close_foreground_window()
        # 2. 等待 3 秒（给应用保存数据的时间），再提权执行关机
        self._shutdown_delay_timer = QTimer(self)
        self._shutdown_delay_timer.setSingleShot(True)
        self._shutdown_delay_timer.timeout.connect(self._run_shutdown_bat)
        self._shutdown_delay_timer.start(3000)

    def _do_cancel(self):
        """取消：停止所有定时器并删除 bat 文件"""
        if hasattr(self, "_bat_timer") and self._bat_timer.isActive():
            self._bat_timer.stop()
        if hasattr(self, "_shutdown_delay_timer") and self._shutdown_delay_timer.isActive():
            self._shutdown_delay_timer.stop()
        self._remove_shutdown_bat()


# ──────────────────────────── 入口 ────────────────────────────────

def main():
    app = QApplication(sys.argv)

    # 生成临时箭头 SVG 文件，供样式表引用（Qt 不支持 data: URI）
    import tempfile, atexit
    _tmp_dir = tempfile.mkdtemp()
    _up_path   = os.path.join(_tmp_dir, "arrow_up.svg").replace("\\", "/")
    _down_path = os.path.join(_tmp_dir, "arrow_dn.svg").replace("\\", "/")
    with open(_up_path, "w") as f:
        f.write('<svg xmlns="http://www.w3.org/2000/svg" width="8" height="6"><polygon points="4,0 8,6 0,6" fill="#f1f5f9"/></svg>')
    with open(_down_path, "w") as f:
        f.write('<svg xmlns="http://www.w3.org/2000/svg" width="8" height="6"><polygon points="0,0 8,0 4,6" fill="#f1f5f9"/></svg>')
    import shutil
    atexit.register(lambda: shutil.rmtree(_tmp_dir, ignore_errors=True))

    sheet = STYLE_SHEET.replace("{UP_ARROW_PATH}", _up_path).replace("{DOWN_ARROW_PATH}", _down_path)
    app.setStyleSheet(sheet)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()