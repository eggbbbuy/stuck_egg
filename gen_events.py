"""產生 <code>_events.json：K 線上的事件標記(除權息/季財報/月營收公告)。
除息日來自 FinMind;財報/月營收用法定公告日推算。標記日期會貼齊最近的交易日。
法說會無可靠 API → 不含(可日後手動加)。
用法：python gen_events.py <code>"""
import sys, json, os
from curl_cffi import requests

HERE = os.path.dirname(os.path.abspath(__file__))


def fetch_dividends(code):
    try:
        r = requests.get("https://api.finmindtrade.com/api/v4/data",
                         params={"dataset": "TaiwanStockDividendResult", "data_id": code,
                                 "start_date": "2023-06-01"},
                         impersonate="chrome124", timeout=20).json()
        out = []
        for d in r.get("data", []):
            div = d.get("stock_and_cache_dividend")
            txt = f"除息{div:g}" if isinstance(div, (int, float)) and div else "除息"
            out.append({"time": d["date"], "label": txt, "type": "div"})
        return out
    except Exception:
        return []


def revenue_markers(fund):
    out = []
    for r in fund.get("monthRevenue", [])[-13:]:
        try:
            y, m = r["ym"].split("/"); y, m = int(y), int(m)
            m2, y2 = (m + 1, y) if m < 12 else (1, y + 1)
            out.append({"time": f"{y2:04d}-{m2:02d}-10", "label": "", "type": "rev"})
        except Exception:
            pass
    return out


def report_markers(fund):
    dl = {"03": ("05-15", "Q1財報"), "06": ("08-14", "Q2財報"), "09": ("11-14", "Q3財報")}
    out = []
    for q in fund.get("quarterly", [])[-8:]:
        try:
            y, m, _ = q["q"].split("-")
            if m == "12":
                out.append({"time": f"{int(y)+1:04d}-03-31", "label": "年報", "type": "rpt"})
            elif m in dl:
                out.append({"time": f"{y}-{dl[m][0]}", "label": dl[m][1], "type": "rpt"})
        except Exception:
            pass
    return out


def main():
    code = sys.argv[1]
    fund = json.load(open(os.path.join(HERE, f"{code}_fund.json"), encoding="utf-8"))
    tech = json.load(open(os.path.join(HERE, f"{code}_tech.json"), encoding="utf-8"))
    dates = [r["time"] for r in tech["frames"]["D"]["ohlc"]]
    dset = set(dates)
    first, last = (dates[0], dates[-1]) if dates else ("", "")

    def snap(d):
        if d in dset:
            return d
        earlier = [x for x in dates if x <= d]
        return earlier[-1] if earlier else None  # 早於圖表範圍 → 丟掉

    raw = fetch_dividends(code) + revenue_markers(fund) + report_markers(fund)
    seen, markers = set(), []
    for m in raw:
        if not (first <= m["time"] <= last) and m["time"] < first:
            continue
        t = snap(m["time"])
        if not t:
            continue
        key = (t, m["type"])
        if key in seen:
            continue
        seen.add(key)
        markers.append({"time": t, "label": m["label"], "type": m["type"]})
    markers.sort(key=lambda x: x["time"])
    with open(os.path.join(HERE, f"{code}_events.json"), "w", encoding="utf-8") as f:
        json.dump({"markers": markers}, f, ensure_ascii=False, separators=(",", ":"))
    print(f"wrote {code}_events.json: {len(markers)} markers "
          f"(除息{sum(1 for m in markers if m['type']=='div')}/"
          f"財報{sum(1 for m in markers if m['type']=='rpt')}/"
          f"月營收{sum(1 for m in markers if m['type']=='rev')})")


if __name__ == "__main__":
    main()
