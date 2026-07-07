# -*- coding: utf-8 -*-
"""美股資訊分頁的資料來源：抓各族群美股「最近已收盤」價 + 漲跌% + 日期 → 寫 usmkt.json。
族群定義在此(GROUPS)，us.html 直接讀 usmkt.json 用收合方式呈現。每日更新。"""
import json, os, sys, datetime
from curl_cffi import requests as cf
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))

# 族群定義：icon / 標題 / 說明 / (代號, 中文名, 業務說明)
GROUPS = [
    {"key": "hdd", "icon": "💽", "title": "HDD / 儲存",
     "note": "AI 資料中心大容量硬碟需求(對應台股 銘異3060)",
     "stocks": [
         ("STX",  "希捷",       "HDD 雙雄之一・HAMR 近線大容量硬碟龍頭"),
         ("WDC",  "威騰",       "HDD 雙雄之一(+ 快閃記憶體事業)"),
         ("NTAP", "NetApp",     "企業級儲存陣列(混合雲/資料管理)"),
         ("HPE",  "慧與科技",   "伺服器 / 儲存系統(HPE・企業資料中心)"),
         ("MRVL", "邁威爾",     "HDD 控制晶片 + 資料中心/光電互聯"),
         ("DELL", "戴爾",       "伺服器 / 儲存系統整機"),
     ]},
    {"key": "power", "icon": "⚡", "title": "功率元件 / 電源",
     "note": "功率半導體漲價循環 + AI 伺服器供電(對應台股 強茂/大中/富鼎等)",
     "stocks": [
         ("MPWR", "MPS",        "電源管理 / DrMOS・AI 伺服器供電核心 ⭐"),
         ("ON",   "onsemi",     "功率 MOSFET / IGBT / SiC(車用・工控)"),
         ("WOLF", "Wolfspeed",  "碳化矽 SiC 純製造商(高壓功率)"),
         ("NVTS", "Navitas",    "氮化鎵 GaN 功率 IC(快充/伺服器電源)"),
         ("POWI", "Power Integ", "高壓電源轉換 IC"),
         ("VICR", "Vicor",      "電源模組(資料中心 HVDC 高壓直流供電)"),
         ("DIOD", "Diodes",     "分離式 / 功率二極體・MOSFET"),
         ("ADI",  "亞德諾",     "類比 / 電源管理大廠"),
         ("TXN",  "德儀",       "類比 / 電源管理大廠"),
         ("NXPI", "恩智浦",     "車用 / 功率 / 微控制器"),
     ]},
]


def fetch_us(tk):
    j = cf.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{tk}",
               params={"range": "7d", "interval": "1d"}, impersonate="chrome124", timeout=15).json()
    r = j["chart"]["result"][0]
    state = r.get("meta", {}).get("marketState", "")
    ts = r["timestamp"]
    cl = r["indicators"]["quote"][0]["close"]
    pairs = [(t, c) for t, c in zip(ts, cl) if c is not None]
    # 美股還在盤中(REGULAR)時最後一根未收，取前一根當「最近已收盤」
    idx = -2 if state == "REGULAR" else -1
    last_t, last_c = pairs[idx]
    prev_c = pairs[idx - 1][1]
    pct = (last_c / prev_c - 1) * 100 if prev_c else 0
    d = datetime.datetime.utcfromtimestamp(last_t)
    return {"price": round(last_c, 2), "chgPct": round(pct, 2), "date": d.strftime("%m/%d")}


def fetch_hist(tk):
    """近3年週線收盤 → [{'time':'YYYY-MM-DD','value':收盤}]，給展開走勢圖用。"""
    j = cf.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{tk}",
               params={"range": "3y", "interval": "1wk"}, impersonate="chrome124", timeout=15).json()
    r = j["chart"]["result"][0]
    ts = r["timestamp"]
    cl = r["indicators"]["quote"][0]["close"]
    out = []
    for t, c in zip(ts, cl):
        if c is None:
            continue
        d = datetime.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d")
        out.append({"time": d, "value": round(c, 2)})
    return out


def main():
    asof = ""
    out_groups = []
    for g in GROUPS:
        rows = []
        for tk, name, desc in g["stocks"]:
            try:
                q = fetch_us(tk)
                asof = q["date"]
                try:
                    hist = fetch_hist(tk)
                except Exception as he:
                    hist = []
                    print(f"  {tk} hist FAIL {he}")
                rows.append({"tk": tk, "name": name, "desc": desc, **q, "hist": hist})
                print(f"  {tk} {q['price']} ({q['chgPct']:+}%) {q['date']} hist={len(hist)}")
            except Exception as e:
                rows.append({"tk": tk, "name": name, "desc": desc, "price": None, "chgPct": None, "date": "", "hist": []})
                print(f"  {tk} FAIL {e}")
        out_groups.append({"key": g["key"], "icon": g["icon"], "title": g["title"],
                           "note": g["note"], "stocks": rows})
    data = {"asof": asof, "groups": out_groups}
    with open(os.path.join(HERE, "usmkt.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    print(f"wrote usmkt.json: asof {asof}")


if __name__ == "__main__":
    main()
