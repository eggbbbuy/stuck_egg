"""估值：本益比(PE, TTM) + PEG + 近2年PE區間。EPS 用 FinMind 單季加總成 TTM、股價用 Yahoo。
輸出 <code>_val.json。用法：python gen_val.py 4938 [.TW|.TWO|auto]"""
import sys, json, datetime
from curl_cffi import requests

FM = "https://api.finmindtrade.com/api/v4/data"


def closes(code, suffix, rng="3y"):
    sufs = [".TW", ".TWO"] if suffix == "auto" else [suffix]
    for suf in sufs:
        try:
            j = requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{code}{suf}"
                             f"?range={rng}&interval=1d", impersonate="chrome124", timeout=30).json()
            res = j["chart"]["result"][0]
            ts, cl = res["timestamp"], res["indicators"]["quote"][0]["close"]
            rows = [(datetime.date.fromtimestamp(t), c) for t, c in zip(ts, cl) if c]
            if len(rows) > 60:
                return suf, rows
        except Exception:
            continue
    return None, []


def quarterly_eps(code):
    r = requests.get(FM, params={"dataset": "TaiwanStockFinancialStatements",
                                 "data_id": code, "start_date": "2021-01-01"},
                     impersonate="chrome124", timeout=40)
    j = r.json()
    eps = {}
    for row in (j.get("data", []) if j.get("status") == 200 else []):
        if row.get("type") == "EPS":
            eps[row["date"]] = row["value"]
    # [(date_obj, eps)] 排序
    out = []
    for d, v in eps.items():
        try:
            out.append((datetime.date.fromisoformat(d), v))
        except Exception:
            pass
    out.sort()
    return out


def ttm_at(eps_list, on_date):
    """on_date 當下的 TTM EPS = 最近 4 季(季底<=on_date)之和。"""
    avail = [v for (d, v) in eps_list if d <= on_date]
    if len(avail) < 4:
        return None
    return sum(avail[-4:])


def main():
    code = sys.argv[1]
    suffix = sys.argv[2] if len(sys.argv) > 2 else "auto"
    suf, rows = closes(code, suffix)
    if not rows:
        raise RuntimeError("無股價")
    eps_list = quarterly_eps(code)
    last_date, last_close = rows[-1]

    ttm_now = ttm_at(eps_list, last_date)
    pe_now = round(last_close / ttm_now, 1) if (ttm_now and ttm_now > 0) else None

    # 近2年每日 PE 區間
    two_y_ago = last_date - datetime.timedelta(days=730)
    pe_series = []
    for d, c in rows:
        if d < two_y_ago:
            continue
        ttm = ttm_at(eps_list, d)
        if ttm and ttm > 0:
            pe_series.append(c / ttm)
    pe_stats = None
    if len(pe_series) > 30 and pe_now:
        s = sorted(pe_series)
        below = sum(1 for x in pe_series if x <= pe_now)
        pe_stats = {
            "min": round(s[0], 1), "max": round(s[-1], 1),
            "med": round(s[len(s) // 2], 1),
            "pctile": round(below / len(pe_series) * 100),
        }

    # PEG：用 TTM EPS 年增率
    ttm_1y = ttm_at(eps_list, last_date - datetime.timedelta(days=365))
    growth = peg = None
    if ttm_now and ttm_1y and ttm_1y > 0 and ttm_now > 0:
        growth = round((ttm_now / ttm_1y - 1) * 100, 1)
        if growth and growth > 0 and pe_now:
            peg = round(pe_now / growth, 2)

    note = ""
    if ttm_now is None or ttm_now <= 0:
        note = "近4季為虧損或 EPS 過小，本益比不適用（轉機/虧損股看 PB 與獲利轉折）"

    out = {
        "code": code, "suffix": suf, "asof": last_date.isoformat(),
        "price": round(last_close, 2), "ttmEps": round(ttm_now, 2) if ttm_now else None,
        "pe": pe_now, "peRange": pe_stats, "growth": growth, "peg": peg, "note": note,
    }
    with open(f"{code}_val.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"wrote {code}_val.json: PE={pe_now} TTM_EPS={out['ttmEps']} PEG={peg} 區間={pe_stats} {note}")


if __name__ == "__main__":
    main()
