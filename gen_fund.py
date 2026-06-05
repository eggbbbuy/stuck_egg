"""抓台股基本面（FinMind 免 token）：月營收+年增/月增、季度毛利率/營益率/EPS。
輸出 <code>_fund.json。用法：python gen_fund.py 4938"""
import sys, json
from curl_cffi import requests

API = "https://api.finmindtrade.com/api/v4/data"


def fm(dataset, code, start):
    r = requests.get(API, params={"dataset": dataset, "data_id": code, "start_date": start},
                     impersonate="chrome124", timeout=40)
    j = r.json()
    return j.get("data", []) if j.get("status") == 200 else []


def month_revenue(code):
    rows = fm("TaiwanStockMonthRevenue", code, "2023-01-01")
    by = {}
    for r in rows:
        by[(r["revenue_year"], r["revenue_month"])] = r["revenue"]
    keys = sorted(by)
    out = []
    for (y, m) in keys[-13:]:
        rev = by[(y, m)]
        prev = by.get((y - 1, m))
        prevm = by.get((y, m - 1) if m > 1 else (y - 1, 12))
        out.append({
            "ym": f"{y}/{m:02d}",
            "rev": round(rev / 1e8, 2),  # 億元
            "yoy": round((rev / prev - 1) * 100, 1) if prev else None,
            "mom": round((rev / prevm - 1) * 100, 1) if prevm else None,
        })
    return out


def quarterly(code):
    rows = fm("TaiwanStockFinancialStatements", code, "2024-01-01")
    by = {}
    for r in rows:
        by.setdefault(r["date"], {})[r["type"]] = r["value"]
    out = []
    for date in sorted(by)[-8:]:
        d = by[date]
        rev = d.get("Revenue")
        gp = d.get("GrossProfit")
        oi = d.get("OperatingIncome")
        eps = d.get("EPS")
        out.append({
            "q": date,
            "rev": round(rev / 1e8, 2) if rev else None,
            "gm": round(gp / rev * 100, 1) if (gp and rev) else None,
            "om": round(oi / rev * 100, 1) if (oi and rev) else None,
            "eps": round(eps, 2) if eps is not None else None,
        })
    return out


def main():
    code = sys.argv[1]
    mrev = month_revenue(code)
    q = quarterly(code)
    out = {"code": code, "monthRevenue": mrev, "quarterly": q}
    fn = f"{code}_fund.json"
    with open(fn, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    last = mrev[-1] if mrev else {}
    print(f"wrote {fn}: 月營收 {len(mrev)} 筆(最新 {last.get('ym')} {last.get('rev')}億 年增{last.get('yoy')}%), 季報 {len(q)} 季")


if __name__ == "__main__":
    main()
