# -*- coding: utf-8 -*-
"""策略回測:投信近5日買超>1000張 + 股本<100億 → 買進,停利/停損7%,最多持有40交易日。
過去3年,每2週一個檢查點。T86逐日快取避免重複抓。結果寫 _bt_result.txt。"""
import datetime, time, numpy as np, json, os
from curl_cffi import requests as cf
import chip_screen as cs

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "_bt_result.txt")
T86CACHE = os.path.join(HERE, "_t86_cache.json")

def log(s):
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")

open(OUT, "w").close()

tdcc = cs.fetch_tdcc()
small = {c for c, e in tdcc.items() if 0 < e["cap"] < 100 and not c.startswith("00") and len(c) == 4}
log(f"股本<100億: {len(small)} 檔")

t86cache = {}
if os.path.exists(T86CACHE):
    try: t86cache = json.load(open(T86CACHE, encoding="utf-8"))
    except: pass

def t86(ymd):
    if ymd in t86cache:
        return t86cache[ymd]
    try:
        j = cf.get("https://www.twse.com.tw/rwd/zh/fund/T86",
                   params={"date": ymd, "selectType": "ALL", "response": "json"},
                   impersonate="chrome124", timeout=25).json()
        if j.get("stat") != "OK":
            t86cache[ymd] = {}; return {}
        d = {}
        for row in j["data"]:
            try: d[row[0].strip()] = int(row[10].replace(",", ""))
            except: pass
        t86cache[ymd] = d
        time.sleep(0.5)
        return d
    except Exception:
        return {}

pxcache = {}
def price(code):
    if code in pxcache: return pxcache[code]
    try:
        j = cf.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{code}.TW",
                   params={"range": "3y", "interval": "1d"}, impersonate="chrome124", timeout=20).json()
        r = j["chart"]["result"][0]; ts = r["timestamp"]; cl = r["indicators"]["quote"][0]["close"]
        arr = [(datetime.datetime.utcfromtimestamp(t).date(), c) for t, c in zip(ts, cl) if c]
        pxcache[code] = arr; return arr
    except Exception:
        pxcache[code] = []; return []

trades = []
start = datetime.date(2023, 7, 1); end = datetime.date(2026, 6, 1)
d = start; checks = 0; wk = 0
while d < end:
    if d.weekday() == 2:  # 每週三
        wk += 1
        if wk % 2 == 0:   # 每2週一次
            net = {}; dd = d; got = 0; tries = 0
            while got < 5 and tries < 10:
                if dd.weekday() < 5:
                    r = t86(dd.strftime("%Y%m%d"))
                    if r:
                        got += 1
                        for k, v in r.items(): net[k] = net.get(k, 0) + v
                dd -= datetime.timedelta(days=1); tries += 1
            cand = [c for c, v in net.items() if v > 1e6 and c in small]
            for c in cand[:6]:
                arr = price(c)
                entry = [(dt, px) for dt, px in arr if dt >= d]
                if len(entry) < 2: continue
                ep = entry[0][1]; out = None
                for dt, px in entry[1:41]:
                    if px >= ep * 1.07: out = ("win", 7.0); break
                    if px <= ep * 0.93: out = ("loss", -7.0); break
                if out is None:
                    out = ("timeout", (entry[min(40, len(entry) - 1)][1] / ep - 1) * 100)
                trades.append(out)
            checks += 1
            if checks % 10 == 0:
                log(f"  ...已跑 {checks} 檢查點, {len(trades)} 筆交易")
    d += datetime.timedelta(days=1)

json.dump(t86cache, open(T86CACHE, "w", encoding="utf-8"))
n = len(trades)
if n:
    rets = [t[1] for t in trades]
    wins = sum(1 for t in trades if t[0] == "win")
    loss = sum(1 for t in trades if t[0] == "loss")
    tmo = [t[1] for t in trades if t[0] == "timeout"]
    log("\n===== 回測結果 =====")
    log(f"檢查點 {checks} 個 / 總交易 {n} 筆")
    log(f"停利+7%: {wins} ({wins/n*100:.0f}%)")
    log(f"停損-7%: {loss} ({loss/n*100:.0f}%)")
    log(f"逾時(40日)出場: {len(tmo)} ({len(tmo)/n*100:.0f}%) 平均{np.mean(tmo):+.1f}%" if tmo else "逾時: 0")
    log(f"整體勝率(報酬>0): {sum(1 for r in rets if r>0)/n*100:.0f}%")
    log(f"每筆平均報酬(未計成本): {np.mean(rets):+.2f}%")
    log(f"計入來回成本0.6%: {np.mean(rets)-0.6:+.2f}%")
else:
    log("無交易樣本")
log("DONE")
