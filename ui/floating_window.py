# -*- coding: utf-8 -*-
"""悬浮窗本体：无边框、置顶、可拖动、不占任务栏。只显示 名称 价格 涨跌幅。"""
import threading

from PySide6.QtCore import Qt, QTimer, Signal, QPoint
from PySide6.QtGui import QAction, QColor, QPainter, QBrush
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QMenu

from services import stock_api
from services.stock_api import Quote


class FloatingWindow(QWidget):
    quote_ok = Signal(object)    # Quote
    quote_err = Signal(str)
    request_change_stock = Signal()
    request_quit = Signal()

    def __init__(self, cfg: dict):
        super().__init__()
        self.cfg = cfg
        self.paused = False
        self._fetching = False
        self._drag_offset: QPoint | None = None
        self._last_quote: Quote | None = None

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
                            | Qt.Tool)  # Tool: 不出任务栏按钮
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(cfg.get("opacity", 0.92))

        fs = cfg.get("font_size", 13)
        self.lbl_name = QLabel(cfg.get("name", "…"))
        self.lbl_price = QLabel("--")
        self.lbl_pct = QLabel("--")
        self.lbl_warn = QLabel("")  # 数据异常小提示
        self.lbl_name.setStyleSheet(f"color:#d8dade; font-size:{fs}px;")
        self.lbl_price.setStyleSheet(f"color:#d8dade; font-size:{fs}px; font-weight:600;")
        self.lbl_pct.setStyleSheet(f"color:#9aa0a6; font-size:{fs}px;")
        self.lbl_warn.setStyleSheet(f"color:#e6a23c; font-size:{max(fs - 3, 8)}px;")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 6, 12, 6)
        lay.setSpacing(8)
        for w in (self.lbl_name, self.lbl_price, self.lbl_pct, self.lbl_warn):
            lay.addWidget(w)

        self.quote_ok.connect(self._on_quote)
        self.quote_err.connect(self._on_error)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(max(cfg.get("refresh_seconds", 5), 2) * 1000)
        self.refresh()

    # ---------- 行情 ----------
    def refresh(self):
        if self.paused or self._fetching:
            return
        self._fetching = True
        symbol = self.cfg["symbol"]

        def work():
            try:
                q = stock_api.fetch_quote(symbol)
                self.quote_ok.emit(q)
            except Exception as e:  # noqa: BLE001 网络/解析失败都不许崩
                self.quote_err.emit(str(e))

        threading.Thread(target=work, daemon=True).start()

    def _on_quote(self, q: Quote):
        self._fetching = False
        if q.symbol != self.cfg["symbol"]:
            return  # 切股瞬间迟到的旧股票回包，丢弃
        self._last_quote = q
        self.lbl_name.setText(q.name)
        self.lbl_price.setText(f"{q.price:.2f}")
        sign = "+" if q.pct > 0 else ""
        self.lbl_pct.setText(f"{sign}{q.pct:.2f}%")
        if q.pct > 0:
            color = self.cfg.get("color_up", "#e64545")
        elif q.pct < 0:
            color = self.cfg.get("color_down", "#1fa35c")
        else:
            color = self.cfg.get("color_flat", "#9aa0a6")
        fs = self.cfg.get("font_size", 13)
        self.lbl_price.setStyleSheet(f"color:{color}; font-size:{fs}px; font-weight:600;")
        self.lbl_pct.setStyleSheet(f"color:{color}; font-size:{fs}px;")
        self.lbl_warn.setText("")
        self.setToolTip(f"{q.name}  {q.price:.2f}  {sign}{q.pct:.2f}%  更新 {q.time}")
        self.adjustSize()
        if self.cfg.get("name") != q.name:
            self.cfg["name"] = q.name  # 用行情里的真名覆盖，防手输错名

    def _on_error(self, msg: str):
        self._fetching = False
        self.lbl_warn.setText("⚠")  # 保留最后一次成功价格，只加个小提示
        self.setToolTip(f"数据异常: {msg}")

    def set_stock(self, symbol: str, name: str):
        self.cfg["symbol"] = symbol
        self.cfg["name"] = name
        self.lbl_name.setText(name)
        self.lbl_price.setText("--")
        self.lbl_pct.setText("--")
        self._fetching = False
        self.refresh()

    def toggle_pause(self):
        self.paused = not self.paused
        if not self.paused:
            self.refresh()

    # ---------- 外观 ----------
    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor(28, 30, 34, 235)))
        p.drawRoundedRect(self.rect(), 9, 9)

    # ---------- 拖动 ----------
    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            self._drag_offset = ev.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, ev):
        if self._drag_offset is not None and ev.buttons() & Qt.LeftButton:
            self.move(ev.globalPosition().toPoint() - self._drag_offset)

    def mouseReleaseEvent(self, ev):
        if self._drag_offset is not None:
            self._drag_offset = None
            pos = self.pos()
            self.cfg["window_x"], self.cfg["window_y"] = pos.x(), pos.y()

    # ---------- 右键菜单 ----------
    def contextMenuEvent(self, ev):
        menu = QMenu(self)
        act_change = QAction("更换股票…", menu)
        act_change.triggered.connect(self.request_change_stock.emit)
        act_pause = QAction("继续刷新" if self.paused else "暂停刷新", menu)
        act_pause.triggered.connect(self.toggle_pause)
        act_hide = QAction("隐藏(托盘继续跑)", menu)
        act_hide.triggered.connect(self.hide)
        act_quit = QAction("退出", menu)
        act_quit.triggered.connect(self.request_quit.emit)
        for a in (act_change, act_pause, act_hide, act_quit):
            menu.addAction(a)
        menu.exec(ev.globalPos())

    def closeEvent(self, ev):
        ev.ignore()
        self.hide()  # 关闭=隐藏到托盘，⛔不真退出
