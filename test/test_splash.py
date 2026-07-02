import sys
import os

os.chdir(r'E:\软件开发\云集智能音乐创意台\dev\app')
sys.path.insert(0, '.')

from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtCore import Qt, QPropertyAnimation, pyqtProperty
from PyQt6.QtGui import QColor, QPixmap, QPainter

app = QApplication(sys.argv)

print("Step 1: Creating QPixmap...", flush=True)
pixmap = QPixmap(520, 360)
pixmap.fill(QColor("#0D0D0D"))
print("  QPixmap created", flush=True)

print("Step 2: Creating QSplashScreen...", flush=True)
splash = QSplashScreen(pixmap)
splash.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
print("  QSplashScreen created", flush=True)

print("Step 3: Loading icon...", flush=True)
base = os.path.dirname(os.path.abspath('E:\\软件开发\\云集智能音乐创意台\\dev\\app\\main.py'))
for name in ('icon.png', 'icon.ico'):
    p = os.path.join(base, name)
    print(f"  Checking {p}: exists={os.path.exists(p)}", flush=True)
    if os.path.exists(p):
        icon_pixmap = QPixmap(p)
        print(f"  Icon loaded: {icon_pixmap.width()}x{icon_pixmap.height()}", flush=True)
        break

print("Step 4: Showing splash...", flush=True)
splash.show()
splash.repaint()
print("  Splash shown", flush=True)

print("SUCCESS: SplashScreen works!", flush=True)

from PyQt6.QtCore import QTimer
QTimer.singleShot(2000, app.quit)
ret = app.exec()
print(f"Event loop exited with code: {ret}", flush=True)
