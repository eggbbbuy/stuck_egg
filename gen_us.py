# -*- coding: utf-8 -*-
"""抓各標的「對應相關美股」的最近收盤價 + 漲跌% + 日期 → 寫 us.json。
台股盤中時，美股最近收盤＝昨晚(或最近一個美股交易日)。每日更新。"""
import json, os, sys, datetime
from curl_cffi import requests as cf
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))

# 台股代號 → 相關美股(可多檔)
MAP = {
    # ⭐ EGG 關注
    "3081": ["COHR", "LITE"], "4938": ["AAPL", "DELL"], "8299": ["MU", "WDC"], "3060": ["STX", "WDC", "NTAP"],
    # 💻 AI PC
    "2357": ["NVDA", "DELL"], "2353": ["NVDA", "DELL"], "2377": ["NVDA"], "2376": ["NVDA"],
    "2382": ["NVDA", "SMCI", "DELL"], "3231": ["NVDA", "SMCI"], "2324": ["NVDA", "SMCI"],
    "3037": ["NVDA", "AMD"], "2383": ["NVDA"],
    # ❄️ 散熱
    "3017": ["NVDA", "VRT"], "3324": ["NVDA", "VRT"], "6230": ["NVDA", "VRT"],
    "3653": ["NVDA", "VRT"], "8996": ["NVDA", "VRT"], "2421": ["NVDA", "VRT"],
    # 🔌 被動
    "2327": ["VSH", "TEL"], "2492": ["VSH", "TEL"], "6173": ["VSH", "TEL"],
    "2428": ["VSH", "TEL"], "2472": ["VSH", "TEL"], "6175": ["VSH", "TEL"],
    # 🛰️ SpaceX
    "2313": ["RKLB"], "3491": ["RKLB"], "2314": ["RKLB"], "6285": ["RKLB"], "6274": ["RKLB"],
    # ⚡ 功率半導體
    "2481": ["ON", "VSH"], "5425": ["ON", "VSH"], "3675": ["ON", "VSH"], "8255": ["ON", "VSH"],
    "3317": ["ON", "VSH"], "6435": ["ON", "MPWR"], "8261": ["ON", "MPWR"], "5299": ["ON", "MPWR"],
    "6138": ["ON", "MPWR"], "6719": ["ON", "MPWR"], "3707": ["ON"], "3016": ["ON"], "5347": ["ON"],
    # 🤖 機器人 / Optimus
    "1536": ["TSLA"], "2049": ["TSLA"], "4576": ["TSLA"], "4583": ["TSLA"], "4571": ["TSLA"],
    "1597": ["TSLA"], "3019": ["TSLA"], "3362": ["TSLA"], "2374": ["TSLA"], "5371": ["TSLA"],
    "2464": ["TSLA"], "2308": ["TSLA"], "8374": ["TSLA"], "4585": ["TSLA"],
    # 🧠 記憶體
    "6531": ["MU", "WDC"], "2344": ["MU", "WDC"], "5289": ["MU", "WDC"], "2408": ["MU", "WDC"],
    "2337": ["MU", "WDC"], "3260": ["MU", "WDC"], "4967": ["MU", "WDC"], "2451": ["MU", "WDC"], "5351": ["MU", "WDC"],
    # 📦 ABF 載板 / PCB 材料（需求來自 AI GPU/ASIC）
    "8046": ["NVDA", "AMD"], "3189": ["NVDA", "AMD"], "6213": ["NVDA", "AMD"], "2368": ["NVDA", "AMD"],
    # 🔬 先進封裝 / 測試
    "3711": ["AMKR", "NVDA"], "2449": ["AMKR", "TER"], "6239": ["AMKR", "MU"], "3374": ["AMKR", "NVDA"],
    # 🔋 PMIC / 電源管理 IC
    "6415": ["MPWR", "TXN"], "3588": ["MPWR", "TXN"], "2436": ["MPWR", "TXN"], "3257": ["MPWR", "TXN"],
    # 🏭 半導體設備 / 廠務
    "6667": ["AMAT", "LRCX"],
    # 📊 ETF
    "0050": ["EWT"], "00981A": ["EWT"], "00631L": ["EWT"], "00632R": ["EWT"],
}

NAME = {
    "NVDA": "輝達", "MU": "美光", "WDC": "威騰", "STX": "希捷", "NTAP": "NetApp", "TSLA": "特斯拉",
    "AAPL": "蘋果", "DELL": "戴爾", "SMCI": "美超微", "AMD": "超微", "VRT": "Vertiv", "VSH": "威世",
    "TEL": "泰科", "RKLB": "火箭實驗室", "ON": "onsemi", "MPWR": "MPS", "AMAT": "應材", "LRCX": "科林",
    "EWT": "台灣50ETF", "COHR": "Coherent", "LITE": "Lumentum", "TXN": "德儀",
    "AMKR": "艾克爾", "TER": "泰瑞達",
}


def fetch_us(tk):
    j = cf.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{tk}",
               params={"range": "7d", "interval": "1d"}, impersonate="chrome124", timeout=15).json()
    r = j["chart"]["result"][0]
    state = r.get("meta", {}).get("marketState", "")
    ts = r["timestamp"]
    cl = r["indicators"]["quote"][0]["close"]
    pairs = [(t, c) for t, c in zip(ts, cl) if c is not None]
    # 要「最近已收盤」：美股還在盤中(REGULAR)時，最後一根是今天未收的，取前一根
    idx = -2 if state == "REGULAR" else -1
    last_t, last_c = pairs[idx]
    prev_c = pairs[idx - 1][1]
    pct = (last_c / prev_c - 1) * 100 if prev_c else 0
    d = datetime.datetime.utcfromtimestamp(last_t)   # 美股日線時戳約 13:30 UTC = 當地交易日
    return {"price": round(last_c, 2), "chgPct": round(pct, 2),
            "name": NAME.get(tk, tk), "date": d.strftime("%m/%d")}


def main():
    tickers = sorted({t for v in MAP.values() for t in v})
    out, asof = {}, ""
    for tk in tickers:
        try:
            out[tk] = fetch_us(tk)
            asof = out[tk]["date"]
            print(f"  {tk} {out[tk]['price']} ({out[tk]['chgPct']:+}%) {out[tk]['date']}")
        except Exception as e:
            print(f"  {tk} FAIL {e}")
    data = {"asof": asof, "tickers": out, "map": MAP}
    with open(os.path.join(HERE, "us.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    print(f"wrote us.json: {len(out)}/{len(tickers)} tickers, asof {asof}")


if __name__ == "__main__":
    main()
