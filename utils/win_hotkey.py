# -*- coding: utf-8 -*-
"""Windows 全局快捷键(默认 Alt+`)。非 Windows 平台安静跳过，不影响其他功能。
原理: RegisterHotKey + Qt 原生事件过滤器抓 WM_HOTKEY，Excel/浏览器前台时照样生效。
"""
import sys

from PySide6.QtCore import QAbstractNativeEventFilter, QObject, Signal

WM_HOTKEY = 0x0312
_MODS = {"alt": 0x0001, "ctrl": 0x0002, "shift": 0x0004, "win": 0x0008}
# 常用键 → 虚拟键码。以后做自定义快捷键往这里补
_VKS = {"`": 0xC0, "~": 0xC0, "f9": 0x78, "f10": 0x79, "f11": 0x7A, "f12": 0x7B,
        "space": 0x20, "home": 0x24, "end": 0x23}


def _parse(spec: str):
    mods, vk = 0, None
    for part in spec.lower().split("+"):
        part = part.strip()
        if part in _MODS:
            mods |= _MODS[part]
        elif part in _VKS:
            vk = _VKS[part]
        elif len(part) == 1 and (part.isalnum()):
            vk = ord(part.upper())
    return mods, vk


class GlobalHotkey(QObject):
    triggered = Signal()

    def __init__(self, app, spec: str = "alt+`", hotkey_id: int = 1):
        super().__init__()
        self.ok = False
        if sys.platform != "win32":
            return
        import ctypes
        import ctypes.wintypes
        mods, vk = _parse(spec)
        if vk is None:
            return
        MOD_NOREPEAT = 0x4000
        self.ok = bool(ctypes.windll.user32.RegisterHotKey(
            None, hotkey_id, mods | MOD_NOREPEAT, vk))
        if not self.ok:
            return  # 快捷键被别的程序占了：功能降级，托盘还能点

        outer = self

        class _Filter(QAbstractNativeEventFilter):
            def nativeEventFilter(self, event_type, message):
                if event_type == b"windows_generic_MSG":
                    msg = ctypes.wintypes.MSG.from_address(int(message))
                    if msg.message == WM_HOTKEY and msg.wParam == hotkey_id:
                        outer.triggered.emit()
                        return True, 0
                return False, 0

        self._filter = _Filter()  # 持有引用，⛔别删：被GC后快捷键悄悄失效
        app.installNativeEventFilter(self._filter)
