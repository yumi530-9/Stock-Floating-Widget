# -*- coding: utf-8 -*-
"""配置持久化。Windows 存 %APPDATA%\\StockWidget\\config.json，Linux 存 ~/.config/stock_widget。"""
import json
import os
import sys

_DEFAULTS = {
    "symbol": "sz300408",
    "name": "三环集团",
    "refresh_seconds": 5,
    "window_x": None,
    "window_y": None,
    "font_size": 13,
    "opacity": 0.92,
    "color_up": "#e64545",
    "color_down": "#1fa35c",
    "color_flat": "#9aa0a6",
    "hotkey": "alt+`",
}


def _config_dir() -> str:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
        return os.path.join(base, "StockWidget")
    return os.path.join(os.path.expanduser("~"), ".config", "stock_widget")


def _config_path() -> str:
    return os.path.join(_config_dir(), "config.json")


def load() -> dict:
    cfg = dict(_DEFAULTS)
    try:
        with open(_config_path(), encoding="utf-8") as fh:
            cfg.update(json.load(fh))
    except (OSError, ValueError):
        pass  # 首次运行或文件损坏都走默认值
    return cfg


def save(cfg: dict) -> None:
    os.makedirs(_config_dir(), exist_ok=True)
    tmp = _config_path() + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, ensure_ascii=False, indent=2)
    os.replace(tmp, tmp[:-4])
