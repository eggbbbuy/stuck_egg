# -*- coding: utf-8 -*-
"""本機常駐盯盤:檢查 WATCH 清單的止穩/停損訊號,有訊號才發 Telegram 提醒(不洗版)。
・季線(MA60)跌破 = 停損警訊
・站回月線(MA20)/帶量止跌紅K/KD低檔金叉 = 止穩訊號
・單日跌>5% 或創近月新低 = 也提醒
由 quote_loop.py 收盤後呼叫 run_stock_watch();亦可獨立 `python stock_watch.py` 手動跑。
每檔每日最多發一次(_stock_watch_stamp.json 記錄)。"""
import os, sys, json, datetime, requests
from curl_cffi import requests as cf

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
STAMP = os.path.join(HERE, "_stock_watch_stamp.json")

# 盯盤清單: code -> (名稱, 後綴)
WATCH = {
    "2481": ("強茂", ".TW"),
    "5425": ("台半", ".TWO"),
}

# Telegram(沿用 jp_web 的 bot;發到同一個使用者)
TG_TOKEN = "8762980864:AAFNWZf9ljU54gYKZwAStX9QGRe7khZZ9A8"
TG_CHAT = "5072938387"


def tg_send(text):
    try:
        r = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                          json={"chat_id": TG_CHAT, "text": text, "disable_web_page_preview": True},
                          timeout=20)
        return r.json().get("ok", False)
    except Exception as e:
        print("TG fail:", e)
        return False


def _ma(a, n):
    return sum(a[-n:]) / n


def _kd(highs, lows, closes, n=9):
    rsv = []
    for i in range(len(closes)):
        if i < n - 1:
            continue
        hh = max(highs[i - n + 1:i + 1]); ll = min(lows[i - n + 1:i + 1])
        rsv.append((closes[i] - ll) / (hh - ll) * 100 if hh != ll else 50)
    k = d = 50; out = []
    for r in rsv:
        k = k * 2 / 3 + r / 3; d = d * 2 / 3 + k / 3; out.append((k, d))
    return out


def analyze(code, suffix):
    j = cf.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{code}{suffix}",
               params={"range": "6mo", "interval": "1d"}, impersonate="chrome124", timeout=20).json()
    r = j["chart"]["result"][0]; q = r["indicators"]["quote"][0]
    idx = [i for i, x in enumerate(q["close"]) if x is not None]
    cl = [q["close"][i] for i in idx]; hi = [q["high"][i] for i in idx]
    lo = [q["low"][i] for i in idx]; vo = [q["volume"][i] or 0 for i in idx]
    last, prev = cl[-1], cl[-2]
    ma5, ma20, ma60 = _ma(cl, 5), _ma(cl, 20), _ma(cl, 60)
    prev_ma20 = _ma(cl[:-1], 20)
    sw_excl = min(lo[-20:-1])           # 不含今天的近20日低
    chg = (last / prev - 1) * 100
    v5 = sum(vo[-6:-1]) / 5; vtoday = vo[-1]
    ks = _kd(hi, lo, cl); (k, dv) = ks[-1]; (pk, pd) = ks[-2]
    redK = last > prev
    sig = []
    if last < ma60:
        sig.append(("停損", f"跌破季線({ma60:.1f})"))
    if last >= ma20 and prev < prev_ma20:
        sig.append(("止穩", f"站回月線({ma20:.1f})"))
    if redK and last >= sw_excl and vtoday > v5 * 1.2:
        sig.append(("止穩", "帶量止跌紅K"))
    if k > dv and pk <= pd and k < 30:
        sig.append(("止穩", f"KD低檔金叉(K{k:.0f}/D{dv:.0f})"))
    if chg < -5:
        sig.append(("注意", f"單日大跌{chg:.1f}%"))
    if last <= sw_excl:
        sig.append(("注意", "創近月新低"))
    return {"last": last, "chg": chg, "ma20": ma20, "ma60": ma60, "k": k, "d": dv, "sig": sig}


def run_stock_watch(force=False):
    today = datetime.date.today().isoformat()
    try:
        stamp = json.load(open(STAMP, encoding="utf-8")) if os.path.exists(STAMP) else {}
    except Exception:
        stamp = {}
    lines = []
    for code, (name, suf) in WATCH.items():
        try:
            a = analyze(code, suf)
        except Exception as e:
            print(f"{name} 抓取失敗: {e}"); continue
        key = f"{code}:{today}"
        if a["sig"] and (force or stamp.get(key) != [s[1] for s in a["sig"]]):
            tags = "／".join(f"{t}:{m}" for t, m in a["sig"])
            lines.append(f"【{name} {code}】收{a['last']:.1f}({a['chg']:+.1f}%) 月線{a['ma20']:.1f}/季線{a['ma60']:.1f}\n　→ {tags}")
            stamp[key] = [s[1] for s in a["sig"]]
        print(f"{name}: 收{a['last']:.1f} sig={a['sig']}")
    if lines:
        msg = "📉 盯盤提醒(收盤)\n\n" + "\n\n".join(lines) + \
              "\n\n判斷:跌破季線=停損訊號;止穩需站回月線/帶量紅K/KD金叉至少2項。⚠️非投顧建議。"
        ok = tg_send(msg)
        print("TG 已發送" if ok else "TG 發送失敗")
    json.dump(stamp, open(STAMP, "w", encoding="utf-8"), ensure_ascii=False)
    return bool(lines)


if __name__ == "__main__":
    run_stock_watch(force="--force" in sys.argv)
