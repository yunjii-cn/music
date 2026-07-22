"""
yunji_splash.py — 品牌化启动屏组件（共享模块）
──────────────────────────────────────
供 installer.py（自解压安装器）和 main.py（应用主程序）复用，
确保「解压进度条」与「启动进度条」视觉完全一致（同款暗底 + 云标 +
渐变蓝条 + 缓动动画 + 不确定模式光带扫动）。
"""

import os
import sys
import ctypes
from PyQt6.QtCore import (
    Qt, pyqtSignal, pyqtProperty, QTimer, QRectF,
)
from PyQt6.QtGui import (
    QPainter, QColor, QFont, QLinearGradient, QIcon, QPixmap,
)
from PyQt6.QtWidgets import QSplashScreen


class BrandedSplash(QSplashScreen):
    """品牌化启动屏：确定进度用缓动进度条；进度无法确定时自动切换为动态加载动画。

    - 确定模式：set_progress() 只设"目标进度"（由真实加载阶段驱动），_display 每帧
      缓动逼近 _target，丝滑无突跳；_display 真正逼近 1.0 时发出 reached_full。
    - 不确定模式：当某阶段长时间未推进（目标已追平且尚未到 100%，即拿不到子进度、
      无法确定进度）时，自动切换为"来回扫动的光带 + 动态省略号"动画，不显示百分比，
      保证界面始终有加载动效；收到新的 set_progress 会切回确定模式并继续丝滑推进。
    """

    reached_full = pyqtSignal()

    _STALL_FRAMES = 90        # 约 1.5s（16ms/帧）目标停滞未推进 -> 判定进度无法确定，切动态动画

    # ── 品牌常量 ───────────────────────────────────
    TITLE_TEXT = "云集智能音乐创意台"
    BG_COLOR = "#0D0D0D"
    BAR_BG = "#222222"
    BAR_GRAD_START = "#1565C0"   # AW深蓝
    BAR_GRAD_END = "#42A5F5"     # AW亮蓝
    IND_BAND_COLOR = (0x15, 0x65, 0xC0)
    IND_BAND_CENTER = "#42A5F5"

    def __init__(self):
        pixmap = QPixmap(520, 360)
        pixmap.fill(QColor(self.BG_COLOR))
        super().__init__(pixmap)
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint
        )
        self._display = 0.0          # 当前实际绘制值（丝滑动画用）
        self._target = 0.0           # 目标进度（由真实加载阶段设定）
        self._message = "正在自动安装..."
        self._finished = False
        self._indeterminate = False   # 不确定进度模式：显示动态加载动画
        self._phase = 0.0             # 动画相位（光带扫动 / 省略号）
        self._stall = 0               # 目标停滞帧计数（用于判定"进度无法确定"）
        # 启动屏 LOGO 改为矢量绘制（见 _draw_logo），不依赖外部图片资源，
        # 即便打包未带入 icon 也能稳定显示品牌徽标。
        self._logo_phase = 0.0
        # 动画计时器常驻：驱动确定模式的缓动 + 不确定模式的扫动动画
        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(16)
        self._anim_timer.timeout.connect(self._tick)
        self._anim_timer.start()
        # 缓存字体，避免每帧重建 QFont（会造成动画卡顿）
        self._title_font = QFont("Microsoft YaHei", 22, QFont.Weight.Bold)
        self._msg_font = QFont("Microsoft YaHei", 10)
        self._pct_font = QFont("Microsoft YaHei", 9)

    def _get_progress(self):
        return self._display

    def _set_progress(self, val):
        self.set_progress(val)

    progress = pyqtProperty(float, _get_progress, _set_progress)

    def set_progress(self, value, message=""):
        """确定进度：设置目标值（由真实加载阶段驱动），会切回确定模式。"""
        try:
            value = max(0.0, min(1.0, float(value)))
        except Exception:
            value = 0.0
        self._indeterminate = False
        self._stall = 0
        self._target = value
        if message:
            self._message = message
        if not self._anim_timer.isActive():
            self._anim_timer.start()

    def set_indeterminate(self, message=""):
        """进度无法确定：切换为动态加载动画（无百分比、无固定进度）。"""
        self._indeterminate = True
        if message:
            self._message = message
        if not self._anim_timer.isActive():
            self._anim_timer.start()

    def _tick(self):
        if self._finished:
            self._anim_timer.stop()
            return
        # 相位常驻推进：供不确定模式的光带扫动 / 省略号使用
        # （速度砍半：0.012 -> 0.006，扫动更缓、更优雅）
        self._phase = (self._phase + 0.006) % 1.0

        if self._indeterminate:
            self.repaint()
            return

        diff = self._target - self._display
        if abs(diff) < 0.005:
            self._display = self._target
            # 目标已追平：若长时间未推进且尚未到 100%，判定"进度无法确定"，切动态动画
            if self._target < 1.0:
                self._stall += 1
                if self._stall >= self._STALL_FRAMES:
                    self._indeterminate = True
        else:
            # 缓动：每帧逼近剩余距离的 12%，丝滑无突跳
            self._display += diff * 0.12
            self._stall = 0
        self.repaint()
        if self._display >= 0.999 and self._target >= 1.0 and not self._finished:
            self.reached_full.emit()

    def finish(self, w):
        if self._finished:
            return
        self._finished = True
        self._anim_timer.stop()
        try:
            super().finish(w)
        except Exception:
            self.hide()

    # ── 绘制（品牌视觉）────────────────────────────

    def _draw_logo(self, painter, w):
        """品牌 LOGO（优先加载 logo.png / ico.png 真实图片，回退矢量绘制）。"""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        size = 80
        x = (w - size) // 2
        y = 35

        # 首次调用时尝试加载真实 LOGO 图片
        if not hasattr(self, '_logo_pixmap') or self._logo_pixmap is None:
            self._logo_pixmap = None
            try:
                if hasattr(sys, '_MEIPASS'):
                    base = sys._MEIPASS
                else:
                    base = os.path.dirname(os.path.abspath(__file__))
                for name in ('ico.png', 'logo.png', 'icon.ico'):
                    p = os.path.join(base, name)
                    if os.path.exists(p):
                        if name.endswith('.ico'):
                            pm = QIcon(p).pixmap(size, size)
                        else:
                            pm = QPixmap(p)
                        if not pm.isNull():
                            self._logo_pixmap = pm.scaled(
                                size, size,
                                Qt.AspectRatioMode.KeepAspectRatio,
                                Qt.TransformationMode.SmoothTransformation,
                            )
                            break
            except Exception:
                pass

        # 绘制真实 LOGO（有图就画，不再画矢量）
        if self._logo_pixmap and not self._logo_pixmap.isNull():
            ix = x + (size - self._logo_pixmap.width()) // 2
            iy = y + (size - self._logo_pixmap.height()) // 2
            painter.drawPixmap(ix, iy, self._logo_pixmap)
            return

        # ── 回退：矢量绘制圆角渐变蓝底 + 白色音符（无 logo.png 时）──
        grad = QLinearGradient(x, y, x, y + size)
        grad.setColorAt(0.0, QColor("#1565C0"))
        grad.setColorAt(1.0, QColor("#42A5F5"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(grad)
        painter.drawRoundedRect(QRectF(x, y, size, size), 16, 16)
        # 白色音符
        painter.setBrush(QColor("#FFFFFF"))
        painter.setPen(QColor("#FFFFFF"))
        painter.drawEllipse(x + 16, y + 40, 18, 14)          # 符头
        pen = painter.pen()
        pen.setWidth(3)
        painter.setPen(pen)
        painter.drawLine(x + 33, y + 46, x + 33, y + 18)        # 符干
        painter.drawLine(x + 33, y + 18, x + 47, y + 24)        # 符尾旗
        painter.drawLine(x + 33, y + 22, x + 45, y + 28)        # 符尾旗

    def drawContents(self, painter):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        painter.fillRect(0, 0, w, h, QColor(self.BG_COLOR))

        if self._logo_phase is not None:
            self._draw_logo(painter, w)

        painter.setPen(QColor("#F0F0F0"))
        painter.setFont(self._title_font)
        title = self.TITLE_TEXT
        fm = painter.fontMetrics()
        tw = fm.horizontalAdvance(title)
        painter.drawText((w - tw) // 2, 180, title)

        bar_x, bar_y, bar_w, bar_h = 60, 240, w - 120, 10
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(self.BAR_BG))
        painter.drawRoundedRect(QRectF(bar_x, bar_y, bar_w, bar_h), 5, 5)

        if self._indeterminate:
            # 不确定进度：来回扫动的光带（ping-pong + 平滑缓入缓出）
            seg_w = bar_w * 0.32
            tri = 1.0 - abs(2.0 * self._phase - 1.0)       # 0 -> 1 -> 0
            eased = tri * tri * (3.0 - 2.0 * tri)           # smoothstep
            seg_x = bar_x + (bar_w - seg_w) * eased
            grad = QLinearGradient(seg_x, bar_y, seg_x + seg_w, bar_y)
            grad.setColorAt(0.0, QColor(*self.IND_BAND_COLOR, 0))
            grad.setColorAt(0.5, QColor(self.IND_BAND_CENTER))
            grad.setColorAt(1.0, QColor(*self.IND_BAND_COLOR, 0))
            painter.setBrush(grad)
            painter.drawRoundedRect(QRectF(seg_x, bar_y, seg_w, bar_h), 5, 5)
        else:
            fill_w = bar_w * min(self._display, 1.0)
            if fill_w > 0:
                grad = QLinearGradient(bar_x, bar_y, bar_x + fill_w, bar_y)
                grad.setColorAt(0, QColor(self.BAR_GRAD_START))
                grad.setColorAt(1, QColor(self.BAR_GRAD_END))
                painter.setBrush(grad)
                painter.drawRoundedRect(QRectF(bar_x, bar_y, fill_w, bar_h), 5, 5)

        painter.setPen(QColor("#888888"))
        painter.setFont(self._msg_font)
        msg = self._message
        if self._indeterminate:
            dots = "." * (int(self._phase * 12) % 4)
            msg = self._message.rstrip(".") + dots
        fm2 = painter.fontMetrics()
        mw = fm2.horizontalAdvance(msg)
        painter.drawText((w - mw) // 2, 275, msg)

        # 百分比仅在确定模式显示
        if not self._indeterminate:
            pct = f"{int(min(self._display, 1.0) * 100)}%"
            painter.setPen(QColor("#42A5F5"))
            painter.setFont(self._pct_font)
            fm3 = painter.fontMetrics()
            pw = fm3.horizontalAdvance(pct)
            painter.drawText((w - pw) // 2, 300, pct)


# ── 跨进程/跨模块协调：通知 launcher 的 Win32 预启动屏收起 ──
_SPLASH_READY_EVENT = "Global\\YunjiSplashReady"


def mark_splash_ready():
    """通知 launcher 的预启动屏：Qt 品牌启动屏已就位，可以收起了。

    launcher._PreSplash 在 import main 的静默黑屏期弹出一个独立的 Win32
    动态等待界面，并等待本事件；main.main() 显示真正的品牌启动屏后调用
    本函数 SetEvent，预启动屏随即收起。非 Windows 平台为 no-op。
    """
    try:
        if sys.platform != 'win32':
            return
        k32 = ctypes.windll.kernel32
        ev = k32.CreateEventW(None, True, False, _SPLASH_READY_EVENT)
        if ev:
            k32.SetEvent(ev)
            k32.CloseHandle(ev)
    except Exception:
        pass
