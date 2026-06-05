/* stuck_egg 共用股價圖：日/週/月K + MA5/10/20/60 疊圖 + MACD 副圖 + 技術面摘要
   需要頁面提供：#qPrice #qChg #qAsof #tfToggle #chart #macd #techSummary
   用法：StockChart.init('4938') */
(function (global) {
  var MA = [
    { n: 5,  color: '#e6e9ef' },
    { n: 10, color: '#f5b301' },
    { n: 20, color: '#ff8a65' },
    { n: 60, color: '#6cb2ff' },
  ];
  var FRAMES = [['D', '日K'], ['W', '週K'], ['M', '月K']];

  function el(id) { return document.getElementById(id); }

  function init(code) {
    fetch('./' + code + '_tech.json').then(function (r) { return r.json(); }).then(function (d) {
      render(d);
    }).catch(function (e) {
      if (el('chart')) el('chart').innerHTML = '<div style="padding:24px;color:#9aa4b2">圖表載入失敗：' + e + '</div>';
    });
  }

  function render(d) {
    // ── 報價 ──
    var up = d.chgPct >= 0;
    if (el('qPrice')) el('qPrice').textContent = Number(d.latest).toLocaleString();
    if (el('qChg')) {
      var c = el('qChg');
      c.textContent = (up ? '▲ +' : '▼ ') + d.chg + ' (' + (up ? '+' : '') + d.chgPct + '%)';
      c.style.color = up ? '#26a69a' : '#ef5350';
    }
    if (el('qAsof')) el('qAsof').textContent = '收盤 ' + d.asof + '（非即時）';

    // ── 技術面摘要 ──
    if (el('techSummary')) el('techSummary').innerHTML = techHtml(d.tech);

    var LC = global.LightweightCharts;
    var common = {
      autoSize: true,
      layout: { background: { color: 'transparent' }, textColor: '#9aa4b2', fontFamily: 'inherit' },
      grid: { vertLines: { color: 'rgba(37,43,56,0.5)' }, horzLines: { color: 'rgba(37,43,56,0.5)' } },
      rightPriceScale: { borderColor: '#252b38' },
      timeScale: { borderColor: '#252b38' },
      crosshair: { mode: 0 },
    };

    var main = LC.createChart(el('chart'), common);
    var candle = main.addCandlestickSeries({
      upColor: '#26a69a', downColor: '#ef5350', borderUpColor: '#26a69a',
      borderDownColor: '#ef5350', wickUpColor: '#26a69a', wickDownColor: '#ef5350',
    });
    var maSeries = MA.map(function (m) {
      return main.addLineSeries({ color: m.color, lineWidth: 1, priceLineVisible: false,
        lastValueVisible: false, crosshairMarkerVisible: false });
    });

    var macdChart = LC.createChart(el('macd'), common);
    var histSeries = macdChart.addHistogramSeries({ priceLineVisible: false });
    var difSeries = macdChart.addLineSeries({ color: '#f5b301', lineWidth: 1, priceLineVisible: false, lastValueVisible: false });
    var deaSeries = macdChart.addLineSeries({ color: '#6cb2ff', lineWidth: 1, priceLineVisible: false, lastValueVisible: false });

    // 同步兩張圖的時間軸
    var lock = false;
    function sync(a, b) {
      a.timeScale().subscribeVisibleLogicalRangeChange(function (rg) {
        if (lock || !rg) return; lock = true; b.timeScale().setVisibleLogicalRange(rg); lock = false;
      });
    }
    sync(main, macdChart); sync(macdChart, main);

    function load(frameKey) {
      var f = d.frames[frameKey];
      candle.setData(f.ohlc);
      maSeries.forEach(function (s, i) { s.setData(f.ma[MA[i].n] || []); });
      histSeries.setData(f.macd.hist);
      difSeries.setData(f.macd.dif);
      deaSeries.setData(f.macd.dea);
      main.timeScale().fitContent();
      macdChart.timeScale().fitContent();
    }

    // ── 週期切換鈕 ──
    if (el('tfToggle')) {
      el('tfToggle').innerHTML = '';
      FRAMES.forEach(function (fr, idx) {
        if (!d.frames[fr[0]]) return;
        var b = document.createElement('button');
        b.textContent = fr[1]; b.className = 'tfbtn' + (idx === 0 ? ' active' : '');
        b.onclick = function () {
          Array.prototype.forEach.call(el('tfToggle').children, function (x) { x.classList.remove('active'); });
          b.classList.add('active'); load(fr[0]);
        };
        el('tfToggle').appendChild(b);
      });
    }
    load('D');
  }

  function techHtml(t) {
    function cell(label, val, color) {
      return '<div class="tk"><span>' + label + '</span><b style="color:' + (color || '#fff') + '">' + val + '</b></div>';
    }
    var sigColor = t.signal === '偏多' ? '#26a69a' : (t.signal === '偏空' ? '#ef5350' : '#f5b301');
    var maOrder = (t.ma5 > t.ma20 && t.ma20 > t.ma60) ? '多頭排列' :
                  ((t.ma5 < t.ma20 && t.ma20 < t.ma60) ? '空頭排列' : '糾結');
    var rsiC = t.rsi14 >= 70 ? '#ef5350' : (t.rsi14 <= 30 ? '#26a69a' : '#fff');
    var kdC = (t.k > t.d) ? '#26a69a' : '#ef5350';
    var macdC = (t.hist >= 0) ? '#26a69a' : '#ef5350';
    return '<div class="techgrid">' +
      cell('綜合訊號', t.signal + '（' + t.score + '/6）', sigColor) +
      cell('均線排列', maOrder, maOrder === '多頭排列' ? '#26a69a' : (maOrder === '空頭排列' ? '#ef5350' : '#f5b301')) +
      cell('RSI(14)', t.rsi14, rsiC) +
      cell('KD', 'K ' + t.k + ' / D ' + t.d, kdC) +
      cell('MACD柱', t.hist, macdC) +
      cell('MA5 / MA10', t.ma5 + ' / ' + t.ma10) +
      cell('MA20(月) / MA60(季)', t.ma20 + ' / ' + t.ma60) +
      cell('DIF / DEA', t.dif + ' / ' + t.dea) +
      '</div>' +
      '<div class="dim" style="margin-top:6px">綜合訊號＝6 項技術條件（站上月線/季線、MA5>MA20、MACD柱>0、K>D、RSI>50）的多空計分，僅供參考。</div>';
  }

  global.StockChart = { init: init };
})(window);
