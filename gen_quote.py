"""盤中即時報價 — 抓 Yahoo 即時 quote，全部股票寫成 quotes.json（給首頁顯示盤中價）。
輕量：只抓報價，不重算日K/指標，所以可每 10 分鐘跑一次而不會爆 commit。
用法：python gen_quote.py
"""
import json, datetime
from curl_cffi import requests


def read_stocks(path="stocks.txt"):
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            code = parts[0]
            suf = parts[1] if len(parts) > 1 else "auto"
            out.append((code, suf))
    return out


def fetch_quote(code, suffix):
    sufs = [".TW", ".TWO"] if suffix in ("auto", "") else [suffix]
    for suf in sufs:
        url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{code}{suf}"
               f"?range=1d&interval=5m")
        try:
            j = requests.get(url, impersonate="chrome124", timeout=20).json()
            meta = j["chart"]["result"][0]["meta"]
            price = meta.get("regularMarketPrice")
            prev = meta.get("chartPreviousClose") or meta.get("previousClose")
            if price is None or prev in (None, 0):
                continue
            return {
                "price": round(price, 2),
                "prevClose": round(prev, 2),
                "chg": round(price - prev, 2),
                "chgPct": round((price / prev - 1) * 100, 2),
                "time": meta.get("regularMarketTime"),
                "suffix": suf,
            }
        except Exception:
            continue
    return None


def main():
    stocks = read_stocks()
    quotes = {}
    for code, suf in stocks:
        q = fetch_quote(code, suf)
        if q:
            quotes[code] = q
    tw = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    out = {"asof": tw.strftime("%Y-%m-%d %H:%M"), "tz": "台灣時間", "quotes": quotes}
    with open("quotes.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"wrote quotes.json: {len(quotes)}/{len(stocks)} stocks, asof {out['asof']} TW")


if __name__ == "__main__":
    main()
