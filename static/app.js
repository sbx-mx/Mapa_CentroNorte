(() => {
  const root = document.querySelector('.app-shell');
  if (!root) return;
  const page = root.dataset.page;
  const state = { stores: [], filtered: [], markers: [], map: null };
  const colors = ['#00754a','#1f77b4','#7b4ab5','#e18616','#b23a48','#6f5945','#147d92'];
  const dmColors = new Map();
  const $ = id => document.getElementById(id);
  const clean = value => String(value ?? '').trim();
  const normalized = value => clean(value).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toUpperCase();
  const fmtPercent = value => value == null ? '—' : new Intl.NumberFormat('es-MX',{style:'percent',maximumFractionDigits:1}).format(value);
  const fmtMoney = value => value == null ? '—' : new Intl.NumberFormat('es-MX',{style:'currency',currency:'MXN',notation:'compact',maximumFractionDigits:1}).format(value);
  const escapeHtml = value => clean(value).replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));

  function optionize(id, key){
    [...new Set(state.stores.map(store => clean(store[key])).filter(Boolean))].sort((a,b)=>a.localeCompare(b,'es')).forEach(value=>{
      const option=document.createElement('option'); option.value=value; option.textContent=value; $(id).appendChild(option);
    });
  }
  function popup(store){
    const rows=[['CC',store.cc],['DM',store.dm],['Municipio',store.municipality],['Formato',store.format],['Comercial',store.commercial_format],['Tier',store.tier],['Ventas',fmtMoney(store.sales_mxn)],['Dif. ppto',fmtPercent(store.budget_variance_pct)],['NPS',store.nps],['EBITDA',fmtPercent(store.ebitda_pct)],['Corte',store.cutoff_ytd]];
    return `<div class="popup"><h3>${escapeHtml(store.store_name)}</h3><dl class="popup-grid">${rows.map(([k,v])=>`<dt>${escapeHtml(k)}</dt><dd>${escapeHtml(v ?? '—')}</dd>`).join('')}</dl></div>`;
  }
  function initializeMap(){
    state.map=L.map('map',{zoomControl:true}).setView([19.51,-99.18],11);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'© OpenStreetMap contributors',maxZoom:19}).addTo(state.map);
  }
  function render(){
    const query=normalized($('search').value);
    state.filtered=state.stores.filter(store => store.active !== false && (!query || normalized(store.store_name).includes(query) || normalized(store.cc).includes(query)) && ['dm','coverage','tier','format','commercial_format'].every(key=>!$(key).value || clean(store[key])===$(key).value));
    $('visibleCount').textContent=state.filtered.length;
    $('cdmxCount').textContent=state.filtered.filter(s=>normalized(s.coverage).includes('CIUDAD')).length;
    $('edomexCount').textContent=state.filtered.filter(s=>normalized(s.coverage).includes('ESTADO')).length;
    $('dtCount').textContent=state.filtered.filter(s=>normalized(s.format).includes('DRIVE')).length;
    if(page==='mapa') renderMap(); else renderDirectory();
    $('status').textContent=`${state.filtered.length} de ${state.stores.length} tiendas`;
  }
  function renderMap(){
    state.markers.forEach(marker=>marker.remove()); state.markers=[]; const bounds=[];
    state.filtered.forEach(store=>{
      if(!Number.isFinite(store.latitude)||!Number.isFinite(store.longitude)) return;
      if(!dmColors.has(store.dm)) dmColors.set(store.dm,colors[dmColors.size%colors.length]);
      const color=dmColors.get(store.dm); const marker=L.circleMarker([store.latitude,store.longitude],{radius:8,color:'#fff',weight:2,fillColor:color,fillOpacity:.95}).addTo(state.map).bindPopup(popup(store));
      state.markers.push(marker); bounds.push([store.latitude,store.longitude]);
    });
    if(bounds.length) state.map.fitBounds(bounds,{padding:[28,28],maxZoom:13});
  }
  function renderDirectory(){
    $('directory').innerHTML=state.filtered.map(store=>`<article class="store-row"><strong>${escapeHtml(store.cc)}</strong><span>${escapeHtml(store.store_name)}<br><small>${escapeHtml(store.municipality)}</small></span><span>${escapeHtml(store.dm)}</span><span>${escapeHtml(store.commercial_format)}</span><span>${escapeHtml(store.tier)}</span></article>`).join('') || '<p class="status">No hay resultados.</p>';
  }
  function reset(){ ['search','dm','coverage','tier','format','commercial_format'].forEach(id=>$(id).value=''); render(); }
  async function start(){
    try{ const response=await fetch('/api/stores'); if(!response.ok) throw new Error('HTTP '+response.status); const payload=await response.json(); state.stores=payload.stores; ['dm','coverage','tier','format','commercial_format'].forEach(key=>optionize(key,key)); if(page==='mapa') initializeMap(); render(); }
    catch(error){ $('status').textContent='No fue posible cargar la base JSON.'; $('status').classList.add('error'); console.error(error); }
  }
  $('reset').addEventListener('click',reset); ['search','dm','coverage','tier','format','commercial_format'].forEach(id=>$(id).addEventListener(id==='search'?'input':'change',render)); start();
})();

