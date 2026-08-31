/* 71_egg 選品倉庫 共用購物車 (首頁 + 商品頁都套用) */
(function(){
  var KEY='kiwiegg_cart';
  var LINE_OA='https://line.me/R/oaMessage/%40344mwpgw/?';
  function yen(n){return '¥'+Number(n||0).toLocaleString();}
  function load(){try{return JSON.parse(localStorage.getItem(KEY)||'[]');}catch(e){return [];}}
  function save(c){try{localStorage.setItem(KEY,JSON.stringify(c));}catch(e){}updateBadge();}
  function totalQty(){return load().reduce(function(s,i){return s+(i.qty||1);},0);}
  function totalYen(){return load().reduce(function(s,i){return s+(i.price||0)*(i.qty||1);},0);}
  function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}

  var CSS=[
  '#cartBtn{position:relative;width:30px;height:30px;border-radius:7px;border:1px solid #ddd;background:#fff;font-size:17px;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;padding:0;vertical-align:middle;flex:0 0 auto;}',
  '#cartBtn.fixed{position:fixed;top:10px;right:12px;z-index:1000;box-shadow:0 2px 10px rgba(0,0,0,.16);}',
  '#cartCount{position:absolute;top:-6px;right:-6px;min-width:16px;height:16px;background:#e0281e;color:#fff;font-size:10px;border-radius:8px;display:flex;align-items:center;justify-content:center;padding:0 4px;font-weight:700;}',
  '#cartOverlay{position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:2000;display:none;}',
  '#cartOverlay.open{display:flex;justify-content:flex-end;}',
  '#cartSheet{background:#fff;width:100%;max-width:420px;height:100%;display:flex;flex-direction:column;box-shadow:-4px 0 24px rgba(0,0,0,.15);font-family:inherit;}',
  '#cartHead{display:flex;align-items:center;justify-content:space-between;padding:16px 18px;border-bottom:1px solid #eee;font-size:16px;}',
  '#cartClose{border:none;background:none;font-size:26px;line-height:1;cursor:pointer;color:#888;padding:0;width:32px;height:32px;}',
  '#cartBody{flex:1;overflow-y:auto;padding:6px 14px;}',
  '.cart-empty{text-align:center;color:#999;padding:60px 0;}',
  '.cart-item{display:flex;gap:10px;padding:12px 2px;border-bottom:1px solid #f2f2f2;position:relative;}',
  '.cart-item>img{width:64px;height:76px;object-fit:cover;border-radius:8px;background:#f3f3f3;flex:0 0 auto;}',
  '.ci-info{flex:1;min-width:0;}',
  '.ci-brand{font-size:11px;color:#8a8a8a;font-weight:600;text-transform:uppercase;letter-spacing:.4px;}',
  '.ci-title{font-size:13px;line-height:1.4;margin:2px 0;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;}',
  '.ci-meta{font-size:12px;color:#666;}',
  '.ci-bot{display:flex;align-items:center;justify-content:space-between;margin-top:6px;}',
  '.ci-qty{display:flex;align-items:center;gap:8px;}',
  '.ci-qty button{width:26px;height:26px;border:1px solid #ddd;background:#fff;border-radius:6px;cursor:pointer;font-size:15px;line-height:1;padding:0;}',
  '.ci-qty span{min-width:18px;text-align:center;font-size:13px;}',
  '.ci-price{font-weight:700;font-size:14px;}',
  '.ci-del{position:absolute;top:8px;right:0;border:none;background:none;color:#bbb;cursor:pointer;font-size:14px;padding:4px;}',
  '#cartFoot{border-top:1px solid #eee;padding:14px 18px 18px;}',
  '.cart-total{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:12px;font-size:15px;}',
  '.cart-total b{font-size:20px;}',
  '.cart-submit{display:block;width:100%;background:#06c755;color:#fff;border:none;font-weight:700;padding:14px;border-radius:10px;font-size:15px;cursor:pointer;}',
  '#cartToast{position:fixed;bottom:30px;left:50%;transform:translateX(-50%) translateY(20px);background:rgba(0,0,0,.85);color:#fff;padding:10px 20px;border-radius:24px;font-size:14px;z-index:3000;opacity:0;transition:.25s;pointer-events:none;}',
  '#cartToast.show{opacity:1;transform:translateX(-50%) translateY(0);}',
  '@media(max-width:640px){#cartSheet{max-width:100%;}}'
  ].join('');

  function updateBadge(){var c=document.getElementById('cartCount');if(!c)return;var n=totalQty();c.textContent=n>0?n:'';c.style.display=n>0?'':'none';}
  function openCart(){renderCart();document.getElementById('cartOverlay').classList.add('open');document.body.style.overflow='hidden';}
  function closeCart(){document.getElementById('cartOverlay').classList.remove('open');document.body.style.overflow='';}

  function renderCart(){
    var c=load(),body=document.getElementById('cartBody'),foot=document.getElementById('cartFoot');
    if(!c.length){body.innerHTML='<div class="cart-empty">購物車是空的 🛒</div>';foot.innerHTML='';return;}
    body.innerHTML=c.map(function(it,i){
      var meta=[];if(it.color)meta.push('顏色:'+esc(it.color));if(it.size)meta.push('尺寸:'+esc(it.size));
      return '<div class="cart-item"><img src="'+esc(it.img||'')+'" alt="">'+
        '<div class="ci-info"><div class="ci-brand">'+esc(it.brand||'')+'</div><div class="ci-title">'+esc(it.title||'')+'</div>'+
        '<div class="ci-meta">'+meta.join('　')+'</div>'+
        '<div class="ci-bot"><div class="ci-qty"><button type="button" data-act="dec" data-i="'+i+'">−</button><span>'+(it.qty||1)+'</span><button type="button" data-act="inc" data-i="'+i+'">＋</button></div>'+
        '<span class="ci-price">'+yen((it.price||0)*(it.qty||1))+'</span></div></div>'+
        '<button class="ci-del" type="button" data-act="del" data-i="'+i+'">✕</button></div>';
    }).join('');
    foot.innerHTML='<div class="cart-total"><span>合計</span><b>'+yen(totalYen())+'</b></div>'+
      '<button id="cartSubmit" type="button" class="cart-submit">送出訂購單（轉導 LINE）</button>';
    body.querySelectorAll('button[data-act]').forEach(function(b){b.addEventListener('click',function(){onAct(b.getAttribute('data-act'),parseInt(b.getAttribute('data-i'),10));});});
    document.getElementById('cartSubmit').addEventListener('click',submitOrder);
  }

  function onAct(act,i){var c=load();if(!c[i])return;if(act==='inc')c[i].qty=(c[i].qty||1)+1;else if(act==='dec')c[i].qty=Math.max(1,(c[i].qty||1)-1);else if(act==='del')c.splice(i,1);save(c);renderCart();}

  function submitOrder(){
    var c=load();if(!c.length){alert('購物車是空的');return;}
    var lines=['【71_egg 訂購單】'],tot=0;
    c.forEach(function(it,i){var q=it.qty||1;tot+=(it.price||0)*q;
      var m=[];if(it.color)m.push('顏色:'+it.color);if(it.size)m.push('尺寸:'+it.size);
      lines.push((i+1)+'. '+(it.brand||'')+' '+(it.title||''));
      lines.push('   '+(m.length?m.join(' / ')+'　':'')+'x'+q+'　'+yen(it.price||0));
      lines.push('   編號:'+(it.id||''));
    });
    lines.push('———');lines.push('合計: '+yen(tot));
    window.open(LINE_OA+encodeURIComponent(lines.join('\n')),'_blank');
  }

  function addToCart(item){
    var c=load(),f=null;
    for(var i=0;i<c.length;i++){if(c[i].id===item.id&&c[i].color===item.color&&c[i].size===item.size){f=c[i];break;}}
    if(f)f.qty=(f.qty||1)+(item.qty||1);else c.push(item);
    save(c);toast('✓ 已加入購物車');
  }

  var toastT;
  function toast(msg){var t=document.getElementById('cartToast');if(!t){t=document.createElement('div');t.id='cartToast';document.body.appendChild(t);}t.textContent=msg;t.classList.add('show');clearTimeout(toastT);toastT=setTimeout(function(){t.classList.remove('show');},1600);}

  function injectUI(){
    var style=document.createElement('style');style.textContent=CSS;document.head.appendChild(style);
    var btn=document.createElement('button');btn.id='cartBtn';btn.type='button';btn.setAttribute('aria-label','購物車');btn.innerHTML='🛒<span id="cartCount"></span>';
    btn.addEventListener('click',openCart);
    var slot=document.getElementById('cartSlot');
    if(slot)slot.appendChild(btn);else{btn.classList.add('fixed');document.body.appendChild(btn);}
    var ov=document.createElement('div');ov.id='cartOverlay';
    ov.innerHTML='<div id="cartSheet"><div id="cartHead"><b>購物車</b><button id="cartClose" type="button" aria-label="關閉">×</button></div><div id="cartBody"></div><div id="cartFoot"></div></div>';
    document.body.appendChild(ov);
    ov.addEventListener('click',function(e){if(e.target===ov)closeCart();});
    document.getElementById('cartClose').addEventListener('click',closeCart);
    document.addEventListener('keydown',function(e){if(e.key==='Escape')closeCart();});
    updateBadge();
  }

  function wireProduct(){
    var sel={color:null,size:null};
    document.querySelectorAll('.opt').forEach(function(o){
      o.addEventListener('click',function(){
        var g=o.getAttribute('data-g');if(!g)return;
        document.querySelectorAll('.opt[data-g="'+g+'"]').forEach(function(x){x.classList.remove('on');});
        o.classList.add('on');sel[g]=o.textContent;
        var sv=document.querySelector('.selval[data-sv="'+g+'"]');if(sv)sv.textContent=o.textContent;
      });
    });
    ['color','size'].forEach(function(g){var os=document.querySelectorAll('.opt[data-g="'+g+'"]');if(os.length===1)os[0].click();});
    var btn=document.getElementById('addBtn');
    if(btn){btn.addEventListener('click',function(){
      var hasColor=document.querySelectorAll('.opt[data-g="color"]').length>0;
      var hasSize=document.querySelectorAll('.opt[data-g="size"]').length>0;
      if(hasColor&&!sel.color){toast('請先選擇顏色');return;}
      if(hasSize&&!sel.size){toast('請先選擇尺寸');return;}
      addToCart({id:btn.getAttribute('data-id'),brand:btn.getAttribute('data-brand'),title:btn.getAttribute('data-title'),price:parseInt(btn.getAttribute('data-price'),10)||0,img:btn.getAttribute('data-img'),color:sel.color||'',size:sel.size||'',qty:1});
    });}
  }

  window.CART={add:addToCart,open:openCart};
  function init(){injectUI();wireProduct();}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
