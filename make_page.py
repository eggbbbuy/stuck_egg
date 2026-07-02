# -*- coding: utf-8 -*-
"""產生標準個股分析頁（資料驅動：圖表/技術/基本面/估值自動載入）。
用法：python make_page.py  → 依 STOCKS 產生每個 <code>.html"""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# AI PC 概念股（聯發科2454、台積電2330 不在此列）
STOCKS = [
    ("2357", "華碩", "NB / 主機板品牌廠（AI PC 換機潮）"),
    ("2353", "宏碁", "NB 品牌廠（AI PC 換機潮）"),
    ("2377", "微星", "主機板 / 電競 NB / AI 伺服器"),
    ("2376", "技嘉", "主機板 / AI 伺服器 / AI PC"),
    ("2382", "廣達", "NB / AI 伺服器代工龍頭"),
    ("3231", "緯創", "NB / AI 伺服器代工"),
    ("2324", "仁寶", "NB 代工"),
    ("3017", "奇鋐", "散熱龍頭（均熱片 / 3D VC / 液冷）"),
    ("3324", "雙鴻", "散熱模組 / 液冷"),
    ("3037", "欣興", "ABF 載板龍頭"),
    ("2383", "台光電", "高頻 CCL 銅箔基板龍頭"),
    # 被動元件
    ("2327", "國巨", "MLCC 被動元件龍頭"),
    ("2492", "華新科", "MLCC / 被動元件（第二梯隊）"),
    ("6173", "信昌電", "電容 / 被動元件（第二梯隊）"),
    ("2428", "興勤", "熱敏電阻 / 過電流保護（被動供應鏈）"),
    ("2472", "立隆電", "鋁質電解電容（被動供應鏈）"),
    ("6175", "立敦", "電容材料 / 化成箔（被動供應鏈）"),
    # SpaceX / 低軌衛星概念（只留確定供應鏈）
    ("2313", "華通", "低軌衛星 PCB 龍頭（Starlink 太空板）"),
    ("3491", "昇達科", "微波元件 / 波導（衛星純度最高）"),
    ("2314", "台揚", "衛星地面站 / 天線設備"),
    ("6285", "啟碁", "衛星終端 / 相位陣列天線"),
    ("6274", "台燿", "高頻 PTFE 基板（衛星 / RF）"),
    # 功率 / 離散元件
    ("2481", "強茂", "功率二極體 / MOSFET（IDM・Nexperia 轉單）"),
    ("5425", "台半", "功率二極體 / 整流器（離散元件）"),
    ("3675", "德微", "二極體 / MOSFET 功率半導體（IDM）"),
    ("8255", "朋程", "車用整流二極體（功率元件）"),
    # 功率半導體擴充（股癌 EP672：IDM 漲價循環 / Fabless / 代工產能）
    ("3317", "尼克森", "功率 MOSFET / 二極體（IDM）"),
    ("6435", "大中", "MOSFET / DrMOS（功率・AI 伺服器電源）"),
    ("8261", "富鼎", "MOSFET / DrMOS（功率・Fabless）"),
    ("5299", "杰力", "電源管理 IC（功率・Fabless）"),
    ("6138", "茂達", "類比 / 電源管理 IC（功率・Fabless）"),
    ("6719", "力智", "電源管理 IC（功率・Fabless）"),
    ("3707", "漢磊", "功率 / SiC / GaN 晶圓代工"),
    ("3016", "嘉晶", "功率磊晶片（漢磊集團）"),
    ("5347", "世界先進", "8吋晶圓代工（功率 / 驅動 IC）"),
    # 機器人 / Tesla Optimus 供應鏈
    ("1536", "和大", "減速機 / 齒輪（機器人傳動）"),
    ("2049", "上銀", "線性滑軌 / 滾珠螺桿（機器人關節龍頭）"),
    ("4576", "大銀微系統", "精密運動控制 / 伺服馬達（機器人）"),
    ("4583", "台灣精銳", "行星減速機（機器人關節）"),
    ("4571", "鈞興-KY", "精密齒輪 / 傳動（機器人）"),
    ("1597", "直得", "線性滑軌 / 微型化（機器人）"),
    ("3019", "亞光", "光學鏡頭（Tesla 夥伴・機器視覺）"),
    ("3362", "先進光", "光學鏡頭（機器視覺）"),
    ("2374", "佳能", "影像感測 / 鏡頭（機器視覺）"),
    ("5371", "中光電", "光學 / 影像（機器視覺）"),
    ("2464", "盟立", "自動化整合 / 盟英機器人關節馬達（機器人）"),
    ("2308", "台達電", "工業自動化 / 伺服馬達（機器人）"),
    ("8374", "羅昇", "自動化系統整合（機器人）"),
    ("4585", "達明", "協作型機器人（純度最高）"),
    # 半導體設備 / 廠務
    ("6667", "信紘科", "半導體廠務工程 / 特殊氣體化學品供應系統"),
    # 散熱元件（奇鋐 3017 / 雙鴻 3324 已在上方，靠 sub 關鍵字歸入散熱組）
    ("6230", "超眾", "熱導管 / 均熱板（散熱）"),
    ("3653", "健策", "均熱片 / 散熱基板（散熱）"),
    ("8996", "高力", "液冷板 / 熱交換器（AI 伺服器液冷）"),
    ("2421", "建準", "DC 散熱風扇 / 液冷"),
    # 記憶體（與 NVIDIA 有合作者排前）
    ("6531", "愛普", "客製化高頻寬記憶體 / HBM（切入 NVIDIA·AMD AI 晶片）"),
    ("2344", "華邦電", "DRAM / NOR Flash 記憶體（NOR 傳切入 NVIDIA 鏈）"),
    ("5289", "宜鼎", "工控 / 邊緣 AI 記憶體儲存（NVIDIA 夥伴生態）"),
    ("2408", "南亞科", "DRAM 記憶體廠（DDR5 / HBM 自研）"),
    ("2337", "旺宏", "NOR / NAND Flash 記憶體（IDM）"),
    ("3260", "威剛", "DRAM / SSD 記憶體模組"),
    ("4967", "十銓", "DRAM / SSD 記憶體模組"),
    ("2451", "創見", "DRAM / 工控記憶體模組"),
    ("5351", "鈺創", "利基型 DRAM 記憶體"),
    # ABF 載板 / PCB 材料
    ("8046", "南電", "ABF 載板（AI 晶片基板）"),
    ("3189", "景碩", "ABF 載板"),
    ("6213", "聯茂", "CCL 銅箔基板（PCB 材料）"),
    ("2368", "金像電", "AI 伺服器高階 PCB"),
    # 先進封裝 / 測試
    ("3711", "日月光投控", "封測龍頭（先進封裝 / CoWoS 外溢）"),
    ("2449", "京元電", "IC 測試（AI 晶片測試）"),
    ("6239", "力成", "記憶體封測 / 先進封裝"),
    ("3374", "精材", "晶圓級封裝 WLP（先進封裝）"),
    # PMIC / 電源管理 IC
    ("6415", "矽力-KY", "PMIC / 電源管理 IC 設計（類比龍頭）"),
    ("3588", "通嘉", "PMIC / AC-DC 電源控制 IC"),
    ("2436", "偉詮電", "PMIC / USB PD 電源控制 IC"),
    ("3257", "虹冠電", "PMIC / 類比 IC（電源管理）"),
    # ETF
    ("0050", "元大台灣50", "台股大盤 ETF（市值前 50 大）"),
    ("00981A", "統一台股增長", "主動式台股 ETF"),
    ("00631L", "元大台灣50正2", "台灣50 槓桿 ETF（2 倍）"),
    ("00632R", "元大台灣50反1", "台灣50 反向 ETF（-1 倍）"),
]

NAV = "".join(
    f'<a href="./{c}.html">{c} {n}</a>' for c, n, _ in STOCKS
)

TEMPLATE = """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{CODE} {NAME} 股票分析 | stuck_egg</title>
<style>
  :root{{ --bg:#0e1117; --card:#171c26; --line:#252b38; --txt:#e6e9ef; --sub:#9aa4b2;
         --up:#ef5350; --down:#26a69a; --accent:#f5b301; }}
  *{{box-sizing:border-box}}
  body{{margin:0;background:var(--bg);color:var(--txt);
       font-family:-apple-system,"Noto Sans TC","Microsoft JhengHei",Segoe UI,Roboto,sans-serif;line-height:1.7;}}
  .wrap{{max-width:880px;margin:0 auto;padding:18px 16px 60px;}}
  a.back{{position:fixed;left:14px;bottom:16px;z-index:50;background:#1b2230;color:#e6e9ef;
         border:1px solid #2f3a4d;border-radius:22px;padding:9px 15px;font-size:.9rem;
         text-decoration:none;box-shadow:0 3px 12px rgba(0,0,0,.45)}}
  a.back:hover{{border-color:#f5b301}}
  h1{{font-size:1.5rem;margin:.2em 0 .1em}}
  h2{{font-size:1.15rem;margin:1.7em 0 .5em;border-left:4px solid var(--accent);padding-left:10px}}
  .sub{{color:var(--sub);font-size:.9rem;margin-bottom:14px}}
  .card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin:12px 0;}}
  .tv{{background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden;margin:12px 0}}
  .kpi{{display:flex;justify-content:space-between;border-bottom:1px dashed var(--line);padding:7px 0}}
  .kpi:last-child{{border-bottom:0}}.kpi b{{color:#fff}}
  .dim{{color:var(--sub);font-size:.82rem}}a{{color:#6cb2ff}}
  .warn{{background:rgba(245,179,1,.12);border:1px solid var(--accent);color:#f7c948}}
  .tag{{display:inline-block;font-size:.78rem;padding:2px 9px;border-radius:999px;margin:2px 4px 2px 0}}
  .bull{{background:rgba(239,83,80,.15);color:var(--up);border:1px solid var(--up)}}
  .bear{{background:rgba(38,166,154,.15);color:var(--down);border:1px solid var(--down)}}
  ul{{margin:.3em 0 .3em 1.1em;padding:0}}li{{margin:.35em 0}}
  .disc{{font-size:.8rem;color:var(--sub);border-top:1px solid var(--line);margin-top:26px;padding-top:14px}}
  .nav{{display:flex;flex-wrap:wrap;gap:6px}}
  .nav a{{background:#171c26;border:1px solid #252b38;border-radius:8px;padding:4px 10px;font-size:.82rem;text-decoration:none}}
  .tfbar{{display:flex;gap:6px;margin:4px 0 8px}}
  .tfbtn{{background:#171c26;border:1px solid #252b38;color:#9aa4b2;border-radius:8px;padding:5px 16px;font-size:.9rem;cursor:pointer}}
  .tfbtn.active{{background:#f5b301;color:#0e1117;border-color:#f5b301;font-weight:700}}
  .malegend{{display:flex;gap:14px;flex-wrap:wrap;font-size:.78rem;color:#9aa4b2;margin-bottom:6px}}
  .malegend i{{display:inline-block;width:14px;height:3px;vertical-align:middle;margin-right:4px;border-radius:2px}}
  .techgrid{{display:grid;grid-template-columns:1fr 1fr;gap:6px 18px}}
  @media(max-width:620px){{.techgrid{{grid-template-columns:1fr}}}}
  .tk{{display:flex;justify-content:space-between;border-bottom:1px dashed var(--line);padding:6px 0}}
  .ftab{{width:100%;border-collapse:collapse;font-size:.88rem}}
  .ftab th{{color:var(--sub);font-weight:600;padding:6px 6px;border-bottom:1px solid var(--line)}}
  .ftab td{{padding:6px 6px;border-bottom:1px solid var(--line)}}
</style>
</head>
<body>
<div class="wrap">
  <a class="back" href="./">← 回首頁</a>
  <h1>{CODE} {NAME} — 股票分析</h1>
  <div class="sub">{SUB}　|　{GROUP}</div>

  <div class="card" style="display:flex;justify-content:space-between;align-items:baseline">
    <div><b style="font-size:1.7rem" id="qPrice">—</b> <span id="qChg" class="dim"></span></div>
    <div class="dim" id="qAsof"></div>
  </div>
  <div class="card" id="usPeers" style="display:none"></div>
  <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center">
    <div id="tfToggle" class="tfbar"></div>
    <div id="ovToggle" class="tfbar"></div>
  </div>
  <div id="maLegend" class="malegend">
    <span><i style="background:#e6e9ef"></i>MA5</span><span><i style="background:#f5b301"></i>MA10</span>
    <span><i style="background:#ff8a65"></i>MA20 月線</span><span><i style="background:#6cb2ff"></i>MA60 季線</span>
  </div>
  <div id="bollLegend" class="malegend" style="display:none">
    <span><i style="background:#b39ddb"></i>布林上軌</span><span><i style="background:#9aa4b2"></i>中軌 MA20</span><span><i style="background:#b39ddb"></i>下軌</span>
  </div>
  <div class="tv" style="height:360px"><div id="chart" style="height:100%;width:100%"></div></div>
  <div class="tv" style="height:140px;margin-top:6px"><div id="macd" style="height:100%;width:100%"></div></div>
  <div class="dim">MACD（柱＋DIF 橘 / DEA 藍）</div>
  <div class="tv" style="height:130px;margin-top:6px"><div id="kd" style="height:100%;width:100%"></div></div>
  <div class="dim">KD（K 橘 / D 藍；80 上方超買、20 下方超賣）。三張圖時間軸同步、可切日/週/月。資料：Yahoo，每日自動更新。</div>

  <h2>技術面</h2>
  <div class="card" id="techSummary"></div>

  <h2>基本面（月營收 / 季度毛利 / EPS）</h2>
  <div class="card" id="fundamental"><div class="dim">載入中…</div></div>

  <h2>估值（本益比 / PEG / 近2年PE區間）</h2>
  <div class="card" id="valuation"><div class="dim">載入中…</div></div>

  <h2>籌碼面（三大法人 / 融資融券）</h2>
  <div class="card" id="chip"><div class="dim">載入中…</div></div>

  <h2>催化時間軸（最大單日漲跌日）</h2>
  <div class="card" id="autoTimeline"><div class="dim">載入中…</div></div>

  <h2>多空分析（資料自動）</h2>
  <div class="card" id="autoVerdict"><div class="dim">載入中…</div></div>

  <h2>公司定位</h2>
  <div class="card">
    <div class="kpi"><span>定位</span><b>{SUB}</b></div>
    <div class="kpi"><span>題材</span><b>{THEME}</b></div>
  </div>

  <h2>追蹤清單同類股（點擊切換）</h2>
  <div class="card"><div class="nav">{NAV}</div></div>

  <h2>看圖框架（非投顧建議）</h2>
  <div class="card">
    <ul>
      <li>先看上方<b>技術面</b>綜合訊號（偏多/偏空）＋均線排列，判斷現在多空位階。</li>
      <li><b>基本面</b>看月營收年增有沒有續強、毛利率方向；<b>估值</b>看 PE 位階（靠右紅=相對貴）＋ PEG。</li>
      <li>避免追漲停噴出當天；回檔測月線/季線不破再分批，<b>設停損、控部位</b>。</li>
    </ul>
    <div class="warn card" style="margin-top:6px">⚠️ 題材股容易先漲一波 price-in，追高風險高；留意是「本業真的受惠」還是只是沾光的概念股（純度高低差很多）。順勢可參與但別追頂、設停損。</div>
  </div>

  <div class="disc">
    📌 免責聲明：本頁為個人資訊整理，<b>非投資顧問建議、非買賣推薦</b>。技術/基本面/估值數據來自 Yahoo、FinMind，每日自動更新；圖表由 TradingView lightweight-charts 繪製。盈虧自負。
  </div>
</div>
<script src="https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js"></script>
<script src="./stockchart.js?v=6"></script>
<script>StockChart.init('{CODE}');</script>
</body>
</html>
"""


CARRIER_PCB = {"8046", "3189", "6213", "2368"}   # ABF載板/PCB材料
ADV_PKG = {"3711", "2449", "6239", "3374"}        # 先進封裝/測試


def main():
    for code, name, sub in STOCKS:
        if code in CARRIER_PCB:
            group = "ABF載板 / PCB材料"
            theme = "AI 晶片載板 / PCB 材料超級循環（結構性缺貨漲價）"
        elif code in ADV_PKG:
            group = "先進封裝 / 測試"
            theme = "AI 先進封裝（CoWoS 外溢）/ IC 測試放量"
        elif "被動" in sub:
            group = "被動元件"
            theme = "被動元件漲價循環 + AI 伺服器/終端需求"
        elif any(k in sub for k in ("功率", "離散", "二極體", "MOSFET", "整流")):
            group = "功率/離散元件"
            theme = "功率元件漲價 + Nexperia 轉單/China+1 + AI 伺服器"
        elif any(k in sub for k in ("衛星", "SpaceX", "Starlink", "波導", "化合物半導體", "天線", "CPE")):
            group = "SpaceX 概念"
            theme = "低軌衛星放量 + SpaceX IPO 題材"
        elif any(k in sub for k in ("機器人", "機器視覺", "Optimus", "減速機", "諧波", "滑軌", "致動")):
            group = "機器人 / Optimus 概念"
            theme = "Tesla Optimus 人形機器人供應鏈（精密傳動 / 機器視覺 / 自動化）"
        elif any(k in sub for k in ("廠務", "特殊氣體", "化學品供應")):
            group = "半導體設備 / 廠務"
            theme = "半導體廠務工程 + 晶圓廠擴產 capex"
        elif any(k in sub for k in ("散熱", "液冷", "均熱", "熱導管", "熱交換", "散熱風扇")):
            group = "散熱元件"
            theme = "AI 伺服器 / AI PC 散熱升級（VC 均熱片 → 液冷）"
        elif "PMIC" in sub:
            group = "PMIC / 電源管理 IC"
            theme = "電源管理晶片（AI / 伺服器 / 消費電源）"
        elif any(k in sub for k in ("記憶體", "DRAM", "Flash", "HBM", "NAND", "儲存")):
            group = "記憶體"
            theme = "記憶體超級循環（AI HBM/DDR5 + NVIDIA 供應鏈）"
        elif "ETF" in sub:
            group = "ETF"
            theme = "台股 ETF / 槓桿反向工具"
        else:
            group = "AI PC 概念股"
            theme = "AI PC 換機潮（NVIDIA RTX Spark / N1X 帶動）"
        # 模板是 .format 風格(CSS/JS 字面括號用 {{}}、佔位符用 {CODE});務必用 format,
        # 用 .replace 會留下 {{ 變成非法 CSS → 整頁變白底(深色主題失效)
        html = TEMPLATE.format(CODE=code, NAME=name, SUB=sub, GROUP=group, THEME=theme, NAV=NAV)
        with open(f"{code}.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("wrote", code + ".html", name)


if __name__ == "__main__":
    main()
