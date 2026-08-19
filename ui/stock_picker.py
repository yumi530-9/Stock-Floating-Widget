# -*- coding: utf-8 -*-
"""更换股票对话框：输入名称/拼音/代码 → 实时搜索 → 选中。选完悬浮窗只显示名称。"""
import threading

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (QDialog, QLineEdit, QListWidget, QListWidgetItem,
                               QVBoxLayout)

from services import stock_api
from services.stock_api import StockHit


class StockPicker(QDialog):
    _results = Signal(str, list)  # (对应的关键词, hits)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("更换股票")
        self.setFixedSize(300, 320)
        self.selected: StockHit | None = None

        self.edit = QLineEdit()
        self.edit.setPlaceholderText("输入名称 / 拼音 / 代码，如 三环集团 或 300408")
        self.listw = QListWidget()
        lay = QVBoxLayout(self)
        lay.addWidget(self.edit)
        lay.addWidget(self.listw)

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(300)
        self._debounce.timeout.connect(self._do_search)

        self.edit.textChanged.connect(lambda _: self._debounce.start())
        self.edit.returnPressed.connect(self._pick_first)
        self.listw.itemDoubleClicked.connect(self._pick_item)
        self.listw.itemActivated.connect(self._pick_item)
        self._results.connect(self._show_results)

    def _do_search(self):
        kw = self.edit.text().strip()
        if not kw:
            self.listw.clear()
            return

        def work():
            hits = stock_api.search_stocks(kw)
            self._results.emit(kw, hits)

        threading.Thread(target=work, daemon=True).start()

    def _show_results(self, kw: str, hits: list):
        if kw != self.edit.text().strip():
            return  # 迟到的旧关键词结果，丢弃
        self.listw.clear()
        for h in hits:
            item = QListWidgetItem(f"{h.name}  {h.code}")  # 代码只在选择器里出现
            item.setData(Qt.UserRole, h)
            self.listw.addItem(item)

    def _pick_first(self):
        if self.listw.count():
            self._pick_item(self.listw.item(0))

    def _pick_item(self, item: QListWidgetItem):
        self.selected = item.data(Qt.UserRole)
        self.accept()
