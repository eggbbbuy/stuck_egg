# -*- coding: utf-8 -*-
"""進階籌碼報告 + 綜合進場判斷(紅黃綠燈)。
資料源(免費):TWSE T86(三大法人) + MI_MARGN(融資融券)。
提供:近1/5/20日 外資、投信買賣超、連續買賣天數、融資變化 → 籌碼評分 → 綜合結論。
供 bottom_watch 在訊號觸發時呼叫 chip_report_and_verdict()。"""
import datetime, time
from curl_cffi import requests as cf

_T86_CACHE = {}   # ymd -> {code: (foreign_shares, trust_shares)}
_MARGIN_CACHE = {}  # ymd -> {code: 融資今日餘額(張)}


def _tw_days(n):
    days = []; d = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    d = d.date()
    while len(days) < n + 5:
        if d.weekday() < 5:
            days.append(d.strftime("%Y%m%d"))
        d -= datetime.timedelta(days=1)
    return days


def _t86(ymd):
    if ymd in _T86_CACHE:
        return _T86_CACHE[ymd]
    try:
        j = cf.get("https://www.twse.com.tw/rwd/zh/fund/T86",
                   params={"date": ymd, "selectType": "ALL", "response": "json"},
                   impersonate="chrome124", timeout=20).json()
        if j.get("stat") != "OK":
            _T86_CACHE[ymd] = None; return None
        d = {}
        for row in j["data"]:
            try:
                d[row[0].strip()] = (int(row[4].replace(",", "")), int(row[10].replace(",", "")))
            except Exception:
                pass
        _T86_CACHE[ymd] = d; time.sleep(0.3); return d
    except Exception:
        return None


def _margin(ymd):
    if ymd in _MARGIN_CACHE:
        return _MARGIN_CACHE[ymd]
    try:
        j = cf.get("https://www.twse.com.tw/rwd/zh/marginTrading/MI_MARGN",
                   params={"date": ymd, "selectType": "ALL", "response": "json"},
                   impersonate="chrome124", timeout=20).json()
        if j.get("stat") != "OK":
            _MARGIN_CACHE[ymd] = None; return None
        d = {}
        for t in j.get("tables", []):
            if "融資融券彙總" in t.get("title", "") or (t.get("fields") and t["fields"][0] == "代號"):
                for row in t.get("data", []):
                    try:
                        d[row[0].strip()] = int(row[6].replace(",", ""))  # 融資今日餘額(張)
                    except Exception:
                        pass
        _MARGIN_CACHE[ymd] = d; time.sleep(0.3); return d
    except Exception:
        return None


def gather(code, days=20):
    """回傳每交易日(新→舊)的 (ymd, foreign, trust, margin)。"""
    out = []
    for ymd in _tw_days(days + 3):
        if len([x for x in out if x[1] is not None]) >= days:
            break
        t = _t86(ymd)
        if t is None:
            continue
        fs, ts = t.get(code, (None, None))
        m = (_margin(ymd) or {}).get(code)
        out.append((ymd, fs, ts, m))
    return out


def chip_report_and_verdict(code, tech_ok=True):
    """回傳 (報告字串, 燈號 '🟢/🟡/🔴', 一句話結論)。tech_ok=技術訊號是否成立。"""
    rows = [r for r in gather(code, 20) if r[1] is not None]
    if len(rows) < 5:
        return ("（籌碼資料抓取中/暫無）", "🟡", "籌碼資料不足,先看技術面")
    f = [r[1] for r in rows]  # 外資(股) 新→舊
    t = [r[2] for r in rows]  # 投信
    m = [r[3] for r in rows if r[3] is not None]  # 融資餘額(張) 新→舊
    def s(v): return sum(v) / 1000  # 股→張
    f1, f5, f20 = f[0] / 1000, s(f[:5]), s(f[:20])
    t1, t5, t20 = t[0] / 1000, s(t[:5]), s(t[:20])
    # 連續買賣天數(外資)
    fcont = 0
    for x in f:
        if (x > 0) == (f[0] > 0) and x != 0:
            fcont += 1
        else:
            break
    fcont = fcont if f[0] > 0 else -fcont
    # 融資變化(近5日)
    mchg = (m[0] - m[min(5, len(m) - 1)]) if len(m) >= 2 else 0

    # ===== 籌碼評分(-100~+100) =====
    score = 0
    score += 20 if f20 > 0 else -20          # 外資20日淨買
    score += 15 if f5 > 0 else -15           # 外資5日淨買
    score += 15 if t20 > 0 else -12          # 投信20日淨買
    score += 10 if t5 > 0 else -8            # 投信5日淨買
    score += 10 if fcont >= 2 else (-10 if fcont <= -2 else 0)  # 外資連續性
    score += 12 if mchg < 0 else -8          # 融資減(散戶退場)=好

    def bs(v): return "🔴買" if v > 0 else ("🟢賣" if v < 0 else "—")
    report = (
        f"外資 近1日{f1:+.0f} / 近5日{f5:+.0f} / 近20日{f20:+.0f} 張 {bs(f20)}"
        + (f"｜連{abs(fcont)}天{'買' if fcont>0 else '賣'}" if abs(fcont) >= 2 else "") + "\n"
        f"投信 近1日{t1:+.0f} / 近5日{t5:+.0f} / 近20日{t20:+.0f} 張 {bs(t20)}\n"
        f"融資 近5日{mchg:+.0f}張 {'↓散戶退場(偏多)' if mchg<0 else '↑散戶加碼(留意追高)'}\n"
        f"籌碼分數 {score:+d}/100 → {'偏多' if score>=20 else ('偏空' if score<=-20 else '中性')}"
    )

    # ===== 綜合紅黃綠燈 =====
    if tech_ok and score >= 20:
        light, verdict = "🟢", "建議可考慮進場:技術到位＋籌碼偏多(法人買/融資退),可出1份(仍分批)"
    elif tech_ok and score <= -20:
        light, verdict = "🔴", "訊號打折,建議別追:技術雖到位但籌碼偏空(法人在賣),等籌碼轉多再說"
    elif tech_ok:
        light, verdict = "🟡", "可再等等:技術到位但籌碼中性/不明,想進就出很小一口試單,別重壓"
    else:
        light, verdict = "🟡", "技術訊號未成立,先觀察"
    return (report, light, verdict)


if __name__ == "__main__":
    for c, n in [("2481", "強茂"), ("5425", "台半"), ("3060", "銘異"), ("2330", "台積電")]:
        r, l, v = chip_report_and_verdict(c, tech_ok=True)
        print(f"=== {n} {c} ===\n{r}\n{l} {v}\n")
