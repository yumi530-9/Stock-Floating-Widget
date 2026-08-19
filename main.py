# -*- coding: utf-8 -*-
"""极简A股行情悬浮窗 — 入口。python main.py 即可跑。"""
import signal
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from config import settings
from ui.floating_window import FloatingWindow
from ui.stock_picker import StockPicker
from utils.win_hotkey import GlobalHotkey


def _make_icon() -> QIcon:
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#e64545"))
    p.drawRoundedRect(2, 2, 28, 28, 7, 7)
    p.setPen(QColor("white"))
    f = p.font()
    f.setPixelSize(20)
    f.setBold(True)
    p.setFont(f)
    p.drawText(pm.rect(), Qt.AlignCenter, "¥")
    p.end()
    return QIcon(pm)


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # 关窗=进托盘
    signal.signal(signal.SIGINT, signal.SIG_DFL)  # 终端里 Ctrl+C 能退出

    cfg = settings.load()
    win = FloatingWindow(cfg)

    # 恢复上次位置；首次运行贴屏幕右上
    if cfg.get("window_x") is not None:
        win.move(cfg["window_x"], cfg["window_y"])
    else:
        geo = app.primaryScreen().availableGeometry()
        win.adjustSize()
        win.move(geo.right() - win.width() - 8, geo.top() + 80)
    win.show()

    def toggle_visible():
        win.hide() if win.isVisible() else win.show()

    def change_stock():
        dlg = StockPicker(win)
        if dlg.exec() and dlg.selected:
            win.set_stock(dlg.selected.symbol, dlg.selected.name)
            settings.save(cfg)

    def quit_app():
        settings.save(cfg)
        app.quit()

    win.request_change_stock.connect(change_stock)
    win.request_quit.connect(quit_app)

    # 托盘
    tray = QSystemTrayIcon(_make_icon(), app)
    menu = QMenu()
    act_toggle = QAction("显示 / 隐藏")
    act_toggle.triggered.connect(toggle_visible)
    act_change = QAction("更换股票…")
    act_change.triggered.connect(change_stock)
    act_pause = QAction("暂停行情刷新")
    def toggle_pause():
        win.toggle_pause()
        act_pause.setText("继续行情刷新" if win.paused else "暂停行情刷新")
    act_pause.triggered.connect(toggle_pause)
    act_quit = QAction("退出")
    act_quit.triggered.connect(quit_app)
    for a in (act_toggle, act_change, act_pause, act_quit):
        menu.addAction(a)
    tray.setContextMenu(menu)
    tray.setToolTip("股票悬浮窗")
    tray.activated.connect(
        lambda reason: toggle_visible() if reason == QSystemTrayIcon.Trigger else None)
    tray.show()

    # 全局快捷键(仅Windows生效)
    hotkey = GlobalHotkey(app, cfg.get("hotkey", "alt+`"))
    hotkey.triggered.connect(toggle_visible)

    app.aboutToQuit.connect(lambda: settings.save(cfg))
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
