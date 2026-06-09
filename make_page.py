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
    ("3017", "奇鋐", "散熱（均熱片 / 液冷）"),
    ("3324", "雙鴻", "散熱模組"),
    ("3037", "欣興", "ABF 載板龍頭"),
    ("2383", "台光電", "高頻 CCL 銅箔基板龍頭"),
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
         --up:#26a69a; --down:#ef5350; --accent:#f5b301; }}
  *{{box-sizing:border-box}}
  body{{margin:0;background:var(--bg);color:var(--txt);
       font-family:-apple-system,"Noto Sans TC","Microsoft JhengHei",Segoe UI,Roboto,sans-serif;line-height:1.7;}}
  .wrap{{max-width:880px;margin:0 auto;padding:18px 16px 60px;}}
  a.back{{color:var(--sub);font-size:.85rem;text-decoration:none}}
  h1{{font-size:1.5rem;margin:.2em 0 .1em}}
  h2{{font-size:1.15rem;margin:1.7em 0 .5em;border-left:4px solid var(--accent);padding-left:10px}}
  .sub{{color:var(--sub);font-size:.9rem;margin-bottom:14px}}
  .card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin:12px 0;}}
  .tv{{background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden;margin:12px 0}}
  .kpi{{display:flex;justify-content:space-between;border-bottom:1px dashed var(--line);padding:7px 0}}
  .kpi:last-child{{border-bottom:0}}.kpi b{{color:#fff}}
  .dim{{color:var(--sub);font-size:.82rem}}a{{color:#6cb2ff}}
  .warn{{background:rgba(245,179,1,.12);border:1px solid var(--accent);color:#f7c948}}
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
  <div class="sub">{SUB}　|　AI PC 概念股</div>

  <div class="card" style="display:flex;justify-content:space-between;align-items:baseline">
    <div><b style="font-size:1.7rem" id="qPrice">—</b> <span id="qChg" class="dim"></span></div>
    <div class="dim" id="qAsof"></div>
  </div>
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
  <div class="tv" style="height:150px;margin-top:6px"><div id="macd" style="height:100%;width:100%"></div></div>
  <div class="dim">上：日/週/月 K + 均線疊圖；下：MACD（柱＋DIF 橘 / DEA 藍）。資料：Yahoo，每日自動更新。</div>

  <h2>技術面</h2>
  <div class="card" id="techSummary"></div>

  <h2>基本面（月營收 / 季度毛利 / EPS）</h2>
  <div class="card" id="fundamental"><div class="dim">載入中…</div></div>

  <h2>估值（本益比 / PEG / 近2年PE區間）</h2>
  <div class="card" id="valuation"><div class="dim">載入中…</div></div>

  <h2>公司定位</h2>
  <div class="card">
    <div class="kpi"><span>定位</span><b>{SUB}</b></div>
    <div class="kpi"><span>題材</span><b>AI PC 換機潮（NVIDIA RTX Spark / N1X 帶動）</b></div>
    <div class="dim" style="margin-top:8px">想看這檔的「深入催化時間軸 / 多空分析」就跟小助理說，我再單獨幫你深做。</div>
  </div>

  <h2>AI PC 同類股（點擊切換）</h2>
  <div class="card"><div class="nav">{NAV}</div></div>

  <h2>看圖框架（非投顧建議）</h2>
  <div class="card">
    <ul>
      <li>先看上方<b>技術面</b>綜合訊號（偏多/偏空）＋均線排列，判斷現在多空位階。</li>
      <li><b>基本面</b>看月營收年增有沒有續強、毛利率方向；<b>估值</b>看 PE 位階（靠右紅=相對貴）＋ PEG。</li>
      <li>避免追漲停噴出當天；回檔測月線/季線不破再分批，<b>設停損、控部位</b>。</li>
    </ul>
    <div class="warn card" style="margin-top:6px">⚠️ AI PC 是「換機潮題材」，題材股容易先漲一波 price-in；代工/散熱/載板多半同時吃 AI 伺服器，不是純 AI PC。順勢可參與但別追頂。</div>
  </div>

  <div class="disc">
    📌 免責聲明：本頁為個人資訊整理，<b>非投資顧問建議、非買賣推薦</b>。技術/基本面/估值數據來自 Yahoo、FinMind，每日自動更新；圖表由 TradingView lightweight-charts 繪製。盈虧自負。
  </div>
</div>
<script src="https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js"></script>
<script src="./stockchart.js"></script>
<script>StockChart.init('{CODE}');</script>
</body>
</html>
"""


def main():
    for code, name, sub in STOCKS:
        html = (TEMPLATE.replace("{CODE}", code).replace("{NAME}", name)
                .replace("{SUB}", sub).replace("{NAV}", NAV))
        with open(f"{code}.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("wrote", code + ".html", name)


if __name__ == "__main__":
    main()
