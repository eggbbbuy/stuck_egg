"""抓 Yahoo 台股 日/週/月 K + 算技術指標(MA5/10/20/60、MACD、RSI、KD)，
輸出 <code>_tech.json 供 stockchart.js 畫圖。
用法：python gen_tech.py 4938 [.TW|.TWO|auto]"""
import sys, json, datetime
from curl_cffi import requests


def fetch(code, suffix, interval, rng):
    suffixes = [".TW", ".TWO"] if suffix == "auto" else [suffix]
    for suf in suffixes:
        url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{code}{suf}"
               f"?range={rng}&interval={interval}")
        try:
            j = requests.get(url, impersonate="chrome124", timeout=30).json()
            res = j["chart"]["result"][0]
            ts, q = res["timestamp"], res["indicators"]["quote"][0]
            rows = []
            for i, t in enumerate(ts):
                o, h, l, c = q["open"][i], q["high"][i], q["low"][i], q["close"][i]
                if None in (o, h, l, c):
                    continue
                rows.append({"time": datetime.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"),
                             "open": round(o, 2), "high": round(h, 2), "low": round(l, 2), "close": round(c, 2)})
            if len(rows) > 20:
                return suf, rows
        except Exception:
            continue
    return None, []


def sma(vals, n):
    out = []
    for i in range(len(vals)):
        if i + 1 < n:
            out.append(None)
        else:
            out.append(round(sum(vals[i + 1 - n:i + 1]) / n, 2))
    return out


def ema_list(vals, n):
    k = 2 / (n + 1)
    out, prev = [], None
    for v in vals:
        prev = v if prev is None else v * k + prev * (1 - k)
        out.append(prev)
    return out


def macd(closes):
    e12, e26 = ema_list(closes, 12), ema_list(closes, 26)
    dif = [e12[i] - e26[i] for i in range(len(closes))]
    dea = ema_list(dif, 9)
    hist = [(dif[i] - dea[i]) * 2 for i in range(len(closes))]
    return ([round(x, 2) for x in dif], [round(x, 2) for x in dea], [round(x, 2) for x in hist])


def rsi(closes, n=14):
    out = [None] * len(closes)
    if len(closes) <= n:
        return out
    gains = losses = 0.0
    for i in range(1, n + 1):
        ch = closes[i] - closes[i - 1]
        gains += max(ch, 0); losses += max(-ch, 0)
    ag, al = gains / n, losses / n
    out[n] = round(100 - 100 / (1 + (ag / al if al else 999)), 1)
    for i in range(n + 1, len(closes)):
        ch = closes[i] - closes[i - 1]
        ag = (ag * (n - 1) + max(ch, 0)) / n
        al = (al * (n - 1) + max(-ch, 0)) / n
        out[i] = round(100 - 100 / (1 + (ag / al if al else 999)), 1)
    return out


def kd(rows, n=9):
    k, d = 50.0, 50.0
    ks, ds = [None] * len(rows), [None] * len(rows)
    for i in range(len(rows)):
        if i + 1 < n:
            continue
        win = rows[i + 1 - n:i + 1]
        hi = max(r["high"] for r in win); lo = min(r["low"] for r in win)
        rsv = (rows[i]["close"] - lo) / (hi - lo) * 100 if hi > lo else 50
        k = k * 2 / 3 + rsv / 3
        d = d * 2 / 3 + k / 3
        ks[i], ds[i] = round(k, 1), round(d, 1)
    return ks, ds


def boll(closes, n=20, k=2):
    mid, up, lo = [], [], []
    for i in range(len(closes)):
        if i + 1 < n:
            mid.append(None); up.append(None); lo.append(None); continue
        win = closes[i + 1 - n:i + 1]
        m = sum(win) / n
        var = sum((x - m) ** 2 for x in win) / n
        sd = var ** 0.5
        mid.append(round(m, 2)); up.append(round(m + k * sd, 2)); lo.append(round(m - k * sd, 2))
    return mid, up, lo


def line(times, vals):
    return [{"time": times[i], "value": vals[i]} for i in range(len(times)) if vals[i] is not None]


def build_frame(rows):
    times = [r["time"] for r in rows]
    closes = [r["close"] for r in rows]
    dif, dea, hist = macd(closes)
    bmid, bup, blo = boll(closes)
    kk, dd = kd(rows)
    return {
        "ohlc": rows,
        "ma": {n: line(times, sma(closes, n)) for n in (5, 10, 20, 60)},
        "boll": {"mid": line(times, bmid), "up": line(times, bup), "lo": line(times, blo)},
        "kd": {"k": line(times, kk), "d": line(times, dd)},
        "macd": {
            "dif": line(times, dif), "dea": line(times, dea),
            "hist": [{"time": times[i], "value": hist[i],
                      "color": "#26a69a" if hist[i] >= 0 else "#ef5350"} for i in range(len(times))],
        },
    }


def main():
    code = sys.argv[1]
    suffix = sys.argv[2] if len(sys.argv) > 2 else "auto"
    frames, used_suf = {}, None
    for key, interval, rng in (("D", "1d", "2y"), ("W", "1wk", "5y"), ("M", "1mo", "10y")):
        suf, rows = fetch(code, suffix if used_suf is None else used_suf, interval, rng)
        if rows:
            used_suf = suf
            frames[key] = build_frame(rows)

    drows = frames["D"]["ohlc"]
    dcloses = [r["close"] for r in drows]
    r14 = rsi(dcloses); kk, dd = kd(drows)
    dif, dea, hist = macd(dcloses)
    last = -1
    ma = {n: sma(dcloses, n)[last] for n in (5, 10, 20, 60)}
    close = dcloses[last]
    # 簡單多空訊號
    score = 0
    if ma[20] and close > ma[20]: score += 1
    if ma[60] and close > ma[60]: score += 1
    if ma[5] and ma[20] and ma[5] > ma[20]: score += 1
    if hist[last] is not None and hist[last] > 0: score += 1
    if kk[last] and dd[last] and kk[last] > dd[last]: score += 1
    if r14[last] and r14[last] > 50: score += 1
    signal = "偏多" if score >= 4 else ("偏空" if score <= 2 else "中性")

    # 最大單日漲幅日（自動催化時間軸用）— 近一年
    moves = []
    recent = drows[-250:] if len(drows) > 250 else drows
    for i in range(1, len(recent)):
        pc = recent[i - 1]["close"]
        if pc:
            moves.append({"time": recent[i]["time"], "close": recent[i]["close"],
                          "pct": round((recent[i]["close"] / pc - 1) * 100, 1)})
    top_moves = sorted(moves, key=lambda m: -m["pct"])[:6]
    top_moves.sort(key=lambda m: m["time"])

    latest = close
    prev = dcloses[-2] if len(dcloses) > 1 else close
    out = {
        "code": code, "suffix": used_suf,
        "latest": latest, "prevClose": prev, "chg": round(latest - prev, 2),
        "chgPct": round((latest / prev - 1) * 100, 2), "asof": drows[-1]["time"],
        "frames": frames, "topMoves": top_moves,
        "tech": {
            "close": close, "ma5": ma[5], "ma10": ma[10], "ma20": ma[20], "ma60": ma[60],
            "rsi14": r14[last], "k": kk[last], "d": dd[last],
            "dif": dif[last], "dea": dea[last], "hist": hist[last],
            "bias10": round((close / ma[10] - 1) * 100, 2) if ma[10] else None,
            "bias20": round((close / ma[20] - 1) * 100, 2) if ma[20] else None,
            "signal": signal, "score": score,
        },
    }
    fn = f"{code}_tech.json"
    with open(fn, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"wrote {fn}: frames={list(frames)} suffix={used_suf} close={close} signal={signal}({score}/6)")


if __name__ == "__main__":
    main()
