# -*- coding: utf-8 -*-
"""行情数据层。与 UI 完全解耦：UI 只认 Quote / search_stocks / fetch_quote 三样。
以后换数据源只改这个文件。当前数据源：腾讯行情(qt.gtimg.cn) + 腾讯搜索(smartbox.gtimg.cn)。
"""
import re
from dataclasses import dataclass

import requests

_TIMEOUT = 4  # 秒。⛔别调大：刷新周期才5秒，超时比周期长会堆积请求


@dataclass
class Quote:
    symbol: str      # 如 sz300408
    name: str        # 三环集团
    price: float
    change: float    # 涨跌额
    pct: float       # 涨跌幅(%)
    time: str        # 行情时间 HH:MM:SS


@dataclass
class StockHit:
    symbol: str
    code: str
    name: str


def fetch_quote(symbol: str) -> Quote:
    """取一只 A 股实时行情。失败抛异常，调用方决定怎么兜底。⛔不许返回假数据。"""
    url = f"https://qt.gtimg.cn/q={symbol}"
    resp = requests.get(url, timeout=_TIMEOUT)
    resp.raise_for_status()
    text = resp.content.decode("gbk", errors="replace")
    m = re.search(r'="([^"]+)"', text)
    if not m:
        raise ValueError(f"行情响应格式异常: {text[:80]}")
    f = m.group(1).split("~")
    if len(f) < 33 or not f[3]:
        raise ValueError(f"行情字段不足: {text[:80]}")
    price = float(f[3])
    if price == 0:
        raise ValueError("价格为0(可能停牌或代码无效)")
    t = f[30]  # 20260812102403
    hhmmss = f"{t[8:10]}:{t[10:12]}:{t[12:14]}" if len(t) >= 14 else ""
    return Quote(symbol=symbol, name=f[1], price=price,
                 change=float(f[31]), pct=float(f[32]), time=hhmmss)


def _unescape(s: str) -> str:
    return re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), s)


def search_stocks(keyword: str) -> list[StockHit]:
    """按名称/拼音/代码搜 A 股。只返回 A 股(GP-A*)，过滤港股美股。失败返回空列表。"""
    keyword = keyword.strip()
    if not keyword:
        return []
    url = "https://smartbox.gtimg.cn/s3/"
    try:
        resp = requests.get(url, params={"v": "2", "q": keyword, "t": "all"},
                            timeout=_TIMEOUT)
        text = resp.content.decode("gbk", errors="replace")
    except requests.RequestException:
        return []
    m = re.search(r'="([^"]*)"', text)
    if not m or m.group(1) == "N":
        return []
    hits = []
    for item in m.group(1).split("^"):
        parts = item.split("~")
        if len(parts) < 5:
            continue
        market, code, name, _pinyin, cat = parts[0], parts[1], parts[2], parts[3], parts[4]
        if not cat.startswith("GP-A"):
            continue
        hits.append(StockHit(symbol=f"{market}{code}", code=code, name=_unescape(name)))
    return hits
