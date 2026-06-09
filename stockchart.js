/* stuck_egg 共用股價圖 + 技術面 + 基本面
   頁面需提供：#qPrice #qChg #qAsof #tfToggle #ovToggle #chart #macd #techSummary #fundamental
   用法：StockChart.init('4938') */
(function (global) {
  var MA = [
    { n: 5,  color: '#e6e9ef' }, { n: 10, color: '#f5b301' },
    { n: 20, color: '#ff8a65' }, { n: 60, color: '#6cb2ff' },
  ];
  var FRAMES = [['D', '日K'], ['W', '週K'], ['M', '月K']];

  function el(id) { return document.getElementById(id); }

  function init(code) {
    fetch('./' + code + '_tech.json').then(function (r) { return r.json(); })
      .then(function (d) { renderChart(d); }).catch(function (e) {
        if (el('chart')) el('chart').innerHTML = '<div style="padding:24px;color:#9aa4b2">圖表載入失敗：' + e + '</div>';
      });
    fetch('./' + code + '_fund.json').then(function (r) { return r.json(); })
      .then(function (d) { renderFund(d); }).catch(function (e) {
        if (el('fundamental')) el('fundamental').innerHTML = '<div class="dim">基本面載入失敗：' + e + '</div>';
      });
    fetch('./' + code + '_val.json').then(function (r) { return r.json(); })
      .then(function (d) { renderVal(d); }).catch(function (e) {
        if (el('valuation')) el('valuation').innerHTML = '<div class="dim">估值載入失敗：' + e + '</div>';
      });
  }

  function renderVal(v) {
    var box = el('valuation'); if (!box) return;
    if (!v.pe) {
      box.innerHTML = '<div class="tk"><span>本益比 (PE)</span><b style="color:#f5b301">不適用</b></div>' +
        '<div class="dim" style="margin-top:6px">' + (v.note || '近4季虧損或 EPS 過小，PE 無意義。') + '</div>';
      return;
    }
    var r = v.peRange;
    var pctColor = r ? (r.pctile >= 80 ? '#ef5350' : (r.pctile <= 30 ? '#26a69a' : '#fff')) : '#fff';
    var level = r ? (r.pctile >= 80 ? '偏貴' : (r.pctile <= 30 ? '相對便宜' : '中性')) : '';
    var html = '<div class="techgrid">';
    html += '<div class="tk"><span>本益比 PE（近4季 TTM）</span><b>' + v.pe + ' 倍</b></div>';
    html += '<div class="tk"><span>每股盈餘 EPS（TTM）</span><b>' + v.ttmEps + ' 元</b></div>';
    if (v.peg != null) html += '<div class="tk"><span>PEG（盈餘年增 ' + v.growth + '%）</span><b>' + v.peg + '</b></div>';
    else html += '<div class="tk"><span>PEG</span><b style="color:#9aa4b2">—（無正成長，不適用）</b></div>';
    if (r) html += '<div class="tk"><span>近2年PE位階</span><b style="color:' + pctColor + '">' + r.pctile + '%（' + level + '）</b></div>';
    html += '</div>';
    if (r) {
      var pos = Math.max(0, Math.min(100, Math.round((v.pe - r.min) / (r.max - r.min) * 100)));
      html += '<div class="dim" style="margin:10px 0 4px">近2年本益比區間：' + r.min + '（低）～ ' + r.max + '（高），中位 ' + r.med + '</div>';
      html += '<div style="position:relative;height:16px;background:linear-gradient(90deg,#26a69a,#f5b301,#ef5350);border-radius:8px;opacity:.85">' +
        '<div style="position:absolute;left:' + pos + '%;top:-3px;width:3px;height:22px;background:#fff;border-radius:2px;box-shadow:0 0 4px #000"></div></div>' +
        '<div class="dim" style="display:flex;justify-content:space-between;margin-top:2px"><span>便宜</span><span>↑ 現在 PE ' + v.pe + '</span><span>貴</span></div>';
    }
    html += '<div class="dim" style="margin-top:8px">判讀：PE 位階越低（靠左綠）相對越便宜、越高（靠右紅）相對越貴；搭配 PEG（&lt;1 通常合理）。<b style="color:#f5b301">⚠️ 但景氣循環股（記憶體/HDD…）獲利在高峰時 PE 會假性偏低，低 PE 反而要小心循環反轉。</b></div>';
    box.innerHTML = html;
  }

  function renderChart(d) {
    var up = d.chgPct >= 0;
    if (el('qPrice')) el('qPrice').textContent = Number(d.latest).toLocaleString();
    if (el('qChg')) { var c = el('qChg'); c.textContent = (up ? '▲ +' : '▼ ') + d.chg + ' (' + (up ? '+' : '') + d.chgPct + '%)'; c.style.color = up ? '#26a69a' : '#ef5350'; }
    if (el('qAsof')) el('qAsof').textContent = '收盤 ' + d.asof + '（非即時）';
    if (el('techSummary')) el('techSummary').innerHTML = techHtml(d.tech);

    var LC = global.LightweightCharts;
    var common = {
      autoSize: true,
      layout: { background: { color: 'transparent' }, textColor: '#9aa4b2', fontFamily: 'inherit' },
      grid: { vertLines: { color: 'rgba(37,43,56,0.5)' }, horzLines: { color: 'rgba(37,43,56,0.5)' } },
      rightPriceScale: { borderColor: '#252b38' }, timeScale: { borderColor: '#252b38' }, crosshair: { mode: 0 },
    };
    var main = LC.createChart(el('chart'), common);
    var candle = main.addCandlestickSeries({ upColor: '#26a69a', downColor: '#ef5350', borderUpColor: '#26a69a', borderDownColor: '#ef5350', wickUpColor: '#26a69a', wickDownColor: '#ef5350' });
    var maSeries = MA.map(function (m) { return main.addLineSeries({ color: m.color, lineWidth: 1, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false }); });
    var bollUp = main.addLineSeries({ color: '#b39ddb', lineWidth: 1, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false, visible: false });
    var bollMid = main.addLineSeries({ color: '#9aa4b2', lineWidth: 1, lineStyle: 2, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false, visible: false });
    var bollLo = main.addLineSeries({ color: '#b39ddb', lineWidth: 1, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false, visible: false });

    var macdChart = LC.createChart(el('macd'), common);
    var histS = macdChart.addHistogramSeries({ priceLineVisible: false });
    var difS = macdChart.addLineSeries({ color: '#f5b301', lineWidth: 1, priceLineVisible: false, lastValueVisible: false });
    var deaS = macdChart.addLineSeries({ color: '#6cb2ff', lineWidth: 1, priceLineVisible: false, lastValueVisible: false });

    var lock = false;
    function sync(a, b) { a.timeScale().subscribeVisibleLogicalRangeChange(function (rg) { if (lock || !rg) return; lock = true; b.timeScale().setVisibleLogicalRange(rg); lock = false; }); }
    sync(main, macdChart); sync(macdChart, main);

    function load(fk) {
      var f = d.frames[fk];
      candle.setData(f.ohlc);
      maSeries.forEach(function (s, i) { s.setData(f.ma[MA[i].n] || []); });
      bollUp.setData(f.boll.up); bollMid.setData(f.boll.mid); bollLo.setData(f.boll.lo);
      histS.setData(f.macd.hist); difS.setData(f.macd.dif); deaS.setData(f.macd.dea);
      main.timeScale().fitContent(); macdChart.timeScale().fitContent();
    }
    function setOverlay(mode) {
      var ma = mode === 'ma';
      maSeries.forEach(function (s) { s.applyOptions({ visible: ma }); });
      bollUp.applyOptions({ visible: !ma }); bollMid.applyOptions({ visible: !ma }); bollLo.applyOptions({ visible: !ma });
      if (el('maLegend')) el('maLegend').style.display = ma ? 'flex' : 'none';
      if (el('bollLegend')) el('bollLegend').style.display = ma ? 'none' : 'flex';
    }

    buildToggle('tfToggle', FRAMES.filter(function (f) { return d.frames[f[0]]; }), function (k) { load(k); }, 'D');
    buildToggle('ovToggle', [['ma', '均線'], ['boll', '布林']], function (k) { setOverlay(k); }, 'ma');
    load('D'); setOverlay('ma');
  }

  function buildToggle(id, items, cb, def) {
    var box = el(id); if (!box) return; box.innerHTML = '';
    items.forEach(function (it) {
      var b = document.createElement('button');
      b.textContent = it[1]; b.className = 'tfbtn' + (it[0] === def ? ' active' : '');
      b.onclick = function () { Array.prototype.forEach.call(box.children, function (x) { x.classList.remove('active'); }); b.classList.add('active'); cb(it[0]); };
      box.appendChild(b);
    });
  }

  function techHtml(t) {
    function cell(l, v, col) { return '<div class="tk"><span>' + l + '</span><b style="color:' + (col || '#fff') + '">' + v + '</b></div>'; }
    var sc = t.signal === '偏多' ? '#26a69a' : (t.signal === '偏空' ? '#ef5350' : '#f5b301');
    var order = (t.ma5 > t.ma20 && t.ma20 > t.ma60) ? '多頭排列' : ((t.ma5 < t.ma20 && t.ma20 < t.ma60) ? '空頭排列' : '糾結');
    var oc = order === '多頭排列' ? '#26a69a' : (order === '空頭排列' ? '#ef5350' : '#f5b301');
    var rc = t.rsi14 >= 70 ? '#ef5350' : (t.rsi14 <= 30 ? '#26a69a' : '#fff');
    function bc(x) { return x >= 0 ? '#26a69a' : '#ef5350'; }
    return '<div class="techgrid">' +
      cell('綜合訊號', t.signal + '（' + t.score + '/6）', sc) +
      cell('均線排列', order, oc) +
      cell('RSI(14)', t.rsi14 + (t.rsi14 >= 70 ? '（過熱）' : (t.rsi14 <= 30 ? '（超賣）' : '')), rc) +
      cell('KD', 'K ' + t.k + ' / D ' + t.d, t.k > t.d ? '#26a69a' : '#ef5350') +
      cell('MACD柱', t.hist, bc(t.hist)) +
      cell('乖離率 10日', (t.bias10 >= 0 ? '+' : '') + t.bias10 + '%', bc(t.bias10)) +
      cell('乖離率 20日', (t.bias20 >= 0 ? '+' : '') + t.bias20 + '%', bc(t.bias20)) +
      cell('MA20月 / MA60季', t.ma20 + ' / ' + t.ma60) +
      '</div>' +
      '<div class="dim" style="margin-top:6px">綜合訊號＝站上月線/季線、MA5>MA20、MACD柱>0、K>D、RSI>50 共 6 項計分；乖離率過大代表偏離均線、易拉回。僅供參考。</div>';
  }

  function renderFund(d) {
    var box = el('fundamental'); if (!box) return;
    var html = '';
    if (d.monthRevenue && d.monthRevenue.length) {
      var mr = d.monthRevenue.slice(-12);
      html += '<div class="dim" style="margin-bottom:6px">月營收（億元）與年增率 — 近 ' + mr.length + ' 月：</div><table class="ftab"><tr><th>月份</th><th style="text-align:right">營收</th><th style="text-align:right">年增(YoY)</th><th style="text-align:right">月增(MoM)</th></tr>';
      mr.slice().reverse().forEach(function (r) {
        function pc(v) { return v == null ? '-' : '<span style="color:' + (v >= 0 ? '#26a69a' : '#ef5350') + '">' + (v >= 0 ? '+' : '') + v + '%</span>'; }
        html += '<tr><td>' + r.ym + '</td><td style="text-align:right">' + r.rev + '</td><td style="text-align:right">' + pc(r.yoy) + '</td><td style="text-align:right">' + pc(r.mom) + '</td></tr>';
      });
      html += '</table>';
    }
    if (d.quarterly && d.quarterly.length) {
      html += '<div class="dim" style="margin:14px 0 6px">季度財報 — 營收(億)/毛利率/營益率/EPS：</div><table class="ftab"><tr><th>季別</th><th style="text-align:right">營收</th><th style="text-align:right">毛利率</th><th style="text-align:right">營益率</th><th style="text-align:right">EPS</th></tr>';
      d.quarterly.slice().reverse().forEach(function (q) {
        html += '<tr><td>' + q.q + '</td><td style="text-align:right">' + (q.rev != null ? q.rev : '-') + '</td><td style="text-align:right">' + (q.gm != null ? q.gm + '%' : '-') + '</td><td style="text-align:right">' + (q.om != null ? q.om + '%' : '-') + '</td><td style="text-align:right">' + (q.eps != null ? q.eps : '-') + '</td></tr>';
      });
      html += '</table>';
    }
    box.innerHTML = html || '<div class="dim">查無基本面資料</div>';
  }

  global.StockChart = { init: init };
})(window);
