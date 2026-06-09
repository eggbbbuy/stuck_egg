# -*- coding: utf-8 -*-
"""籌碼面：三大法人買賣超 + 融資融券（FinMind 免 token）。輸出 <code>_chip.json。
用法：python gen_chip.py 2382"""
import sys, json, datetime
from curl_cffi import requests

API = "https://api.finmindtrade.com/api/v4/data"


def fm(dataset, code, start):
    try:
        r = requests.get(API, params={"dataset": dataset, "data_id": code, "start_date": start},
                         impersonate="chrome124", timeout=40)
        j = r.json()
        return j.get("data", []) if j.get("status") == 200 else []
    except Exception:
        return []


def main():
    code = sys.argv[1]
    start = (datetime.date.today() - datetime.timedelta(days=45)).isoformat()

    # 三大法人買賣超（外資 / 投信 / 自營）—— 單位轉成「張」(股/1000)
    inst = fm("TaiwanStockInstitutionalInvestorsBuySell", code, start)
    by_date = {}
    for r in inst:
        d = r["date"]
        net = (r.get("buy", 0) - r.get("sell", 0)) / 1000.0
        name = r.get("name", "")
        if "Foreign" in name:
            key = "foreign"
        elif "Investment_Trust" in name or "Trust" in name:
            key = "trust"
        elif "Dealer" in name:
            key = "dealer"
        else:
            key = "other"
        by_date.setdefault(d, {}).setdefault(key, 0)
        by_date[d][key] += net
    inst_rows = []
    for d in sorted(by_date)[-10:]:
        x = by_date[d]
        f = round(x.get("foreign", 0))
        t = round(x.get("trust", 0))
        de = round(x.get("dealer", 0))
        inst_rows.append({"date": d, "foreign": f, "trust": t, "dealer": de, "total": f + t + de})
    # 外資/投信近5日累計
    last5 = inst_rows[-5:]
    sum5 = {"foreign": sum(r["foreign"] for r in last5),
            "trust": sum(r["trust"] for r in last5),
            "dealer": sum(r["dealer"] for r in last5)} if last5 else {}

    # 融資融券
    mg = fm("TaiwanStockMarginPurchaseShortSale", code, start)
    margin_rows = []
    for r in sorted(mg, key=lambda x: x["date"])[-10:]:
        margin_rows.append({
            "date": r["date"],
            "marginBal": r.get("MarginPurchaseTodayBalance"),       # 融資餘額(張)
            "shortBal": r.get("ShortSaleTodayBalance"),             # 融券餘額(張)
        })

    out = {"code": code, "institutional": inst_rows, "inst5": sum5, "margin": margin_rows}
    with open(f"{code}_chip.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    last = inst_rows[-1] if inst_rows else {}
    print(f"wrote {code}_chip.json: 法人{len(inst_rows)}日(最新外資{last.get('foreign')}/投信{last.get('trust')}張) 融資券{len(margin_rows)}日")


if __name__ == "__main__":
    main()
