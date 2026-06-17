/* stuck_egg 共用股價圖 + 技術面 + 基本面
   頁面需提供：#qPrice #qChg #qAsof #tfToggle #ovToggle #chart #macd #techSummary #fundamental
   用法：StockChart.init('4938') */
(function (global) {
  var MA = [
    { n: 5,  color: '#e6e9ef' }, { n: 10, color: '#f5b301' },
    { n: 20, color: '#ff8a65' }, { n: 60, color: '#6cb2ff' },
  ];
  var FRAMES = [['D', '日K'], ['W', '週K'], ['M', '月K']];
  var QUOTES = null, QASOF = '';   // 即時報價(跟首頁同一份 quotes.json,每2分更新)

  function el(id) { return document.getElementById(id); }

  // 報價顯示:優先用即時 quotes.json(跟首頁一致),沒有才退回日K收盤
  function applyPrice(d) {
    var q = QUOTES && QUOTES[d.code];
    var price = q ? q.price : d.latest, chg = q ? q.chg : d.chg, pct = q ? q.chgPct : d.chgPct;
    var up = pct >= 0;
    if (el('qPrice')) el('qPrice').textContent = Number(price).toLocaleString();
    if (el('qChg')) { var c = el('qChg'); c.textContent = (up ? '▲ +' : '▼ ') + chg + ' (' + (up ? '+' : '') + pct + '%)'; c.style.color = up ? '#ef5350' : '#26a69a'; }
    if (el('qAsof')) el('qAsof').textContent = q ? ('報價 ' + QASOF + '（盤中約每2分更新）') : ('收盤 ' + d.asof + '（非即時）');
  }

  function init(code) {
    var store = {};
    function tryVerdict() {
      if (store.tech && store.fund && store.val) renderVerdict(store.tech, store.fund, store.val);
    }
    fetch('./quotes.json?t=' + Date.now()).then(function (r) { return r.json(); })
      .then(function (q) { QUOTES = q.quotes || {}; QASOF = q.asof || ''; if (store.tech) applyPrice(store.tech); })
      .catch(function () {});
    fetch('./' + code + '_tech.json').then(function (r) { return r.json(); })
      .then(function (d) { store.tech = d; renderChart(d); renderTimeline(d); tryVerdict(); }).catch(function (e) {
        if (el('chart')) el('chart').innerHTML = '<div style="padding:24px;color:#9aa4b2">圖表載入失敗：' + e + '</div>';
      });
    fetch('./' + code + '_fund.json').then(function (r) { return r.json(); })
      .then(function (d) { store.fund = d; renderFund(d); tryVerdict(); }).catch(function (e) {
        if (el('fundamental')) el('fundamental').innerHTML = '<div class="dim">基本面載入失敗：' + e + '</div>';
      });
    fetch('./' + code + '_val.json').then(function (r) { return r.json(); })
      .then(function (d) { store.val = d; renderVal(d); tryVerdict(); }).catch(function (e) {
        if (el('valuation')) el('valuation').innerHTML = '<div class="dim">估值載入失敗：' + e + '</div>';
      });
    fetch('./' + code + '_chip.json').then(function (r) { return r.json(); })
      .then(function (d) { renderChip(d); }).catch(function (e) {
        if (el('chip')) el('chip').innerHTML = '<div class="dim">籌碼面載入失敗：' + e + '</div>';
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
    html += '<details style="margin-top:10px;border:1px solid var(--line);border-radius:8px;overflow:hidden">'
      + '<summary style="cursor:pointer;padding:10px 12px;font-size:.86rem;color:#6cb2ff">📖 PEG 是什麼？貴的股票貴得有沒有道理？（點開看生活例子）</summary>'
      + '<div style="padding:2px 12px 12px;font-size:.85rem;color:var(--txt);line-height:1.8">'
      + '<b>PEG ＝ 本益比 ÷ 盈餘成長率</b>，用來判斷「貴的股票，貴得有沒有道理」。<br><br>'
      + '🍎 <b>水果攤例子</b>（買「每年賺 1 元」的權利）：<br>'
      + '・A 攤（AI 股）：本益比 50（很貴），但獲利每年成長 50% → PEG＝50÷50＝<b>1</b><br>'
      + '・B 攤（傳產）：本益比 10（便宜），但獲利幾乎不成長(5%) → PEG＝10÷5＝<b>2</b><br>'
      + '→ A 雖然本益比貴，但成長快，PEG 反而比 B 低、其實更划算。<br><br>'
      + '<b>判讀：</b><br>'
      + '・<b style="color:var(--down)">PEG &lt; 1</b>：股價可能被低估（成長配得上高股價）<br>'
      + '・<b style="color:var(--up)">PEG &gt; 2</b>：股價可能太貴（成長跟不上，留意泡沫風險）<br><br>'
      + '<b>為什麼科技股要看 PEG：</b>AI 股本益比動輒 40~60 倍，只看本益比永遠買不下手；但若它明年獲利預計成長 60%，60÷60＝1，估值其實合理——投資人買的是「未來的成長」。<br><br>'
      + '<b style="color:var(--accent)">⚠️ 提醒：</b>成長率要用「市場預期的<b>未來</b> 1~3 年」（法人 EPS 預估），不要用「過去」的成長率——用過去算，AI 股往往早就噴完了。'
      + '</div></details>';
    box.innerHTML = html;
  }

  function renderChart(d) {
    applyPrice(d);
    if (el('techSummary')) el('techSummary').innerHTML = techHtml(d.tech);

    var LC = global.LightweightCharts;
    var common = {
      autoSize: true,
      layout: { background: { color: 'transparent' }, textColor: '#9aa4b2', fontFamily: 'inherit' },
      grid: { vertLines: { color: 'rgba(37,43,56,0.5)' }, horzLines: { color: 'rgba(37,43,56,0.5)' } },
      rightPriceScale: { borderColor: '#252b38' }, timeScale: { borderColor: '#252b38' }, crosshair: { mode: 0 },
    };
    var main = LC.createChart(el('chart'), common);
    var candle = main.addCandlestickSeries({ upColor: '#ef5350', downColor: '#26a69a', borderUpColor: '#ef5350', borderDownColor: '#26a69a', wickUpColor: '#ef5350', wickDownColor: '#26a69a' });
    // 事件標記(除息/財報/月營收) — 只在日K顯示
    var eventMarkers = [], curFrame = 'D';
    fetch('./' + d.code + '_events.json').then(function (r) { return r.json(); }).then(function (e) {
      eventMarkers = (e.markers || []).map(function (m) {
        return {
          time: m.time,
          position: m.type === 'div' ? 'belowBar' : 'aboveBar',
          color: m.type === 'div' ? '#ef5350' : (m.type === 'rpt' ? '#f5b301' : '#6cb2ff'),
          shape: 'circle', text: m.label || ''
        };
      });
      if (curFrame === 'D') candle.setMarkers(eventMarkers);
    }).catch(function () {});
    var maSeries = MA.map(function (m) { return main.addLineSeries({ color: m.color, lineWidth: 1, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false }); });
    var bollUp = main.addLineSeries({ color: '#b39ddb', lineWidth: 1, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false, visible: false });
    var bollMid = main.addLineSeries({ color: '#9aa4b2', lineWidth: 1, lineStyle: 2, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false, visible: false });
    var bollLo = main.addLineSeries({ color: '#b39ddb', lineWidth: 1, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false, visible: false });

    var macdChart = LC.createChart(el('macd'), common);
    var histS = macdChart.addHistogramSeries({ priceLineVisible: false });
    var difS = macdChart.addLineSeries({ color: '#f5b301', lineWidth: 1, priceLineVisible: false, lastValueVisible: false });
    var deaS = macdChart.addLineSeries({ color: '#6cb2ff', lineWidth: 1, priceLineVisible: false, lastValueVisible: false });

    // KD 副圖（若頁面有 #kd）
    var kdChart = null, kSer = null, dSer = null;
    if (el('kd')) {
      kdChart = LC.createChart(el('kd'), common);
      kSer = kdChart.addLineSeries({ color: '#f5b301', lineWidth: 1, priceLineVisible: false, lastValueVisible: true });
      dSer = kdChart.addLineSeries({ color: '#6cb2ff', lineWidth: 1, priceLineVisible: false, lastValueVisible: true });
      var ref80 = kdChart.addLineSeries({ color: 'rgba(239,83,80,0.4)', lineWidth: 1, lineStyle: 2, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false });
      var ref20 = kdChart.addLineSeries({ color: 'rgba(38,166,154,0.4)', lineWidth: 1, lineStyle: 2, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false });
      kdChart._ref = function (times) { ref80.setData(times.map(function (t) { return { time: t, value: 80 }; })); ref20.setData(times.map(function (t) { return { time: t, value: 20 }; })); };
    }

    var lock = false;
    function sync(a, b) { a.timeScale().subscribeVisibleLogicalRangeChange(function (rg) { if (lock || !rg) return; lock = true; b.timeScale().setVisibleLogicalRange(rg); lock = false; }); }
    var charts = [main, macdChart].concat(kdChart ? [kdChart] : []);
    charts.forEach(function (a) { charts.forEach(function (b) { if (a !== b) sync(a, b); }); });

    function load(fk) {
      curFrame = fk;
      var f = d.frames[fk];
      candle.setData(f.ohlc);
      candle.setMarkers(fk === 'D' ? eventMarkers : []);
      maSeries.forEach(function (s, i) { s.setData(f.ma[MA[i].n] || []); });
      bollUp.setData(f.boll.up); bollMid.setData(f.boll.mid); bollLo.setData(f.boll.lo);
      histS.setData(f.macd.hist.map(function (h) { return { time: h.time, value: h.value, color: h.value >= 0 ? '#ef5350' : '#26a69a' }; }));
      difS.setData(f.macd.dif); deaS.setData(f.macd.dea);
      if (kdChart && f.kd) {
        kSer.setData(f.kd.k); dSer.setData(f.kd.d);
        kdChart._ref(f.ohlc.map(function (o) { return o.time; }));
        kdChart.timeScale().fitContent();
      }
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
    var sc = t.signal === '偏多' ? '#ef5350' : (t.signal === '偏空' ? '#26a69a' : '#f5b301');
    var order = (t.ma5 > t.ma20 && t.ma20 > t.ma60) ? '多頭排列' : ((t.ma5 < t.ma20 && t.ma20 < t.ma60) ? '空頭排列' : '糾結');
    var oc = order === '多頭排列' ? '#ef5350' : (order === '空頭排列' ? '#26a69a' : '#f5b301');
    var rc = t.rsi14 >= 70 ? '#ef5350' : (t.rsi14 <= 30 ? '#26a69a' : '#fff');
    function bc(x) { return x >= 0 ? '#ef5350' : '#26a69a'; }
    return '<div class="techgrid">' +
      cell('綜合訊號', t.signal + '（' + t.score + '/6）', sc) +
      cell('均線排列', order, oc) +
      cell('RSI(14)', t.rsi14 + (t.rsi14 >= 70 ? '（過熱）' : (t.rsi14 <= 30 ? '（超賣）' : '')), rc) +
      cell('KD', 'K ' + t.k + ' / D ' + t.d, t.k > t.d ? '#ef5350' : '#26a69a') +
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
        function pc(v) { return v == null ? '-' : '<span style="color:' + (v >= 0 ? '#ef5350' : '#26a69a') + '">' + (v >= 0 ? '+' : '') + v + '%</span>'; }
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

  // 自動催化時間軸：用真實K線最大單日漲跌日（事件對照交給使用者，不亂掰）
  function renderTimeline(d) {
    var box = el('autoTimeline'); if (!box) return;
    var tm = d.topMoves || [];
    if (!tm.length) { box.innerHTML = '<div class="dim">資料不足</div>'; return; }
    var html = '<div class="dim" style="margin-bottom:8px">近一年「最大單日漲幅」日（硬數據，可對照當天新聞找催化）：</div><table class="ftab"><tr><th>日期</th><th style="text-align:right">收盤</th><th style="text-align:right">單日</th></tr>';
    tm.slice().reverse().forEach(function (m) {
      var col = m.pct >= 0 ? '#ef5350' : '#26a69a';
      html += '<tr><td>' + m.time + '</td><td style="text-align:right">' + m.close + '</td><td style="text-align:right;color:' + col + '">' + (m.pct >= 0 ? '+' : '') + m.pct + '%</td></tr>';
    });
    html += '</table><div class="dim" style="margin-top:6px">⚠️ 這是「股價自己跳最多的日子」，多半對應法說/題材/族群消息。想知道某一天發生什麼，把日期給小助理，我幫你查當天新聞。</div>';
    box.innerHTML = html;
  }

  // 自動多空：用 技術面 + 月營收年增 + 估值 + 毛利 資料產生
  function renderVerdict(tech, fund, val) {
    var box = el('autoVerdict'); if (!box) return;
    var bulls = [], bears = [];
    var t = (tech && tech.tech) || {};
    // 技術面
    if (t.signal === '偏多') bulls.push('技術面綜合偏多（' + t.score + '/6）、' + (t.ma5 > t.ma20 ? '均線多頭' : '均線轉強'));
    if (t.signal === '偏空') bears.push('技術面綜合偏空（' + t.score + '/6）、動能轉弱');
    if (t.rsi14 >= 70) bears.push('RSI ' + t.rsi14 + ' 偏熱（短線過熱、易拉回）');
    if (t.rsi14 <= 30) bulls.push('RSI ' + t.rsi14 + ' 超賣（短線跌深）');
    if (t.bias20 != null && t.bias20 > 15) bears.push('正乖離大（離月線 +' + t.bias20 + '%），漲多易回檔');
    // 基本面（最新月營收年增、最新季毛利）
    if (fund && fund.monthRevenue && fund.monthRevenue.length) {
      var lastm = fund.monthRevenue[fund.monthRevenue.length - 1];
      if (lastm.yoy != null) {
        if (lastm.yoy >= 20) bulls.push('最新月營收（' + lastm.ym + '）年增 +' + lastm.yoy + '%，營運成長');
        else if (lastm.yoy < 0) bears.push('最新月營收（' + lastm.ym + '）年減 ' + lastm.yoy + '%，本業逆風');
      }
    }
    if (fund && fund.quarterly && fund.quarterly.length) {
      var q = fund.quarterly[fund.quarterly.length - 1];
      if (q.gm != null) (q.gm < 12 ? bears : bulls).push('近一季毛利率 ' + q.gm + '%' + (q.gm < 12 ? '（偏薄）' : ''));
    }
    // 估值
    if (val) {
      if (val.pe && val.peRange) {
        if (val.peRange.pctile >= 80) bears.push('本益比位階 ' + val.peRange.pctile + '%（近2年偏貴）');
        else if (val.peRange.pctile <= 30) bulls.push('本益比位階 ' + val.peRange.pctile + '%（近2年相對便宜）');
      }
      if (!val.pe) bears.push('近4季虧損 / EPS 過小，估值無法用 PE 評（轉機股風險）');
      if (val.peg != null && val.peg < 1) bulls.push('PEG ' + val.peg + '（<1，相對成長合理）');
    }
    if (!bulls.length) bulls.push('—');
    if (!bears.length) bears.push('—');
    function ul(arr) { return '<ul>' + arr.map(function (x) { return '<li>' + x + '</li>'; }).join('') + '</ul>'; }
    box.innerHTML = '<div><span class="tag bull">多方</span></div>' + ul(bulls) +
      '<div style="margin-top:8px"><span class="tag bear">空方 / 風險</span></div>' + ul(bears) +
      '<div class="dim" style="margin-top:6px">⚠️ 此多空為「技術＋營收＋估值」資料自動產生的訊號，非深度產業分析；循環股/轉機股別只看單一指標。</div>';
  }

  // 籌碼面：三大法人買賣超 + 融資融券
  function renderChip(c) {
    var box = el('chip'); if (!box) return;
    var html = '';
    if (c.inst5) {
      function nb(v) { return '<b style="color:' + (v >= 0 ? '#ef5350' : '#26a69a') + '">' + (v >= 0 ? '+' : '') + Number(v).toLocaleString() + '</b>'; }
      html += '<div class="techgrid">' +
        '<div class="tk"><span>外資 近5日</span>' + nb(c.inst5.foreign || 0) + ' 張</div>' +
        '<div class="tk"><span>投信 近5日</span>' + nb(c.inst5.trust || 0) + ' 張</div>' +
        '<div class="tk"><span>自營 近5日</span>' + nb(c.inst5.dealer || 0) + ' 張</div>' +
        '<div class="tk"><span>三大法人合計</span>' + nb((c.inst5.foreign || 0) + (c.inst5.trust || 0) + (c.inst5.dealer || 0)) + ' 張</div>' +
        '</div>';
    }
    if (c.institutional && c.institutional.length) {
      html += '<div class="dim" style="margin:12px 0 6px">三大法人買賣超（張，正=買超）：</div><table class="ftab"><tr><th>日期</th><th style="text-align:right">外資</th><th style="text-align:right">投信</th><th style="text-align:right">自營</th><th style="text-align:right">合計</th></tr>';
      c.institutional.slice(-6).reverse().forEach(function (r) {
        function cc(v) { return '<span style="color:' + (v >= 0 ? '#ef5350' : '#26a69a') + '">' + (v >= 0 ? '+' : '') + Number(v).toLocaleString() + '</span>'; }
        html += '<tr><td>' + r.date + '</td><td style="text-align:right">' + cc(r.foreign) + '</td><td style="text-align:right">' + cc(r.trust) + '</td><td style="text-align:right">' + cc(r.dealer) + '</td><td style="text-align:right">' + cc(r.total) + '</td></tr>';
      });
      html += '</table>';
    }
    if (c.margin && c.margin.length) {
      var mlast = c.margin[c.margin.length - 1], mfirst = c.margin[0];
      var mTrend = (mlast.marginBal != null && mfirst.marginBal != null) ? (mlast.marginBal - mfirst.marginBal) : null;
      html += '<div class="dim" style="margin:12px 0 6px">融資融券（張）：</div>' +
        '<div class="techgrid"><div class="tk"><span>融資餘額</span><b>' + (mlast.marginBal != null ? Number(mlast.marginBal).toLocaleString() : '-') +
        (mTrend != null ? '（近期 ' + (mTrend >= 0 ? '+' : '') + Number(mTrend).toLocaleString() + '）' : '') + '</b></div>' +
        '<div class="tk"><span>融券餘額</span><b>' + (mlast.shortBal != null ? Number(mlast.shortBal).toLocaleString() : '-') + '</b></div></div>';
    }
    html += '<div class="dim" style="margin-top:6px">外資/投信「連續買超」通常偏多；融資大增有時是散戶追高訊號。資料：FinMind，每日更新。</div>';
    box.innerHTML = html || '<div class="dim">查無籌碼資料</div>';
  }

  global.StockChart = { init: init };
})(window);
