"""抓 Yahoo 台股日K OHLC + 算 EMA，輸出 <code>_ohlc.json 給頁面用 lightweight-charts 畫。
用法：python gen_ohlc.py 4938 [.TW|.TWO|auto]
（同源 JSON，GitHub Pages 直接 fetch，無 CORS 問題）"""
import sys, json, datetime
from curl_cffi import requests

HERE_FMT = "%Y-%m-%d"


def fetch_ohlc(code, suffix="auto", rng="15mo"):
    suffixes = [".TW", ".TWO"] if suffix == "auto" else [suffix]
    for suf in suffixes:
        url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{code}{suf}"
               f"?range={rng}&interval=1d")
        try:
            j = requests.get(url, impersonate="chrome124", timeout=30).json()
            res = j["chart"]["result"][0]
            ts = res["timestamp"]
            q = res["indicators"]["quote"][0]
            rows = []
            for i, t in enumerate(ts):
                o, h, l, c = q["open"][i], q["high"][i], q["low"][i], q["close"][i]
                if None in (o, h, l, c):
                    continue
                d = datetime.datetime.utcfromtimestamp(t).strftime(HERE_FMT)
                rows.append({"time": d, "open": round(o, 2), "high": round(h, 2),
                             "low": round(l, 2), "close": round(c, 2)})
            if len(rows) > 20:
                return suf, rows
        except Exception:
            continue
    raise RuntimeError(f"無法取得 {code} 的 OHLC")


def ema(values, period):
    k = 2 / (period + 1)
    out = []
    prev = None
    for v in values:
        prev = v if prev is None else (v * k + prev * (1 - k))
        out.append(round(prev, 2))
    return out


def main():
    code = sys.argv[1]
    suffix = sys.argv[2] if len(sys.argv) > 2 else "auto"
    suf, rows = fetch_ohlc(code, suffix)
    closes = [r["close"] for r in rows]
    e20 = ema(closes, 20)
    e60 = ema(closes, 60)
    ema20 = [{"time": rows[i]["time"], "value": e20[i]} for i in range(len(rows))]
    ema60 = [{"time": rows[i]["time"], "value": e60[i]} for i in range(len(rows))]
    latest = rows[-1]["close"]
    prev = rows[-2]["close"] if len(rows) > 1 else latest
    data = {
        "code": code, "suffix": suf,
        "latest": latest, "prevClose": prev,
        "chg": round(latest - prev, 2),
        "chgPct": round((latest / prev - 1) * 100, 2),
        "asof": rows[-1]["time"],
        "ohlc": rows, "ema20": ema20, "ema60": ema60,
    }
    out = f"{code}_ohlc.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print(f"wrote {out}: {len(rows)} bars, suffix {suf}, latest {latest} ({data['chgPct']:+.2f}%)")


if __name__ == "__main__":
    main()
