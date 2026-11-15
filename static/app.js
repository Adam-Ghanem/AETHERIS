/* AETHERIS — independent scientific frontend. No user-facing fabricated data. */
(() => {
  'use strict';
  const NS = 'http://www.w3.org/2000/svg';
  const $ = (id) => document.getElementById(id);
  const els = (sel) => Array.from(document.querySelectorAll(sel));
  const state = {
    lat: 32.337, lon: -6.349, selectedName: 'Beni Mellal',
    locations: [], currentResult: null, compareResult: null, discoveryResult: null, forensicsResult: null, spatialResult: null, systemsResult: null, signalsResult: null, breakpointResult: null, timeMachineResult: null, timeMachinePoint: "p4", timeMachineTimer: null, aiAvailable: false,
    activeRequest: null, toasty: null,
  };
  const v = (x, digits=2) => x == null || !Number.isFinite(Number(x)) ? '—' : Number(x).toFixed(digits);
  const asText = (id, value) => { const e=$(id); if (e) e.textContent = value; };
  const escapeHtml = (s) => String(s ?? '').replace(/[&<>"']/g, ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));

  function toast(message) {
    const node = $('toast'); node.textContent = message; node.classList.add('show');
    clearTimeout(state.toasty); state.toasty = setTimeout(()=>node.classList.remove('show'), 3500);
  }
  async function api(path, opts={}) {
    let response;
    try { response = await fetch(path, opts); }
    catch (error) {
      if (error.name === 'AbortError') throw error;
      throw new Error('Cannot reach the AETHERIS server. Check the local server and your network connection.');
    }
    let payload;
    try { payload = await response.json(); }
    catch { throw new Error(`Invalid server response (HTTP ${response.status}).`); }
    if (!response.ok) throw new Error(payload.error?.message || payload.detail?.[0]?.msg || `Server error HTTP ${response.status}`);
    return payload;
  }
  function go(view) {
    els('.view').forEach(x => x.classList.toggle('active', x.id === `view-${view}`));
    els('.nav-link').forEach(x => x.classList.toggle('active', x.dataset.view === view));
    location.hash = view;
    const sidebar=$('sidebar');sidebar.classList.remove('menu-open');
    const toggle=$('mobile-menu-toggle');if(toggle)toggle.setAttribute('aria-expanded','false');
    if(view==='notebook')renderNotebook();
    if(view!=='timemachine')stopTimeMachinePlayback();
    window.scrollTo({top:0,behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});
  }
  function pointCoord(lat, lon) {return {x:(lon+180)*960/360,y:(90-lat)*480/180};}
  function updateMarker() {
    const p=pointCoord(state.lat,state.lon);
    $('map-marker').setAttribute('transform',`translate(${p.x.toFixed(2)},${p.y.toFixed(2)})`);
    const f=(n,pos,neg)=>`${Math.abs(n).toFixed(3)}° ${n>=0?pos:neg}`;
    asText('map-coordinate-label',`${f(state.lat,'N','S')} · ${f(state.lon,'E','W')}`);
  }
  function setLocation(lat,lon,name='Custom coordinates',syncSelect=true) {
    state.lat=Number(lat);state.lon=Number(lon);state.selectedName=name;
    $('lat-input').value=state.lat.toFixed(4);$('lon-input').value=state.lon.toFixed(4);
    if (syncSelect) {
      const found=state.locations.find(x=>Math.abs(x.lat-state.lat)<.001 && Math.abs(x.lon-state.lon)<.001);
      $('place-select').value=found ? `${found.lat},${found.lon}`:'custom';
    }
    updateMarker();
  }
  function renderLand(geo) {
    const layer=$('world-land'); layer.innerHTML='';
    function drawRing(ring){
      if(!Array.isArray(ring)||ring.length<3)return;
      return ring.map((p,i)=>{const q=pointCoord(p[1],p[0]);return `${i?'L':'M'}${q.x.toFixed(2)},${q.y.toFixed(2)}`;}).join('')+'Z';
    }
    const parts=[];
    for(const geom of geo.geometries || []) {
      if (geom.type==='Polygon') parts.push(geom.coordinates.map(drawRing).join(''));
      else if(geom.type==='MultiPolygon') for(const poly of geom.coordinates) parts.push(poly.map(drawRing).join(''));
    }
    const land=document.createElementNS(NS,'path'); land.setAttribute('d',parts.join(' '));
    land.setAttribute('fill','#e7c95e');land.setAttribute('fill-rule','evenodd');
    land.setAttribute('stroke','#b4a46c');land.setAttribute('stroke-width','.66');
    land.setAttribute('vector-effect','non-scaling-stroke');
    layer.appendChild(land);
  }
  function drawMapGrid(){
    const layer=$('grid-lines');layer.innerHTML='';
    for(let lon=-150;lon<=180;lon+=30){const x=(lon+180)*960/360;const e=document.createElementNS(NS,'line');for(const [k,val] of Object.entries({x1:x,x2:x,y1:0,y2:480,stroke:'#d9d1ad','stroke-width':.75,'stroke-dasharray':'3 7',opacity:.64}))e.setAttribute(k,val);layer.appendChild(e);}
    for(let lat=-60;lat<=60;lat+=30){const y=(90-lat)*480/180;const e=document.createElementNS(NS,'line');for(const [k,val] of Object.entries({x1:0,x2:960,y1:y,y2:y,stroke:'#d9d1ad','stroke-width':.75,'stroke-dasharray':'3 7',opacity:.64}))e.setAttribute(k,val);layer.appendChild(e);}
  }
  async function loadMap(){
    drawMapGrid();updateMarker();
    try{const resp=await fetch('/static/assets/world.json');if(!resp.ok)throw Error('Failed');renderLand(await resp.json());}
    catch {toast('World outline unavailable; coordinate selection still works.');}
    $('earth-map').addEventListener('click',event=>{
      const svg=$('earth-map');const pt=svg.createSVGPoint();pt.x=event.clientX;pt.y=event.clientY;
      const m=svg.getScreenCTM();if(!m)return;const p=pt.matrixTransform(m.inverse());
      if(p.x<0||p.x>960||p.y<0||p.y>480)return;
      const lon=p.x/960*360-180, lat=90-p.y/480*180;
      setLocation(Math.max(-90,Math.min(90,lat)),Math.max(-180,Math.min(180,lon)));
    });
  }
  function setupLocations(){
    const opts=state.locations.map(x=>`<option value="${x.lat},${x.lon}">${escapeHtml(x.name)}, ${escapeHtml(x.country)}</option>`).join('');
    $('place-select').innerHTML=opts+'<option value="custom">Custom coordinates</option>';
    $('compare-a').innerHTML=opts;$('compare-b').innerHTML=opts;
    $('place-select').value='32.337,-6.349';
    $('forensics-location').innerHTML=state.locations.map(p=>`<option value="${escapeHtml(p.name)}">${escapeHtml(p.name)}, ${escapeHtml(p.country)}</option>`).join('');
    $('forensics-location').value='Beni Mellal';
    $('spatial-location').innerHTML=state.locations.filter(p=>Math.abs(p.lat)<=75).map(p=>`<option value="${escapeHtml(p.name)}">${escapeHtml(p.name)}, ${escapeHtml(p.country)}</option>`).join('')+'<option value="custom">Custom coordinates</option>'; 
    $('spatial-location').value='Beni Mellal';
    $('spatial-location').addEventListener('change',()=>{const q=state.locations.find(p=>p.name===$('spatial-location').value);if(q){$('spatial-lat').value=q.lat;$('spatial-lon').value=q.lon;}});
    for(const id of ['spatial-lat','spatial-lon']) $(id).addEventListener('change',()=>{$('spatial-location').value='custom';});
    $('tm-location').innerHTML=state.locations.filter(p=>Math.abs(p.lat)<=75).map(p=>`<option value="${escapeHtml(p.name)}">${escapeHtml(p.name)}, ${escapeHtml(p.country)}</option>`).join('')+'<option value="custom">Custom coordinates</option>';
    $('tm-location').value='Beni Mellal';
    $('tm-location').addEventListener('change',()=>{const p=state.locations.find(x=>x.name===$('tm-location').value);if(p){$('tm-lat').value=p.lat;$('tm-lon').value=p.lon;}});
    for(const id of ['tm-lat','tm-lon'])$(id).addEventListener('change',()=>{$('tm-location').value='custom';});
    const m=state.locations.find(x=>x.name==='Marrakech'); if(m)$('compare-b').value=`${m.lat},${m.lon}`;
  }
  const xy=(tag,attrs={},text=null)=>{const el=document.createElementNS(NS,tag);Object.entries(attrs).forEach(([k,x])=>el.setAttribute(k,x));if(text!=null)el.textContent=text;return el;};
  function renderLineChart(target, series, settings={}){
    const node=$(target);node.innerHTML='';const W=760,H=settings.large?310:240,pad={l:55,r:22,t:18,b:38};
    const all=series.flatMap(s=>s.points).filter(p=>p&&Number.isFinite(p.value));
    if(!all.length){node.textContent='No chartable observations.';return;}
    let minX=Math.min(...all.map(p=>p.year)),maxX=Math.max(...all.map(p=>p.year));
    if(maxX===minX)maxX+=1;
    let minY=Math.min(...all.map(p=>p.value)),maxY=Math.max(...all.map(p=>p.value));
    if(settings.zero){minY=Math.min(minY,0);maxY=Math.max(maxY,0);}
    const r=maxY-minY||1;minY-=r*.12;maxY+=r*.12;
    const X=x=>pad.l+(x-minX)/(maxX-minX)*(W-pad.l-pad.r);
    const Y=y=>H-pad.b-(y-minY)/(maxY-minY)*(H-pad.t-pad.b);
    const svg=xy('svg',{viewBox:`0 0 ${W} ${H}`,class:`chart-svg${settings.large?' large':''}`,role:'img','aria-label':settings.label||'Annual scientific time-series chart'});
    const defs=xy('defs'),grad=xy('linearGradient',{id:'chartGlow',x1:'0',y1:'0',x2:'0',y2:'1'});grad.appendChild(xy('stop',{offset:'0','stop-color':'#e6b82f','stop-opacity':'.19'}));grad.appendChild(xy('stop',{offset:'1','stop-color':'#e6b82f','stop-opacity':'.01'}));defs.appendChild(grad);svg.appendChild(defs);
    for(let i=0;i<=4;i++){const val=minY+(maxY-minY)*i/4;const y=Y(val);svg.appendChild(xy('line',{x1:pad.l,x2:W-pad.r,y1:y,y2:y,class:'chart-gridline'}));svg.appendChild(xy('text',{x:pad.l-9,y:y+3,'text-anchor':'end'}, val.toFixed(Math.abs(maxY-minY)<3?2:1)));}
    for(let i=0;i<=5;i++){const yr=Math.round(minX+(maxX-minX)*i/5),x=X(yr);svg.appendChild(xy('text',{x,y:H-14,'text-anchor':'middle'},yr));}
    if(settings.zero && minY<0 && maxY>0)svg.appendChild(xy('line',{x1:pad.l,x2:W-pad.r,y1:Y(0),y2:Y(0),class:'chart-zero'}));
    for(const [idx,s] of series.entries()){
      const pts=s.points.filter(p=>Number.isFinite(p.value)).sort((a,b)=>a.year-b.year);
      const d=pts.map((p,i)=>`${i?'L':'M'}${X(p.year).toFixed(2)},${Y(p.value).toFixed(2)}`).join(' ');
      if(idx===0&&!settings.bars&&pts.length>1&&series.length<=2){const p0=pts[0],pn=pts[pts.length-1];svg.appendChild(xy('path',{d:`${d} L${X(pn.year)},${H-pad.b} L${X(p0.year)},${H-pad.b} Z`,fill:'url(#chartGlow)'}));}
      if(settings.bars){const width=Math.max(2,Math.min(18,(W-pad.l-pad.r)/pts.length*.58));for(const p of pts){const y=Y(p.value),base=Y(0);const rect=xy('rect',{x:X(p.year)-width/2,y:Math.min(y,base),width,height:Math.max(1,Math.abs(y-base)),class:`chart-bar ${p.value>=0?'pos':'neg'}`});rect.appendChild(xy('title',{},`${p.year}: ${v(p.value,3)} ${settings.unit||''}`));svg.appendChild(rect);}}
      else{const line=xy('path',{d,class:idx===0?'chart-series':s.className||'chart-fit'});if(s.color)line.setAttribute('stroke',s.color);svg.appendChild(line);
        if(idx===0&&pts.length<45){for(const p of pts){const c=xy('circle',{cx:X(p.year),cy:Y(p.value),r:3.1,class:'chart-point'});c.appendChild(xy('title',{},`${p.year}: ${v(p.value,3)} ${settings.unit||''}`));svg.appendChild(c);}}
      }
    }
    node.appendChild(svg);
  }
  function showError(msg){$('analysis-loading').classList.add('hidden');$('analysis-results').classList.add('hidden');$('analysis-error').classList.remove('hidden');asText('analysis-error-text',msg);}
  function showLoading(){ $('analysis-empty').classList.add('hidden');$('analysis-error').classList.add('hidden');$('analysis-results').classList.add('hidden');$('analysis-loading').classList.remove('hidden');$('analyze-btn').disabled=true;asText('analyze-btn','Retrieving NASA data…');}
  function readyButton(){ $('analyze-btn').disabled=false;$('analyze-btn').innerHTML='Analyze NASA data <span id="analyze-arrow">↗</span>'; }
  function readForm(){
    if(!$('lat-input').value.trim()||!$('lon-input').value.trim()||!$('start-year').value.trim()||!$('end-year').value.trim())throw new Error('Location and date inputs cannot be empty.');
    const lat=Number($('lat-input').value),lon=Number($('lon-input').value),start=Number($('start-year').value),end=Number($('end-year').value),variable=$('variable-select').value;
    if(!Number.isFinite(lat)||lat < -90||lat >90||!Number.isFinite(lon)||lon < -180||lon>180)throw new Error('Choose valid coordinates (-90° to 90° latitude, -180° to 180° longitude).');
    if(!Number.isInteger(start)||!Number.isInteger(end)||start<1981||end>new Date().getUTCFullYear()-1||end-start<7||end-start>44)throw new Error('Choose at least 8 historical years from 1981 through the previous complete calendar year.');
    return {lat,lon,start,end,variable};
  }
  function buildQuery(args){return new URLSearchParams(Object.entries(args).map(([k,val])=>[k,String(val)])).toString();}
  async function runAnalysis(evt){evt?.preventDefault();let args;try{args=readForm();}catch(err){toast(err.message);return;}
    if(state.activeRequest)state.activeRequest.abort();
    const ctl=new AbortController();state.activeRequest=ctl;showLoading();
    try{const data=await api(`/api/v1/investigate?${buildQuery(args)}`,{signal:ctl.signal});state.currentResult=data;renderAnalysis(data);$('analysis-loading').classList.add('hidden');$('analysis-results').classList.remove('hidden');setLocation(args.lat,args.lon,state.selectedName);toast('Scientific investigation complete.');}
    catch(err){if(err.name!=='AbortError')showError(err.message);}
    finally{if(state.activeRequest===ctl){state.activeRequest=null;readyButton();}}
  }
  function renderAnalysis(d){
    const t=d.trend, isTemp=d.variable.id==='T2M',annUnit=t.annual_unit;
    asText('result-title',`${state.selectedName} · ${d.variable.label}`);
    asText('result-subtitle',`${d.period.observed_start}–${d.period.observed_end} · ${d.location.latitude.toFixed(3)}° N/S, ${d.location.longitude.toFixed(3)}° E/W · NASA POWER`);
    asText('metric-slope',`${t.slope_per_decade>0?'+':''}${v(t.slope_per_decade,2)}`);
    asText('metric-direction',`${t.slope_unit} · ${t.slope_per_decade>0?'Upward':t.slope_per_decade<0?'Downward':'Flat'} trend`);
    asText('metric-significance',t.significance_label==='significant'?'Significant':t.significance_label==='not significant'?'Not significant':'Inconclusive');
    asText('metric-p',`HAC p = ${t.p_value_hac==null?'unavailable':(t.p_value_hac<.00001?'<0.00001':v(t.p_value_hac,5))} · α = 0.05`);
    asText('metric-interval',t.ci95_hac_per_decade?`${v(t.ci95_hac_per_decade[0],2)} to ${v(t.ci95_hac_per_decade[1],2)}`:'Not assessed');
    asText('metric-years',String(t.sample_size));asText('metric-range',`${t.start_year}–${t.end_year} · complete years`);
    renderLineChart('trend-chart',[{points:d.annual},{points:t.fitted,className:'chart-fit'}],{unit:annUnit});
    renderLineChart('anomaly-chart',[{points:d.anomalies}],{unit:annUnit,zero:true,bars:true});
    const direction=t.slope_per_decade>0?'increasing':t.slope_per_decade<0?'decreasing':'approximately stable';
    const evidence=t.significance_label==='significant'?'shows statistical evidence of a nonzero linear slope under the stated HAC model assumptions':
      t.significance_label==='not significant'?'does not provide sufficient evidence of a nonzero linear slope at the 5% threshold':'has inconclusive statistical evidence';
    $('interpretation').innerHTML=`For the selected point, annual <strong>${escapeHtml(d.variable.label.toLowerCase())}</strong> is estimated to be <strong>${direction}</strong> at <strong>${escapeHtml((t.slope_per_decade>0?'+':'')+v(t.slope_per_decade,3))} ${escapeHtml(t.slope_unit)}</strong>. The analysis ${escapeHtml(evidence)}. A statistical trend describes an observed pattern; it does not by itself identify a cause.`;
    asText('robust-slope',`${t.theil_sen_per_decade>0?'+':''}${v(t.theil_sen_per_decade,2)} ${t.slope_unit}`);
    asText('r-squared',t.r_squared==null?'—':v(t.r_squared,3));
    asText('baseline-range',`${d.anomaly_baseline.start_year}–${d.anomaly_baseline.end_year}`);
    const fields=[['Data provider',d.evidence.provider],['Source product',d.evidence.product],['Variable & unit',`${d.variable.id} / ${annUnit}`],['Coordinates',`${d.location.latitude}, ${d.location.longitude}`],['Aggregation',d.evidence.annual_aggregation],['Method',d.evidence.science_method],['Data fingerprint',`SHA-256 ${d.evidence.sha256_monthly.slice(0,22)}…`],['Retrieved (UTC)',d.evidence.retrieved_at?d.evidence.retrieved_at.slice(0,19):'—'],['Source request',d.evidence.source_request? 'NASA POWER API (see JSON export)' :'See NASA POWER documentation']];
    $('evidence-list').innerHTML=fields.map(([a,b])=>`<div><dt>${escapeHtml(a)}</dt><dd>${escapeHtml(b)}</dd></div>`).join('');
    $('limitations-list').innerHTML=d.limitations.map(x=>`<li>${escapeHtml(x)}</li>`).join('');
    window.AetherisQuality?.render(d);
    renderSeasonality(d);
    asText('save-investigation', savedHas(d) ? '★ Saved investigation' : '☆ Save investigation');
  }
  function renderSeasonality(d) {
    const container = $('seasonal-chart');container.innerHTML = '';
    const months = d.seasonality?.months || [];
    if (!months.length) {container.textContent='No complete seasonal profile available.';return;}
    const values=months.map(p=>p.mean),min=Math.min(...values),max=Math.max(...values);
    const H= Math.max(1,max-min);
    for (const point of months) {
      const col=document.createElement('div');col.className='season-column';
      const bar=document.createElement('span');bar.className='season-column-bar';
      bar.style.height=`${18+82*(point.mean-min)/H}%`;
      bar.title=`${point.label}: ${v(point.mean,2)} ${d.seasonality.unit} (${point.samples} observations)`;
      const label=document.createElement('small');label.textContent=point.label;
      col.appendChild(bar);col.appendChild(label);container.appendChild(col);
    }
    asText('seasonal-note',`${d.seasonality.method} · ${d.seasonality.unit}. ${d.seasonality.limitation}`);
    $('unusual-years').innerHTML=(d.unusual_years||[]).map((y,i)=>`<div class="extreme-row"><span class="extreme-index">0${i+1}</span><strong>${y.year}</strong><span class="extreme-departure">${y.departure>=0?'+':''}${v(y.departure,2)} ${escapeHtml(d.trend.annual_unit)}</span><small>${escapeHtml(v(y.annual_value,2))} ${escapeHtml(d.trend.annual_unit)} annual</small></div>`).join('');
  }
  function savedKey(d) {return `aetheris:${d.variable.id}:${d.location.latitude.toFixed(4)},${d.location.longitude.toFixed(4)}:${d.period.requested_start}-${d.period.requested_end}`;}
  function savedHas(d) {try{return Boolean(localStorage.getItem(savedKey(d)));}catch{return false;}}
  function saveInvestigation() {
    const d=state.currentResult;if(!d)return toast('Run an investigation first.');
    const key=savedKey(d);
    try {
      if(localStorage.getItem(key)){localStorage.removeItem(key);asText('save-investigation','☆ Save investigation');toast('Saved investigation removed.');}
      else {localStorage.setItem(key,JSON.stringify({saved_at:new Date().toISOString(),result:d,location_name:state.selectedName}));asText('save-investigation','★ Saved investigation');toast('Investigation saved in this browser.');}
    } catch {toast('Browser storage is full or unavailable. Download Evidence JSON instead.');}
  }
  function renderNotebook() {
    const node=$('notebook-list');const records=[];
    try {
      for(let i=0;i<localStorage.length;i++) {
        const key=localStorage.key(i);if(!key?.startsWith('aetheris:'))continue;
        try {const entry=JSON.parse(localStorage.getItem(key));if(entry?.result?.annual?.length&&entry?.result?.evidence?.sha256_monthly)records.push({key,entry});}catch{}
      }
    } catch {node.textContent='Browser storage is unavailable.';return;}
    records.sort((a,b)=>(b.entry.saved_at||'').localeCompare(a.entry.saved_at||''));
    node.innerHTML=records.length?records.map(({key,entry},i)=>{
      const d=entry.result;
      return `<article class="notebook-row"><div><span class="eyebrow">RESEARCH SNAPSHOT / ${String(i+1).padStart(2,'0')}</span><h3>${escapeHtml(entry.location_name||'Selected location')}</h3><p>${escapeHtml(d.variable?.label||d.variable?.id||'Unknown')} · ${d.period?.observed_start}–${d.period?.observed_end} · saved ${escapeHtml((entry.saved_at||'').slice(0,16).replace('T',' '))} UTC</p></div><div class="notebook-actions"><button class="btn btn-outline notebook-open" data-key="${escapeHtml(key)}" type="button">Open snapshot ↗</button><button class="btn btn-ghost notebook-delete" data-key="${escapeHtml(key)}" type="button">Delete</button></div></article>`;
    }).join(''):'<div class="empty-state"><h3>No investigations saved yet.</h3><p>Run an investigation in Earth Explorer and select Save investigation to build your local notebook.</p></div>';
    els('.notebook-open').forEach(btn=>btn.addEventListener('click',()=>{
      try{const e=JSON.parse(localStorage.getItem(btn.dataset.key));const d=e.result;
        if(!d?.annual?.length||!d?.trend?.fitted?.length||!d?.evidence?.sha256_monthly)throw Error('Invalid saved investigation');
        state.currentResult=d;state.selectedName=e.location_name||'Saved point';
        setLocation(d.location.latitude,d.location.longitude,state.selectedName);
        $('start-year').value=d.period.requested_start;$('end-year').value=d.period.requested_end;$('variable-select').value=d.variable.id;
        renderAnalysis(d);$('analysis-empty').classList.add('hidden');$('analysis-error').classList.add('hidden');$('analysis-results').classList.remove('hidden');go('explore');toast('Saved snapshot opened. Historical data has not been refreshed.');
      }catch{toast('Saved investigation is corrupted or unavailable.');}
    }));
    els('.notebook-delete').forEach(btn=>btn.addEventListener('click',()=>{try{localStorage.removeItem(btn.dataset.key);renderNotebook();}catch{toast('Could not remove stored investigation.');}}));
  }
  async function checkAI() {
    try{const status=await api('/api/v1/intelligence/status');state.aiAvailable=Boolean(status.available);
      asText('ai-status',state.aiAvailable?'External model endpoint configured':'External AI model not connected');
      $('ai-analyze').disabled=!state.aiAvailable;
    }catch{asText('ai-status','AI module unavailable');$('ai-analyze').disabled=true;}
  }
  async function runAI() {
    const d=state.currentResult;if(!d)return toast('Run NASA investigation first.');
    if(!state.aiAvailable)return toast('No trained model is connected.');
    const button=$('ai-analyze');button.disabled=true;button.textContent='Running external model…';
    const node=$('ai-output');node.classList.remove('hidden');node.textContent='Waiting for the configured ML inference service…';
    try{const q={lat:d.location.latitude,lon:d.location.longitude,start:d.period.requested_start,end:d.period.requested_end,variable:d.variable.id};
      const res=await api(`/api/v1/intelligence/analyze?${buildQuery(q)}`);const m=res.model;
      node.innerHTML=`<strong>${escapeHtml(m.model_name)} · ${escapeHtml(m.model_version)}</strong><p>${escapeHtml(m.methodology)}</p><div class="ai-signals">${m.signals.length?m.signals.map(s=>`<div><span>${s.year}</span><strong>${s.is_anomaly?'Flagged':'Not flagged'} · ${v(s.anomaly_score,3)}</strong><small>${escapeHtml(s.explanation)}</small></div>`).join(''):'<p>Model returned no anomaly signals for this input.</p>'}</div><p class="comparison-caveat">${m.limitations.map(escapeHtml).join(' • ')}</p>`;
    }catch(err){node.textContent=`AI inference unavailable: ${err.message}`;}
    finally{button.disabled=!state.aiAvailable;button.textContent='Run connected AI ↗';}
  }
  function downloadPdf() {
    const d=state.currentResult;if(!d)return toast('Run an investigation first.');
    const q={lat:d.location.latitude,lon:d.location.longitude,start:d.period.requested_start,end:d.period.requested_end,variable:d.variable.id,place:state.selectedName};
    window.open(`/api/v1/report.pdf?${buildQuery(q)}`,'_blank','noopener');
  }
  function setupDiscoverPlaces() {
    const defaultNames=new Set(['Beni Mellal','Marrakech','Casablanca','Ouarzazate']);
    $('discovery-places').innerHTML=state.locations.map(loc=>`<label class="scan-place"><input type="checkbox" value="${escapeHtml(loc.name)}" ${defaultNames.has(loc.name)?'checked':''}><span>${escapeHtml(loc.name)}</span><small>${escapeHtml(loc.country)}</small></label>`).join('');
  }
  async function runDiscovery(evt) {
    evt.preventDefault();
    const selected=els('#discovery-places input:checked').map(x=>x.value);
    if(selected.length<2 || selected.length>6)return toast('Select between 2 and 6 locations.');
    const start=Number($('discover-start').value),end=Number($('discover-end').value);
    if(!Number.isInteger(start)||!Number.isInteger(end)||start<1981||end>new Date().getUTCFullYear()-1||end-start<7||end-start>44)return toast('Choose 8–45 historical years.');
    $('discover-loading').classList.remove('hidden');$('discover-error').classList.add('hidden');$('discover-results').classList.add('hidden');$('discover-button').disabled=true;
    try {
      const q={locations:selected.join(','),start,end,variable:$('discover-variable').value};
      const d=await api(`/api/v1/discover?${buildQuery(q)}`);state.discoveryResult=d;
      const unit=d.locations.find(x=>x.status==='ok')?.slope_unit||'';
      $('discovery-summary').innerHTML=`<div class="scan-summary-kpi"><span>POINTS EVALUATED</span><strong>${d.successful}</strong></div><div class="scan-summary-kpi"><span>FAILED REQUESTS</span><strong>${d.failed}</strong></div><div class="scan-summary-kpi"><span>VARIABLE</span><strong>${escapeHtml(d.variable)}</strong></div><div class="scan-summary-kpi"><span>PERIOD</span><strong>${d.period.start}–${d.period.end}</strong></div>`;
      const maxSlope=Math.max(.00001,...d.locations.filter(x=>x.status==='ok').map(x=>Math.abs(x.slope_per_decade)));
      $('discovery-rows').innerHTML=d.locations.map((item,i)=>{
        if(item.status!=='ok')return `<article class="discovery-row"><div class="discovery-label"><span class="eyebrow">UNAVAILABLE POINT</span><h3>${escapeHtml(item.location)}</h3><p>${escapeHtml(item.error)}</p></div><span class="scan-fail">Could not retrieve</span></article>`;
        const width=Math.max(2,Math.round(Math.abs(item.slope_per_decade)/maxSlope*100));
        const slope=`${item.slope_per_decade>=0?'+':''}${v(item.slope_per_decade,3)} ${escapeHtml(unit)}`;
        return `<article class="discovery-row"><div class="discovery-label"><span class="eyebrow">POINT ${String(i+1).padStart(2,'0')} · ${escapeHtml(item.country)}</span><h3>${escapeHtml(item.location)}</h3><p>${item.sample_size} complete years · ${escapeHtml(item.lat.toFixed(3)+', '+item.lon.toFixed(3))}</p></div><div class="discovery-value"><strong>${slope}</strong><div class="scan-bar"><span style="width:${width}%;background:${item.slope_per_decade>=0?'#d4a600':'#4e7dab'}"></span></div><small>HAC p: ${item.p_value_hac==null?'n/a':v(item.p_value_hac,4)} · BH adjusted: ${item.adjusted_p_bh==null?'n/a':v(item.adjusted_p_bh,4)} ${item.fdr_flag_05?'· FDR flag':''}</small></div><button type="button" class="btn btn-outline scan-open" data-name="${escapeHtml(item.location)}">Investigate ↗</button></article>`;
      }).join('');
      $('discovery-limitations').innerHTML=d.limitations.map(x=>`<p>• ${escapeHtml(x)}</p>`).join('');
      els('.scan-open').forEach(btn=>btn.addEventListener('click',()=>{const loc=state.locations.find(x=>x.name===btn.dataset.name);if(!loc)return;setLocation(loc.lat,loc.lon,loc.name);$('start-year').value=d.period.start;$('end-year').value=d.period.end;$('variable-select').value=d.variable;go('explore');runAnalysis();}));
      $('discover-results').classList.remove('hidden');toast(`${d.successful} NASA points evaluated.`);
    }catch(error){$('discover-error').classList.remove('hidden');$('discover-error').textContent=error.message;}
    finally{$('discover-loading').classList.add('hidden');$('discover-button').disabled=false;}
  }
  function exportDiscovery(){if(!state.discoveryResult)return toast('Run a scan first.');download('AETHERIS_discovery_scan.json',JSON.stringify(state.discoveryResult,null,2),'application/json');}
  function download(filename, data, type){const blob=new Blob([data],{type});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=filename;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),6000);}
  function exportCSV(){const d=state.currentResult;if(!d){toast('Run an investigation first.');return;}const csv='year,annual_value,unit,anomaly,ols_fitted\n'+d.annual.map((p,i)=>`${p.year},${p.value},${d.trend.annual_unit},${d.anomalies[i]?.value??''},${d.trend.fitted[i]?.value??''}`).join('\n');download(`aetheris_${d.variable.id}_${d.period.observed_start}-${d.period.observed_end}.csv`,csv,'text/csv;charset=utf-8');}
  function exportJSON(){const d=state.currentResult;if(!d){toast('Run an investigation first.');return;}download(`aetheris_evidence_${d.variable.id}.json`,JSON.stringify(d,null,2),'application/json');}
  function chosenPlace(select){return state.locations.find(x=>`${x.lat},${x.lon}`===select.value);}
  async function runComparison(evt){evt.preventDefault();const a=chosenPlace($('compare-a')),b=chosenPlace($('compare-b'));if(!a||!b)return toast('Choose two locations.');if(a.name===b.name)return toast('Choose two different locations.');
    $('compare-empty').classList.add('hidden');$('compare-results').classList.add('hidden');$('compare-error').classList.add('hidden');$('compare-loading').classList.remove('hidden');$('compare-btn').disabled=true;
    try{const start=Number($('compare-start').value),end=Number($('compare-end').value);
      if(!Number.isInteger(start)||!Number.isInteger(end)||start<1981||end>new Date().getUTCFullYear()-1||end-start<7||end-start>44)throw Error('Choose a valid historical period of 8–45 complete years.');
      const q={lat_a:a.lat,lon_a:a.lon,lat_b:b.lat,lon_b:b.lon,start,end,variable:$('compare-variable').value};const data=await api(`/api/v1/compare?${buildQuery(q)}`);
      state.compareResult=data;asText('compare-a-name',a.name);asText('compare-b-name',b.name);asText('legend-a',a.name);asText('legend-b',b.name);
      for(const [id,part]of [['a',data.first],['b',data.second]]){asText(`compare-${id}-slope`,`${part.trend.slope_per_decade>0?'+':''}${v(part.trend.slope_per_decade,2)} ${part.trend.slope_unit}`);asText(`compare-${id}-significance`,`${part.trend.significance_label} · ${part.trend.sample_size} years`);}
      renderLineChart('comparison-chart',[{points:data.first.annual},{points:data.second.annual,className:'chart-line-b',color:'#3776a6'}],{unit:data.first.trend.annual_unit,large:true});
      $('compare-results').classList.remove('hidden');toast('Regional comparison complete.');
    }catch(err){$('compare-error').classList.remove('hidden');$('compare-error').textContent=err.message;}
    finally{$('compare-loading').classList.add('hidden');$('compare-btn').disabled=false;}
  }
  // V3: Real NASA climate-forensic analysis, distinct from AI/ML claims.
  function showForensicsFromCurrent() {
    const d=state.currentResult;
    if(d){
      $('forensics-start').value=d.period.requested_start;
      $('forensics-end').value=d.period.requested_end;
      $('forensics-variable').value=d.variable.id;
      const preset=state.locations.find(p=>Math.abs(p.lat-d.location.latitude)<.001&&Math.abs(p.lon-d.location.longitude)<.001);
      if(preset)$('forensics-location').value=preset.name;
    }
    go('forensics');
  }
  function renderForensics(data, place){
    const c=data.period_contrast,j=data.jackknife,s=data.seasonal_shift;
    const signed=x=>`${x>0?'+':''}${v(x,2)}`;
    asText('forensics-result-title',`${place} · ${data.variable.label}`);
    asText('forensics-period-label',`${data.period.observed_start}–${data.period.observed_end} · NASA POWER · ${data.annual_observations.length} complete years`);
    const values=[
      ['EARLY → LATE SHIFT',`${signed(c.difference)} ${c.unit}`,`${c.first_period.start}–${c.first_period.end} vs ${c.last_period.start}–${c.last_period.end}`],
      ['TREND DIRECTION STABILITY',j.direction_stable_under_single_year_removal?'Stable':'Sensitive','Sign unchanged when any single year is omitted'],
      ['SLOPE SENSITIVITY',`${v(j.minimum_slope_per_decade,2)} to ${v(j.maximum_slope_per_decade,2)}`,j.unit+' · leave-one-year-out range'],
      ['ROLLING HISTORY',`${data.rolling.points.length} windows`,`${data.rolling.window_years}-year trailing averages`],
    ];
    $('forensics-summary').innerHTML=values.map(([label,value,note])=>`<article class="forensic-kpi"><span class="eyebrow">${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong><p>${escapeHtml(note)}</p></article>`).join('');
    renderLineChart('forensics-rolling-chart',[{points:data.annual_observations},{points:data.rolling.points,className:'chart-line-b',color:'#3776a6'}],{unit:j.unit.replace('/decade',''),large:true,label:'Annual observations and rolling mean'});
    renderLineChart('forensics-jackknife-chart',[{points:j.points.map(p=>({year:p.omitted_year,value:p.slope_per_decade}))}],{unit:j.unit,large:true,label:'OLS trend slope per decade when each annual observation is omitted'});
    const maxShift=Math.max(0.0001,...s.months.map(m=>Math.abs(m.difference)));
    $('forensics-seasonal').innerHTML=s.months.map(m=>{
      const height=Math.max(2,Math.abs(m.difference)/maxShift*49);
      const above=m.difference>=0;
      const top=above?`calc(50% - ${height}%)`:'50%';
      return `<div class="shift-month" title="${escapeHtml(m.label)}: ${signed(m.difference)} ${escapeHtml(s.unit)}"><div class="month-label">${escapeHtml(m.label)}</div><div class="shift-indicator"><span class="${above?'':'down'}" style="top:${top};height:${height}%"></span></div><strong>${signed(m.difference)}</strong><small>${escapeHtml(s.unit)}</small></div>`;
    }).join('');
    asText('forensics-seasonal-note',`${s.note} · ${s.unit}. Blue-green = later period higher, peach = lower. ${c.omitted_middle_year?'Middle year '+c.omitted_middle_year+' excluded from balanced comparison.':''}`);
    const fields=[['NASA source',data.evidence.provider],['Data fingerprint','SHA-256 '+data.evidence.sha256_monthly],['Analysis method','OLS trend sensitivity + balanced-era contrast + trailing rolling mean'],['Most influential omitted year',`${j.most_influential_omitted_year.omitted_year} (trend ${signed(j.most_influential_omitted_year.slope_per_decade)} ${j.unit})`],['Source documentation',data.evidence.source_url],['Methodology version',data.evidence.forensics_version]];
    $('forensics-evidence').innerHTML=fields.map(([name,value])=>`<div><dt>${escapeHtml(name)}</dt><dd>${escapeHtml(value)}</dd></div>`).join('');
    $('forensics-limitations').innerHTML=data.limitations.map(message=>`<li>${escapeHtml(message)}</li>`).join('');
  }
  async function runForensics(event){
    event?.preventDefault();
    const chosen=state.locations.find(place=>place.name===$('forensics-location').value);
    if(!chosen)return toast('Select a valid geographic location.');
    const start=Number($('forensics-start').value),end=Number($('forensics-end').value),window=Number($('forensics-window').value);
    if(!Number.isInteger(start)||!Number.isInteger(end)||start<1981||end>new Date().getUTCFullYear()-1||end-start<7||end-start>44)return toast('Select 8–45 historical years.');
    if(!Number.isInteger(window)||window<3||window>15)return toast('Choose a supported rolling window.');
    $('forensics-empty').classList.add('hidden');$('forensics-results').classList.add('hidden');$('forensics-error').classList.add('hidden');$('forensics-loading').classList.remove('hidden');$('forensics-button').disabled=true;
    try{
      const query=buildQuery({lat:chosen.lat,lon:chosen.lon,start,end,variable:$('forensics-variable').value,window});
      const data=await api(`/api/v1/forensics?${query}`);
      state.forensicsResult=data;renderForensics(data,chosen.name);
      $('forensics-results').classList.remove('hidden');toast('Climate forensic diagnostics complete.');
    }catch(error){const node=$('forensics-error');node.classList.remove('hidden');node.textContent=error.message;}
    finally{$('forensics-loading').classList.add('hidden');$('forensics-button').disabled=false;}
  }
  function exportForensics(){
    if(!state.forensicsResult)return toast('Run forensics first.');
    const d=state.forensicsResult;
    download(`AETHERIS_forensics_${d.variable.id}_${d.period.observed_start}-${d.period.observed_end}.json`,JSON.stringify(d,null,2),'application/json');
  }

  // SPATIAL OBSERVATORY — nine independent point investigations, never an interpolated raster.
  function selectedSpatialPoint(p) {
    const d=state.spatialResult;if(!d)return;
    els('.spatial-cell').forEach(e=>e.classList.toggle('selected',e.dataset.point===p.id));
    const node=$('spatial-point-detail');
    if(p.status!=='ok'){
      node.innerHTML=`<div class="point-label">${escapeHtml(p.id.toUpperCase())} / SOURCE UNAVAILABLE</div><h3>No measurement</h3><p>${escapeHtml(p.error||'NASA source request failed.')}</p>`;
      return;
    }
    node.innerHTML=`<div class="point-label">${escapeHtml(p.id.toUpperCase())} / ${p.is_center?'CENTER SAMPLE':'NEIGHBOR SAMPLE'}</div>
      <h3>${escapeHtml(v(p.slope_per_decade,3))} <small>${escapeHtml(p.slope_unit)}</small></h3>
      <dl><div><dt>Latitude</dt><dd>${v(p.lat,4)}°</dd></div><div><dt>Longitude</dt><dd>${v(p.lon,4)}°</dd></div><div><dt>Complete years</dt><dd>${p.annual_years}</dd></div><div><dt>HAC p-value</dt><dd>${p.p_value_hac==null?'Not available':v(p.p_value_hac,5)}</dd></div><div><dt>BH-adjusted q</dt><dd>${p.adjusted_p_bh==null?'Not available':v(p.adjusted_p_bh,5)}</dd></div><div><dt>Data fingerprint</dt><dd class="point-hash" title="${escapeHtml(p.sha256_monthly)}">${escapeHtml(p.sha256_monthly.slice(0,20))}…</dd></div></dl>
      <p class="point-note">${p.exploratory_fdr_05?'Exploratory adjusted-p threshold crossed; this is not causal evidence.':'No exploratory FDR flag at 0.05, or unavailable test.'}</p>
      <button type="button" class="btn btn-primary full" id="spatial-open-point">Investigate this point ↗</button>`;
    $('spatial-open-point').addEventListener('click',()=>{
      const choice=state.locations.find(x=>Math.abs(x.lat-p.lat)<.0001&&Math.abs(x.lon-p.lon)<.0001);
      setLocation(p.lat,p.lon,choice?.name||`Spatial point ${p.id.toUpperCase()}`);
      $('start-year').value=d.period.start;$('end-year').value=d.period.end;$('variable-select').value=d.variable;
      go('explore');runAnalysis();
    });
  }
  function renderSpatial(d, place){
    const unit=d.summary.slope_unit;
    asText('spatial-result-title',`${place} · nine-point investigation`);
    asText('spatial-result-subtitle',`${d.period.start}–${d.period.end} · ${d.grid.spacing_km} km sample spacing · ${d.variable} · NASA POWER`);
    asText('spatial-valid',`${d.successful} / 9`);
    asText('spatial-median',`${d.summary.median_slope>0?'+':''}${v(d.summary.median_slope,3)}`);
    asText('spatial-median-unit',unit);
    asText('spatial-spread',`${v(d.summary.slope_spread,3)}`);
    asText('spatial-fdr',String(d.summary.exploratory_fdr_flags));
    const valid=d.points.filter(p=>p.status==='ok'), min=Math.min(...valid.map(p=>p.slope_per_decade)), max=Math.max(...valid.map(p=>p.slope_per_decade));
    const matrix=$('spatial-matrix'); matrix.innerHTML='';
    for(const p of d.points){
      const cell=document.createElement('button');cell.type='button';cell.className='spatial-cell'+(p.status!=='ok'?' failed':'')+(p.is_center?' center':'');cell.dataset.point=p.id;
      const norm=p.status==='ok'?Math.max(0,Math.min(1,(p.slope_per_decade-min)/(max-min||1))):0;
      const hue=(202 - 163*norm).toFixed(0);
      if(p.status==='ok')cell.style.setProperty('--cell-tint',`hsla(${hue},70%,48%,.25)`);
      cell.innerHTML=`<span class="cell-index">${escapeHtml(p.id.toUpperCase())} ${p.is_center?'· CENTER':''}</span><strong>${p.status==='ok'?`${p.slope_per_decade>0?'+':''}${v(p.slope_per_decade,2)}`:'UNAVAILABLE'}</strong><span class="cell-unit">${p.status==='ok'?escapeHtml(unit):'SOURCE FAILED'}</span><span class="cell-coord">${v(p.lat,2)}°, ${v(p.lon,2)}°</span>`;
      cell.setAttribute('aria-label',`Point ${p.id}: ${p.status==='ok'?v(p.slope_per_decade,3)+' '+unit:'unavailable'}; select for details`);
      cell.addEventListener('click',()=>selectedSpatialPoint(p));matrix.appendChild(cell);
    }
    $('spatial-limitations').innerHTML=d.limitations.map(x=>`<li>${escapeHtml(x)}</li>`).join('');
    selectedSpatialPoint(d.points.find(p=>p.is_center&&p.status==='ok')||valid[0]);
  }
  async function runSpatial(event){
    event?.preventDefault();
    const place=state.locations.find(p=>p.name===$('spatial-location').value) || {name:'Custom geographic point',lat:Number($('spatial-lat').value),lon:Number($('spatial-lon').value)};
    if(!$('spatial-lat').value.trim()||!$('spatial-lon').value.trim()||!Number.isFinite(place.lat)||Math.abs(place.lat)>75||!Number.isFinite(place.lon)||Math.abs(place.lon)>180){toast('Spatial Observatory accepts latitude -75° to 75° and longitude -180° to 180°.');return;}
    const start=Number($('spatial-start').value),end=Number($('spatial-end').value);
    if(!Number.isInteger(start)||!Number.isInteger(end)||start<1981||end>new Date().getUTCFullYear()-1||end-start<7||end-start>44){toast('Choose 8–45 valid complete historical years.');return;}
    const button=$('spatial-run');button.disabled=true;button.textContent='Retrieving NASA points…';
    $('spatial-empty').classList.add('hidden');$('spatial-results').classList.add('hidden');$('spatial-error').classList.add('hidden');$('spatial-loading').classList.remove('hidden');
    try{
      const query=buildQuery({lat:place.lat,lon:place.lon,start,end,variable:$('spatial-variable').value,spacing_km:Number($('spatial-spacing').value)});
      const d=await api(`/api/v1/spatial?${query}`);
      state.spatialResult=d;renderSpatial(d,place.name);
      $('spatial-results').classList.remove('hidden');
      if(d.failed)toast(`${d.successful}/9 points succeeded. Source failures are marked.`);else toast('Spatial NASA analysis completed.');
    }catch(err){const el=$('spatial-error');el.textContent=err.message;el.classList.remove('hidden');}
    finally{$('spatial-loading').classList.add('hidden');button.disabled=false;button.textContent='Run spatial field scan ↗';}
  }
  function exportSpatialJson(){if(!state.spatialResult)return toast('Run a spatial investigation first.');download('AETHERIS_spatial_evidence.json',JSON.stringify(state.spatialResult,null,2),'application/json');}
  function exportSpatialCsv(){
    const d=state.spatialResult;if(!d)return toast('Run a spatial investigation first.');
    const rows=['point,row,column,latitude,longitude,status,slope_per_decade,slope_unit,p_value_hac,bh_adjusted_p,complete_years,source_fingerprint'];
    for(const p of d.points)rows.push([p.id,p.row,p.column,p.lat,p.lon,p.status,p.slope_per_decade??'',p.slope_unit??'',p.p_value_hac??'',p.adjusted_p_bh??'',p.annual_years??'',p.sha256_monthly??''].join(','));
    download('AETHERIS_spatial_points.csv',rows.join('\n'),'text/csv;charset=utf-8');
  }

  // AETHERIS V5: paired-source Earth Systems Lab. All rendered numbers come
  // from the backend's validated NASA-source result, never from placeholders.
  function setupSystemsLocations(){
    const select=$('systems-location');
    select.innerHTML=state.locations.map(p=>`<option value="${escapeHtml(p.name)}">${escapeHtml(p.name)}, ${escapeHtml(p.country)}</option>`).join('')+'<option value="custom">Custom coordinates</option>';
    select.value='Beni Mellal';
    select.addEventListener('change',()=>{
      const p=state.locations.find(x=>x.name===select.value);
      if(p){$('systems-lat').value=p.lat;$('systems-lon').value=p.lon;}
    });
    for(const id of ['systems-lat','systems-lon'])$(id).addEventListener('change',()=>{select.value='custom';});
  }
  function systemsKpis(data){
    const t=data.metrics.temperature, p=data.metrics.precipitation;
    const items=[
      ['TEMPERATURE TREND', `${t.trend_per_decade>=0?'+':''}${v(t.trend_per_decade,3)}`, '°C per decade · exploratory OLS/HAC'],
      ['PRECIPITATION TREND', `${p.trend_per_decade>=0?'+':''}${v(p.trend_per_decade,1)}`, 'mm per decade · exploratory OLS/HAC'],
      ['SHARED COMPLETE YEARS', String(data.period.shared_complete_years), 'Years with both NASA products'],
      ['CO-OCCURRING DEVIATIONS', String(data.joint_deviations.count), 'Screened years · NOT a drought index'],
    ];
    $('systems-kpis').innerHTML=items.map(([label,value,note])=>`<div class="systems-kpi"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong><small>${escapeHtml(note)}</small></div>`).join('');
  }
  function renderSystemsScatter(d){
    const host=$('systems-scatter');host.innerHTML='';
    const points=d.years.filter(row=>Number.isFinite(row.temperature_departure_c)&&Number.isFinite(row.precipitation_departure_mm));
    if(!points.length){host.textContent='No aligned annual observations available.';return;}
    const W=650,H=310,pad={l:65,r:20,t:15,b:50};
    const xs=points.map(p=>p.temperature_departure_c),ys=points.map(p=>p.precipitation_departure_mm);
    const xr=Math.max(.5,...xs.map(x=>Math.abs(x)))*1.18;
    const yr=Math.max(20,...ys.map(x=>Math.abs(x)))*1.18;
    const X=x=>pad.l+(x+xr)/(2*xr)*(W-pad.l-pad.r);
    const Y=y=>H-pad.b-(y+yr)/(2*yr)*(H-pad.t-pad.b);
    const svg=xy('svg',{viewBox:`0 0 ${W} ${H}`,role:'img','aria-label':'Scatter plot of annual temperature departures against precipitation departures. Select a year for details.'});
    for(let i=-2;i<=2;i++){
      const x=i*xr/2,y=i*yr/2;
      svg.appendChild(xy('line',{x1:X(x),x2:X(x),y1:pad.t,y2:H-pad.b,class:'gridline'}));
      svg.appendChild(xy('line',{x1:pad.l,x2:W-pad.r,y1:Y(y),y2:Y(y),class:'gridline'}));
      svg.appendChild(xy('text',{x:X(x),y:H-pad.b+22,'text-anchor':'middle',class:'axis-tick'},x.toFixed(1)));
      svg.appendChild(xy('text',{x:pad.l-8,y:Y(y)+4,'text-anchor':'end',class:'axis-tick'},y.toFixed(0)));
    }
    svg.appendChild(xy('line',{x1:X(0),x2:X(0),y1:pad.t,y2:H-pad.b,stroke:'#9fadb077','stroke-width':1.5}));
    svg.appendChild(xy('line',{x1:pad.l,x2:W-pad.r,y1:Y(0),y2:Y(0),stroke:'#9fadb077','stroke-width':1.5}));
    svg.appendChild(xy('text',{x:W/2,y:H-7,'text-anchor':'middle',class:'axis-label'},'Temperature departure from internal baseline (°C)'));
    const ylab=xy('text',{x:16,y:H/2,transform:`rotate(-90 16 ${H/2})`,'text-anchor':'middle',class:'axis-label'},'Precipitation departure (mm)');svg.appendChild(ylab);
    for(const point of points){
      const c=xy('circle',{cx:X(point.temperature_departure_c),cy:Y(point.precipitation_departure_mm),r:point.joint_hot_dry_deviation?7:5.5,
        fill:point.joint_hot_dry_deviation?'#e3b531':'#447db0',class:'point','data-systems-year':point.year,tabindex:'0',role:'button','aria-label':`Inspect year ${point.year}`});
      c.appendChild(xy('title',{},`${point.year}: ${v(point.temperature_departure_c)} °C / ${v(point.precipitation_departure_mm)} mm departure`));
      c.addEventListener('click',()=>selectSystemsYear(point.year));
      c.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();selectSystemsYear(point.year);}});
      svg.appendChild(c);
    }
    host.appendChild(svg);
  }
  function selectSystemsYear(year){
    const d=state.systemsResult;if(!d)return;
    const item=d.years.find(p=>p.year===year);if(!item)return;
    els('.systems-year-item').forEach(button=>{const active=Number(button.dataset.year)===year;button.classList.toggle('selected',active);button.setAttribute('aria-pressed',String(active));});
    els('[data-systems-year]').forEach(circle=>circle.classList.toggle('selected',Number(circle.getAttribute('data-systems-year'))===year));
    const zfmt=z=>z==null?'Unavailable':`${z>=0?'+':''}${v(z,2)} SD`;
    $('systems-year-detail').innerHTML=`<strong>${item.year} · Paired NASA observations</strong><div class="detail-row"><div>Temperature<br><b>${v(item.temperature_c,2)} °C</b><br><small>Departure ${item.temperature_departure_c>=0?'+':''}${v(item.temperature_departure_c)} °C · ${escapeHtml(zfmt(item.temperature_z))}</small></div><div>Precipitation<br><b>${v(item.precipitation_mm,1)} mm</b><br><small>Departure ${item.precipitation_departure_mm>=0?'+':''}${v(item.precipitation_departure_mm,1)} mm · ${escapeHtml(zfmt(item.precipitation_z))}</small></div></div><small>${item.joint_hot_dry_deviation?'<em>Exploratory co-occurrence marker met (not a drought diagnosis).</em>':'No joint threshold flag under this internal baseline.'}</small>`;
  }
  function renderSystems(d,place){
    asText('systems-result-title',`${place} · temperature & rainfall`);
    asText('systems-result-subtitle',`${d.period.paired_years[0]}–${d.period.paired_years[1]} · ${d.period.shared_complete_years} aligned calendar years · NASA POWER`);
    systemsKpis(d);
    renderLineChart('systems-temp-chart',[{points:d.years.map(p=>({year:p.year,value:p.temperature_c}))}],{unit:'°C',large:true,label:'Annual observed temperature from NASA POWER'});
    renderLineChart('systems-rain-chart',[{points:d.years.map(p=>({year:p.year,value:p.precipitation_mm}))}],{unit:'mm',large:true,label:'Annual estimated precipitation totals from NASA POWER'});
    renderSystemsScatter(d);
    $('systems-year-list').innerHTML=d.years.map(row=>`<button type="button" data-year="${row.year}" class="systems-year-item${row.joint_hot_dry_deviation?' joint':''}" aria-pressed="false">${row.year}</button>`).join('');
    els('.systems-year-item').forEach(btn=>btn.addEventListener('click',()=>selectSystemsYear(Number(btn.dataset.year))));
    selectSystemsYear(d.years[d.years.length-1].year);
    const details=[
      ['NASA product','POWER monthly point · MERRA-2 gridded/reanalysis'],
      ['Source 1: temperature',d.evidence.temperature.source_request||d.evidence.temperature.source_url],
      ['Source 2: precipitation',d.evidence.precipitation.source_request||d.evidence.precipitation.source_url],
      ['Joint data fingerprint',`SHA-256 ${d.evidence.paired_sha256}`],
      ['Baseline',`${d.baseline.first_year}–${d.baseline.last_year} · ${d.baseline.sample_size} shared years; internal only`],
      ['Raw association',d.association.raw_pearson_r==null?'Unavailable':`${v(d.association.raw_pearson_r,3)} Pearson r (descriptive)`],
      ['Detrended association',d.association.detrended_pearson_r==null?'Unavailable':`${v(d.association.detrended_pearson_r,3)} Pearson r (descriptive)`],
      ['Early / late mean shift',`${v(d.era_comparison.temperature_change_c,2)} °C · ${v(d.era_comparison.precipitation_change_mm,1)} mm`],
    ];
    $('systems-evidence').innerHTML=details.map(([label,value])=>`<div><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value)}</dd></div>`).join('');
    $('systems-limitations').innerHTML=d.limitations.map(x=>`<li>${escapeHtml(x)}</li>`).join('');
  }
  async function runSystems(event){
    event?.preventDefault();
    const latInput=$('systems-lat').value.trim(),lonInput=$('systems-lon').value.trim();
    const lat=Number(latInput),lon=Number(lonInput),start=Number($('systems-start').value),end=Number($('systems-end').value);
    if(!latInput||!lonInput||!Number.isFinite(lat)||!Number.isFinite(lon)||Math.abs(lat)>90||Math.abs(lon)>180){toast('Enter valid geographic coordinates.');return;}
    if(!Number.isInteger(start)||!Number.isInteger(end)||start<1981||end>new Date().getUTCFullYear()-1||end-start<7||end-start>44){toast('Choose 8–45 complete historical years.');return;}
    const name=state.locations.find(x=>Math.abs(x.lat-lat)<.0001&&Math.abs(x.lon-lon)<.0001)?.name||'Custom geographic point';
    $('systems-empty').classList.add('hidden');$('systems-results').classList.add('hidden');$('systems-error').classList.add('hidden');$('systems-loading').classList.remove('hidden');
    const button=$('systems-run');button.disabled=true;button.textContent='Examining NASA climate records…';
    try{
      const d=await api(`/api/v1/systems?${buildQuery({lat,lon,start,end})}`);
      state.systemsResult=d;renderSystems(d,name);$('systems-results').classList.remove('hidden');toast('Coupled source investigation completed.');
    }catch(err){const box=$('systems-error');box.textContent=err.message;box.classList.remove('hidden');}
    finally{$('systems-loading').classList.add('hidden');button.disabled=false;button.textContent='Investigate both signals ↗';}
  }
  function exportSystemsJson(){if(!state.systemsResult)return toast('Run a coupled investigation first.');download('AETHERIS_earth_systems_evidence.json',JSON.stringify(state.systemsResult,null,2),'application/json');}
  function exportSystemsCsv(){
    const d=state.systemsResult;if(!d)return toast('Run a coupled investigation first.');
    const cols=['year','temperature_c','precipitation_mm','temperature_departure_c','precipitation_departure_mm','temperature_z','precipitation_z','joint_hot_dry_deviation'];
    const rows=[cols.join(','),...d.years.map(y=>cols.map(k=>y[k]??'').join(','))];
    download('AETHERIS_earth_systems_annual.csv',rows.join('\n'),'text/csv;charset=utf-8');
  }


  function showSignalsFromCurrent(){
    const d=state.currentResult;
    if(!d)return toast('Run an investigation before opening its seasonal signals.');
    $('signals-start').value=d.period.requested_start;
    $('signals-end').value=d.period.requested_end;
    $('signals-variable').value=d.variable.id;
    $('signals-lat').value=d.location.latitude;
    $('signals-lon').value=d.location.longitude;
    const preset=state.locations.find(p=>Math.abs(p.lat-d.location.latitude)<.001&&Math.abs(p.lon-d.location.longitude)<.001);
    $('signals-location').value=preset?.name||'custom';
    go('signals');
  }

  // v6 Seasonal Signal Laboratory: all numbers and chart points come directly
  // from source-derived backend results (no synthetic client-side observations).
  function setupSignalLocations(){
    const el=$('signals-location');
    el.innerHTML=state.locations.map(p=>`<option value="${escapeHtml(p.name)}">${escapeHtml(p.name)}, ${escapeHtml(p.country)}</option>`).join('')+'<option value="custom">Custom coordinates</option>';
    el.value='Beni Mellal';
    el.addEventListener('change',()=>{
      const p=state.locations.find(x=>x.name===el.value);
      if(p){$('signals-lat').value=p.lat;$('signals-lon').value=p.lon;}
    });
    for(const key of ['signals-lat','signals-lon'])$(key).addEventListener('change',()=>{el.value='custom';});
  }
  function signalNumber(value,digits=3){return value==null?'Unavailable':`${Number(value)>=0?'+':''}${v(value,digits)}`;}
  function renderSignalLab(data,place){
    asText('signals-result-title',`${place} · monthly climate fingerprint`);
    asText('signals-result-subtitle',`${data.period.requested_start}–${data.period.requested_end} · ${data.period.complete_years} complete years · ${data.variable.id} · NASA POWER`);
    const flagged=data.summary.fdr_flagged_months;
    const month=data.months.find(m=>m.month===data.summary.strongest_absolute_slope_month);
    const kpis=[
      ['ANALYZED MONTHS','12','Independent calendar-month trajectories'],
      ['COMPLETE YEARS',String(data.period.complete_years),'Incomplete years excluded and displayed'],
      ['EXPLORATORY FDR FLAGS',String(flagged),'BH-adjusted q < 0.05 (not attribution)'],
      ['STRONGEST ABSOLUTE SLOPE',month?month.name:'—',month?`${signalNumber(month.slope_per_decade)} ${month.trend_unit}`:'Not available'],
    ];
    $('signals-kpis').innerHTML=kpis.map(([a,b,c])=>`<div class="systems-kpi"><span>${escapeHtml(a)}</span><strong>${escapeHtml(b)}</strong><small>${escapeHtml(c)}</small></div>`).join('');
    const largest=Math.max(.001,...data.months.map(m=>Math.abs(m.slope_per_decade||0)));
    $('signals-months').innerHTML=data.months.map(m=>{
      const mag=Math.max(1,Math.abs(m.slope_per_decade||0)/largest*100);
      const tone=m.slope_per_decade>0?'up':m.slope_per_decade<0?'down':'flat';
      return `<button type="button" class="signal-month" data-signal-month="${m.month}" aria-pressed="false"><span class="signal-month-name">${escapeHtml(m.name)}</span><span class="signal-month-slope">${escapeHtml(signalNumber(m.slope_per_decade,2))}</span><span class="signal-month-bar"><i class="${tone}" style="width:${mag.toFixed(1)}%"></i></span><small>${m.q_value_bh==null?'q not available':`q=${v(m.q_value_bh,3)}`}</small></button>`;
    }).join('');
    els('[data-signal-month]').forEach(button=>button.addEventListener('click',()=>selectSignalMonth(Number(button.dataset.signalMonth))));
    const header='<span class="signal-matrix-corner">YEAR</span>'+data.months.map(m=>`<span class="signal-matrix-head">${escapeHtml(m.name)}</span>`).join('');
    const scale=Math.max(.00001,data.summary.maximum_absolute_departure||0);
    const rows=data.matrix.map(row=>`<span class="signal-matrix-year">${row.year}</span>`+row.months.map(cell=>{
      const miss=cell.departure==null;
      const factor=miss?0:Math.min(1,Math.abs(cell.departure)/scale);
      const color=miss?'':cell.departure>0?`rgba(255,187,115,${(.12+.8*factor).toFixed(3)})`:`rgba(74,171,222,${(.12+.8*factor).toFixed(3)})`;
      const label=miss?`${row.year} ${data.months[cell.month-1].name}: year excluded or unavailable`:`${row.year} ${data.months[cell.month-1].name}: ${v(cell.value,3)} ${data.months[cell.month-1].unit}, departure ${signalNumber(cell.departure,3)}`;
      return `<button type="button" class="signal-heat-cell${miss?' unavailable':''}" ${miss?'disabled':''} data-year="${row.year}" data-month="${cell.month}" style="${miss?'':`background:${color}`} " aria-label="${escapeHtml(label)}" title="${escapeHtml(label)}"></button>`;
    }).join('')).join('');
    $('signals-matrix').innerHTML=header+rows;
    els('.signal-heat-cell:not(:disabled)').forEach(b=>b.addEventListener('click',()=>selectSignalCell(Number(b.dataset.year),Number(b.dataset.month))));
    const details=[
      ['NASA source',data.evidence.provider],
      ['POWER request',data.evidence.source_url||'Not available'],
      ['Monthly source SHA-256',data.evidence.source_sha256_monthly],
      ['Seasonal analysis SHA-256',data.evidence.seasonal_analysis_sha256],
      ['Baseline',`${data.baseline.start_year}–${data.baseline.end_year} · internal only`],
      ['Aggregation',data.evidence.aggregation],
      ['Method',data.evidence.method],
      ['Excluded years',data.period.excluded_years.length?data.period.excluded_years.join(', '):'None'],
    ];
    $('signals-evidence').innerHTML=details.map(([a,b])=>`<div><dt>${escapeHtml(a)}</dt><dd>${escapeHtml(b)}</dd></div>`).join('');
    $('signals-limitations').innerHTML=data.limitations.map(x=>`<li>${escapeHtml(x)}</li>`).join('');
    selectSignalMonth(data.summary.strongest_absolute_slope_month||1);
  }
  function selectSignalMonth(monthNumber){
    const data=state.signalsResult;if(!data)return;
    const m=data.months.find(x=>x.month===monthNumber);if(!m)return;
    els('[data-signal-month]').forEach(btn=>{const active=Number(btn.dataset.signalMonth)===monthNumber;btn.classList.toggle('active',active);btn.setAttribute('aria-pressed',String(active));});
    asText('signals-selected-name',`${m.name} · observed monthly signal`);
    asText('signals-selected-unit',m.unit);
    const points=data.matrix.filter(y=>y.complete).map(y=>({year:y.year,value:y.months[monthNumber-1].value}));
    renderLineChart('signals-month-chart',[{points}],{label:`Observed ${m.name} ${data.variable.id} time series; measured NASA product, no forecast`,large:true,unit:m.unit});
    asText('signals-selected-note',`Every point is the observed ${m.name} value for one complete calendar year. The selection baseline is ${data.baseline.start_year}–${data.baseline.end_year}, internal only.`);
    const details=[
      ['OLS/HAC estimate',`${signalNumber(m.slope_per_decade,4)} ${m.trend_unit}`],
      ['Theil–Sen estimate',`${signalNumber(m.theil_sen_per_decade,4)} ${m.trend_unit}`],
      ['Raw exploratory p',m.p_value_hac==null?'Not available':v(m.p_value_hac,5)],
      ['BH-adjusted q',m.q_value_bh==null?'Not available':v(m.q_value_bh,5)],
      ['FDR flag',m.fdr_flag_exploratory?'Exploratory flag — review assumptions':'No exploratory flag'],
      ['Complete-year observations',String(m.sample_size)],
      ['Internal baseline mean',`${v(m.baseline_mean,3)} ${m.unit}`],
      ['Series status',m.status],
    ];
    $('signals-selected-details').innerHTML=details.map(([a,b])=>`<div><span>${escapeHtml(a)}</span><strong>${escapeHtml(b)}</strong></div>`).join('');
  }
  function selectSignalCell(year,month){
    const d=state.signalsResult;if(!d)return;
    const row=d.matrix.find(x=>x.year===year);
    const cell=row?.months[month-1];if(!cell||cell.value==null)return;
    const unit=d.months[month-1].unit;
    asText('signals-cell-detail',`${year} ${d.months[month-1].name} · NASA value ${v(cell.value,3)} ${unit} · departure from internal baseline ${signalNumber(cell.departure,3)} ${unit}`);
    selectSignalMonth(month);
    els('.signal-heat-cell.selected').forEach(e=>e.classList.remove('selected'));
    const picked=els('.signal-heat-cell').find(x=>Number(x.dataset.year)===year&&Number(x.dataset.month)===month);
    if(picked)picked.classList.add('selected');
  }
  async function runSignalLab(event){
    event?.preventDefault();
    const latText=$('signals-lat').value.trim(),lonText=$('signals-lon').value.trim();
    const lat=Number(latText),lon=Number(lonText),start=Number($('signals-start').value),end=Number($('signals-end').value);
    if(!latText||!lonText||!Number.isFinite(lat)||!Number.isFinite(lon)||Math.abs(lat)>90||Math.abs(lon)>180){toast('Enter valid geographic coordinates.');return;}
    if(!Number.isInteger(start)||!Number.isInteger(end)||start<1981||end>new Date().getUTCFullYear()-1||end-start<7||end-start>44){toast('Choose 8–45 complete historical years.');return;}
    const place=state.locations.find(p=>Math.abs(p.lat-lat)<.0001&&Math.abs(p.lon-lon)<.0001)?.name||'Custom geographic point';
    $('signals-empty').classList.add('hidden');$('signals-results').classList.add('hidden');$('signals-error').classList.add('hidden');$('signals-loading').classList.remove('hidden');
    const button=$('signals-run');button.disabled=true;button.textContent='Analyzing monthly NASA signals…';
    try{
      const data=await api(`/api/v1/seasonal-signals?${buildQuery({lat,lon,start,end,variable:$('signals-variable').value})}`);
      state.signalsResult=data;renderSignalLab(data,place);$('signals-results').classList.remove('hidden');toast('Twelve monthly investigations completed.');
    }catch(err){$('signals-error').textContent=err.message;$('signals-error').classList.remove('hidden');}
    finally{$('signals-loading').classList.add('hidden');button.disabled=false;button.textContent='Analyze 12 months ↗';}
  }
  function exportSignalsJson(){if(!state.signalsResult)return toast('Run Seasonal Signal Lab first.');download('AETHERIS_seasonal_signals_evidence.json',JSON.stringify(state.signalsResult,null,2),'application/json');}
  function exportSignalsCsv(){
    const d=state.signalsResult;if(!d)return toast('Run Seasonal Signal Lab first.');
    const head=['month','unit','sample_size','ols_hac_slope_per_decade','theil_sen_slope_per_decade','p_value_hac','q_value_bh','fdr_exploratory_flag','baseline_mean'];
    const rows=[head.join(','),...d.months.map(m=>[m.name,m.unit,m.sample_size,m.slope_per_decade??'',m.theil_sen_per_decade??'',m.p_value_hac??'',m.q_value_bh??'',m.fdr_flag_exploratory,m.baseline_mean].join(','))];
    download('AETHERIS_monthly_trends.csv',rows.join('\n'),'text/csv;charset=utf-8');
  }

  // AETHERIS V7: exploratory model comparisons computed only from audited NASA annual values.
  function setupBreakpointLocations(){
    const select=$('breakpoint-location');
    select.innerHTML=state.locations.map(p=>`<option value="${escapeHtml(p.name)}">${escapeHtml(p.name)}, ${escapeHtml(p.country)}</option>`).join('')+'<option value="custom">Custom coordinates</option>';
    select.value='Beni Mellal';
    select.addEventListener('change',()=>{const p=state.locations.find(x=>x.name===select.value);if(p){$('breakpoint-lat').value=p.lat;$('breakpoint-lon').value=p.lon;}});
    for(const id of ['breakpoint-lat','breakpoint-lon'])$(id).addEventListener('change',()=>{select.value='custom';});
  }
  function breakpointSign(value, digits=3){return value==null?'—':`${value>0?'+':''}${v(value,digits)}`;}
  function inspectBreakpointCandidate(candidate){
    els('.breakpoint-candidate').forEach(b=>{
      const chosen=Number(b.dataset.year)===candidate.year;
      b.classList.toggle('active',chosen);b.setAttribute('aria-pressed',String(chosen));
    });
    const unit=state.breakpointResult?.variable?.annual_unit==='mm'?'mm/decade':'°C/decade';
    $('breakpoint-candidate-detail').innerHTML=`<strong>${candidate.year} · candidate transition</strong>
      <p>${candidate.left_years} years before or at the knot, ${candidate.right_years} years after.</p>
      <div><span>Before</span><b>${breakpointSign(candidate.slope_before_per_decade)} ${unit}</b></div>
      <div><span>After</span><b>${breakpointSign(candidate.slope_after_per_decade)} ${unit}</b></div>
      <div><span>ΔBIC vs one slope</span><b>${breakpointSign(candidate.delta_bic_vs_linear,2)}</b></div>
      <small>Candidate selected after examining this dataset; descriptive model comparison only.</small>`;
  }
  function renderBreakpointLab(d, place){
    const b=d.best_candidate, r=d.robustness, unit=d.variable.annual_unit==='mm'?'mm/decade':'°C/decade';
    asText('breakpoint-result-title',`${place} · ${d.variable.label||d.variable.id}`);
    asText('breakpoint-result-period',`${d.period.observed_start}–${d.period.observed_end} · ${d.quality.complete_years} complete annual observations · NASA POWER`);
    const assessment=d.assessment.label==='piecewise_preferred_exploratory'?'Piecewise favored':
      d.assessment.label==='weak_piecewise_preference'?'Weak preference':
      d.assessment.label==='no_detectable_variation'?'No detectable variation':'Linear model adequate';
    const metrics=[
      ['CANDIDATE TRANSITION',String(b.year),'Selected from available observed years'],
      ['BEFORE / AFTER SLOPE',`${breakpointSign(b.slope_before_per_decade,2)} / ${breakpointSign(b.slope_after_per_decade,2)}`,unit],
      ['MODEL COMPARISON',breakpointSign(b.delta_bic_vs_linear,2),'ΔBIC · exploratory, not p-value'],
      ['LEAVE-ONE-YEAR-OUT',r.within_two_years_fraction==null?'Not available':`${v(r.within_two_years_fraction*100,0)}%`,'Candidate within ±2 years across reruns'],
    ];
    $('breakpoint-summary').innerHTML=metrics.map(([label,val,note])=>`<div class="breakpoint-metric"><span>${escapeHtml(label)}</span><strong>${escapeHtml(val)}</strong><small>${escapeHtml(note)}</small></div>`).join('');
    const existing=$('breakpoint-verdict');if(existing)existing.remove();
    const verdict=document.createElement('div');verdict.id='breakpoint-verdict';verdict.className='breakpoint-verdict';
    verdict.innerHTML=`<strong>${escapeHtml(assessment)}</strong><span>${escapeHtml(d.assessment.meaning)}</span><small>Formal change-point significance: NOT ASSESSED</small>`;
    $('breakpoint-summary').after(verdict);
    renderLineChart('breakpoint-main-chart',[
      {points:d.annual_observations},
      {points:d.linear.fitted,className:'chart-fit'},
      {points:b.fitted,className:'breakpoint-fit'}],
      {large:true,unit:d.variable.annual_unit,label:'Annual NASA POWER observations with single trend and selected continuous piecewise model'});
    const ranked=[...d.candidate_scores].sort((a,b)=>b.delta_bic_vs_linear-a.delta_bic_vs_linear).slice(0,10);
    const vals=ranked.map(x=>x.delta_bic_vs_linear);const low=Math.min(0,...vals), high=Math.max(0,...vals);const span=Math.max(1e-8,high-low);
    $('breakpoint-candidates').innerHTML=ranked.map((item,index)=>{
      const positive=item.delta_bic_vs_linear>=0;
      const strength=Math.max(4,Math.round(Math.abs(item.delta_bic_vs_linear)/span*100));
      return `<button class="breakpoint-candidate" type="button" data-year="${item.year}" aria-pressed="false"><span class="candidate-rank">${String(index+1).padStart(2,'0')}</span><span class="candidate-year">${item.year}</span><span class="candidate-bar"><i style="width:${strength}%;background:${positive?'#d5a314':'#477dae'}"></i></span><strong>${breakpointSign(item.delta_bic_vs_linear,2)}</strong></button>`;
    }).join('');
    els('.breakpoint-candidate').forEach(btn=>btn.addEventListener('click',()=>{
      const pick=d.candidate_scores.find(x=>x.year===Number(btn.dataset.year));if(pick)inspectBreakpointCandidate(pick);
    }));
    inspectBreakpointCandidate(d.candidate_scores.find(x=>x.year===b.year)||ranked[0]);
    const ev=[
      ['Provider',d.evidence.provider],['Source product',d.evidence.source_product],
      ['NASA source URL',d.evidence.source_url||'Not specified'],
      ['Monthly data SHA-256',d.evidence.source_sha256_monthly],
      ['Change-point analysis SHA-256',d.evidence.change_point_analysis_sha256],
      ['Annual aggregation',d.evidence.aggregation],
      ['Excluded incomplete years',(d.quality.incomplete_years_excluded||[]).join(', ')||'None'],
      ['Missing complete years',(d.quality.gaps_in_complete_years||[]).join(', ')||'None'],
      ['Method','Continuous OLS hinge model · BIC comparison · leave-one-year-out sensitivity'],
    ];
    $('breakpoint-evidence').innerHTML=ev.map(([k,val])=>`<div><dt>${escapeHtml(k)}</dt><dd>${escapeHtml(val)}</dd></div>`).join('');
    $('breakpoint-limitations').innerHTML=d.limitations.map(t=>`<li>${escapeHtml(t)}</li>`).join('');
  }
  function showBreakpointsFromCurrent(){
    const d=state.currentResult;if(!d)return toast('Run a NASA investigation first.');
    $('breakpoint-location').value='custom';$('breakpoint-lat').value=d.location.latitude;$('breakpoint-lon').value=d.location.longitude;
    $('breakpoint-variable').value=d.variable.id;$('breakpoint-start').value=d.period.requested_start;$('breakpoint-end').value=d.period.requested_end;
    go('breakpoints');
  }
  async function runBreakpointLab(event){
    event?.preventDefault();
    const latText=$('breakpoint-lat').value.trim(),lonText=$('breakpoint-lon').value.trim();
    const lat=Number(latText),lon=Number(lonText),start=Number($('breakpoint-start').value),end=Number($('breakpoint-end').value),min_segment_years=Number($('breakpoint-min').value);
    if(!latText||!lonText||!Number.isFinite(lat)||!Number.isFinite(lon)||Math.abs(lat)>90||Math.abs(lon)>180)return toast('Enter valid latitude and longitude.');
    if(!Number.isInteger(start)||!Number.isInteger(end)||start<1981||end>2025||end-start<13||end-start>44)return toast('Choose a period of 14–45 historical years ending by 2025.');
    const btn=$('breakpoint-run');btn.disabled=true;btn.textContent='Evaluating trend shifts…';
    $('breakpoint-empty').classList.add('hidden');$('breakpoint-results').classList.add('hidden');$('breakpoint-error').classList.add('hidden');$('breakpoint-loading').classList.remove('hidden');
    try{
      const args={lat,lon,start,end,variable:$('breakpoint-variable').value,min_segment_years};
      const result=await api(`/api/v1/change-points?${buildQuery(args)}`);
      state.breakpointResult=result;
      const place=state.locations.find(x=>Math.abs(x.lat-lat)<.0001&&Math.abs(x.lon-lon)<.0001)?.name||'Custom geographic point';
      renderBreakpointLab(result,place);$('breakpoint-results').classList.remove('hidden');toast('Exploratory change-point comparison complete.');
    }catch(error){$('breakpoint-error').textContent=error.message;$('breakpoint-error').classList.remove('hidden');}
    finally{$('breakpoint-loading').classList.add('hidden');btn.disabled=false;btn.textContent='Analyze possible trend shift ↗';}
  }
  function exportBreakpointJson(){if(!state.breakpointResult)return toast('Analyze a location first.');download('AETHERIS_change_point_evidence.json',JSON.stringify(state.breakpointResult,null,2),'application/json');}
  function exportBreakpointCsv(){
    const d=state.breakpointResult;if(!d)return toast('Analyze a location first.');
    const lines=['year,observed,linear_fit,piecewise_fit,unit'];
    for(let i=0;i<d.annual_observations.length;i++){
      lines.push([d.annual_observations[i].year,d.annual_observations[i].value,d.linear.fitted[i].value,d.best_candidate.fitted[i].value,d.variable.annual_unit].join(','));
    }
    download('AETHERIS_change_point_annual_fits.csv',lines.join('\n'),'text/csv;charset=utf-8');
  }

  // EARTH TIME MACHINE — annual anomalies at 9 actual NASA POWER point samples.
  // Playback changes an already loaded dataset; it does not trigger extra source downloads.
  function stopTimeMachinePlayback(){
    if(state.timeMachineTimer){clearInterval(state.timeMachineTimer);state.timeMachineTimer=null;}
    const btn=$('tm-play');if(btn){btn.textContent='▶ Play timeline';btn.setAttribute('aria-pressed','false');}
  }
  function timeMachineUnit(d){return d?.unit || '°C';}
  function tmSigned(value,digits=2){return value==null?'—':`${value>0?'+':''}${v(value,digits)}`;}
  function selectTimeMachinePoint(id){
    const d=state.timeMachineResult;if(!d)return;
    state.timeMachinePoint=id;
    const point=d.points.find(p=>p.id===id);if(!point)return;
    const year=Number($('tm-year-slider').value);
    const row=point.annual?.find(r=>r.year===year);
    els('.tm-cell').forEach(c=>{c.classList.toggle('selected',c.dataset.point===id);c.setAttribute('aria-pressed',String(c.dataset.point===id));});
    const box=$('tm-point-detail');
    if(point.status!=='ok'){
      box.innerHTML=`<div class="tm-point-tag">${escapeHtml(id.toUpperCase())} / NO SOURCE</div><h3>Point unavailable</h3><p>${escapeHtml(point.error||'The source failed or the baseline is incomplete.')}</p>`;
      $('tm-point-chart').textContent='No annual observations for this point.';return;
    }
    box.innerHTML=`<div class="tm-point-tag">${escapeHtml(id.toUpperCase())} ${point.is_center?'· CENTER SAMPLE':''}</div><h3>${row?.status==='ok'?tmSigned(row.anomaly,3)+' '+escapeHtml(timeMachineUnit(d)):'No valid value for '+year}</h3>
      <p>${year} annual ${escapeHtml(d.variable==='T2M'?'temperature':'precipitation')}: ${row?.status==='ok'?v(row.annual_value,3)+' '+escapeHtml(timeMachineUnit(d)):'missing complete year'}</p>
      <dl class="tm-data-list"><div><dt>Latitude / longitude</dt><dd>${v(point.lat,4)}°, ${v(point.lon,4)}°</dd></div><div><dt>Reference window</dt><dd>${point.baseline_start}–${point.baseline_end}</dd></div><div><dt>Reference baseline</dt><dd>${v(point.baseline,3)} ${escapeHtml(timeMachineUnit(d))}</dd></div><div><dt>Reference complete years</dt><dd>${point.baseline_complete_years} of ${point.baseline_expected_years}</dd></div><div><dt>Valid months</dt><dd>${point.evidence.valid_months}</dd></div><div><dt>Source</dt><dd>${escapeHtml(point.evidence.provider)} · gridded reanalysis</dd></div><div><dt>SHA-256 evidence</dt><dd class="tm-hash" title="${escapeHtml(point.evidence.sha256_monthly)}">${escapeHtml(point.evidence.sha256_monthly.slice(0,26))}…</dd></div></dl>
      <button type="button" class="btn btn-primary full" id="tm-open-investigation">Investigate point in Earth Explorer ↗</button>`;
    $('tm-open-investigation').addEventListener('click',()=>{
      setLocation(point.lat,point.lon,`Time Machine point ${id.toUpperCase()}`);
      $('start-year').value=d.period.start;$('end-year').value=d.period.end;$('variable-select').value=d.variable;
      go('explore');runAnalysis();
    });
    asText('tm-chart-title',`${id.toUpperCase()} · ${d.period.start}–${d.period.end} anomaly history`);
    renderLineChart('tm-point-chart',[{points:point.annual.filter(a=>a.status==='ok').map(a=>({year:a.year,value:a.anomaly}))}],
      {large:true,zero:true,unit:timeMachineUnit(d),label:`Complete annual ${d.variable} anomalies at ${id}, relative to ${point.baseline_start}–${point.baseline_end}`});
  }
  function showTimeMachineYear(year){
    const d=state.timeMachineResult;if(!d)return;
    const frame=d.snapshots.find(f=>f.year===Number(year));if(!frame)return;
    $('tm-year-slider').value=frame.year;
    asText('tm-year-number',String(frame.year));
    asText('tm-frame-label',`${frame.available_points}/9 samples · ${d.variable}`);
    asText('tm-stat-available',`${frame.available_points}/9`);
    asText('tm-stat-median',tmSigned(frame.median_point_anomaly,2));
    asText('tm-stat-positive',String(frame.positive_points));
    asText('tm-stat-center',tmSigned(frame.center_anomaly,2));
    const grid=$('tm-grid');grid.innerHTML='';
    for(const cell of frame.points){
      const point=d.points.find(p=>p.id===cell.id);
      const el=document.createElement('button');el.type='button';el.className=`tm-cell${cell.status!=='ok'?' missing':''}${point.is_center?' center':''}`;
      el.dataset.point=cell.id;el.setAttribute('aria-pressed',String(cell.id===state.timeMachinePoint));
      if(cell.status==='ok'){
        const norm=Math.min(1,Math.abs(cell.anomaly)/(d.color_scale_abs_max||1));
        const rgb=cell.anomaly<0?'65,156,222':'239,156,86';
        el.style.setProperty('--tm-tint',`rgba(${rgb},${(.11 + norm*.62).toFixed(3)})`);
      }
      el.innerHTML=`<small>${escapeHtml(cell.id.toUpperCase())}${point.is_center?' · CENTER':''}</small><strong>${cell.status==='ok'?escapeHtml(tmSigned(cell.anomaly,2)):'NO DATA'}</strong><span>${cell.status==='ok'?escapeHtml(timeMachineUnit(d)):'SOURCE MISSING'}</span>`;
      el.setAttribute('aria-label',`Point ${cell.id}: ${cell.status==='ok'?tmSigned(cell.anomaly,3)+' '+d.unit:'no complete annual observation'} in ${year}; show evidence`);
      el.addEventListener('click',()=>selectTimeMachinePoint(cell.id));
      grid.appendChild(el);
    }
    selectTimeMachinePoint(state.timeMachinePoint);
  }
  function renderTimeMachine(d,place){
    // Deterministic symmetric scale shared across all timeline frames; no yearly recoloring.
    const anomalies=d.snapshots.flatMap(f=>f.points.map(p=>p.anomaly)).filter(x=>Number.isFinite(x));
    d.color_scale_abs_max=Math.max(.000001,...anomalies.map(Math.abs));
    asText('tm-results-title',`${place} · ${d.period.start}–${d.period.end}`);
    asText('tm-results-subtitle',`${d.grid.spacing_km} km spacing · ${d.variable} · ${d.successful_points} valid sources · NASA POWER`);
    asText('tm-baseline-label',`REFERENCE: ${d.baseline.start}–${d.baseline.end}`);
    asText('tm-first-year',String(d.period.start));asText('tm-last-year',String(d.period.end));
    asText('tm-stat-unit',`${d.unit} vs local reference`);asText('tm-stat-center-unit',d.unit+' vs local reference');
    $('tm-year-slider').min=d.period.start;$('tm-year-slider').max=d.period.end;$('tm-year-slider').value=d.period.end;
    $('tm-limitations').innerHTML=d.limitations.map(x=>`<li>${escapeHtml(x)}</li>`).join('');
    state.timeMachinePoint=d.points.some(p=>p.id==='p4'&&p.status==='ok')?'p4':d.points.find(p=>p.status==='ok')?.id || 'p4';
    showTimeMachineYear(d.period.end);
  }
  async function runTimeMachine(event){
    event?.preventDefault();stopTimeMachinePlayback();
    const lt=$('tm-lat').value.trim(),ln=$('tm-lon').value.trim();
    const lat=Number(lt),lon=Number(ln),start=Number($('tm-start').value),end=Number($('tm-end').value);
    if(!lt||!ln||!Number.isFinite(lat)||!Number.isFinite(lon)||Math.abs(lat)>75||Math.abs(lon)>180)return toast('Enter geographic coordinates within ±75° latitude and ±180° longitude.');
    if(!Number.isInteger(start)||!Number.isInteger(end)||start<1981||end>new Date().getUTCFullYear()-1||end-start<11||end-start>44)return toast('Choose 12–45 complete historical years.');
    const button=$('tm-run');button.disabled=true;button.textContent='Retrieving nine NASA series…';
    $('tm-empty').classList.add('hidden');$('tm-results').classList.add('hidden');$('tm-error').classList.add('hidden');$('tm-loading').classList.remove('hidden');
    try{
      const d=await api(`/api/v1/time-machine?${buildQuery({lat,lon,start,end,variable:$('tm-variable').value,spacing_km:Number($('tm-spacing').value)})}`);
      state.timeMachineResult=d;
      const place=state.locations.find(p=>Math.abs(p.lat-lat)<.0001&&Math.abs(p.lon-lon)<.0001)?.name||'Custom point';
      renderTimeMachine(d,place);$('tm-results').classList.remove('hidden');
      if(d.failed_points)toast(`${d.successful_points}/9 points available. Missing samples are clearly marked.`);
      else toast('Time Machine ready. Scrub through historical NASA data.');
    }catch(error){$('tm-error').textContent=error.message;$('tm-error').classList.remove('hidden');}
    finally{$('tm-loading').classList.add('hidden');button.disabled=false;button.textContent='Build time machine ↗';}
  }
  function playTimeMachine(){
    const d=state.timeMachineResult;if(!d)return toast('Build an investigation first.');
    if(state.timeMachineTimer){stopTimeMachinePlayback();return;}
    let year=Number($('tm-year-slider').value);
    if(year>=d.period.end){year=d.period.start;showTimeMachineYear(year);}
    $('tm-play').textContent='Ⅱ Pause timeline';$('tm-play').setAttribute('aria-pressed','true');
    state.timeMachineTimer=setInterval(()=>{
      if(!state.timeMachineResult){stopTimeMachinePlayback();return;}
      const next=Number($('tm-year-slider').value)+1;
      if(next>d.period.end){stopTimeMachinePlayback();return;}
      showTimeMachineYear(next);
    },850);
  }
  function shiftTimeMachine(step){
    if(!state.timeMachineResult)return toast('Build an investigation first.');
    stopTimeMachinePlayback();
    const d=state.timeMachineResult;
    showTimeMachineYear(Math.min(d.period.end,Math.max(d.period.start,Number($('tm-year-slider').value)+step)));
  }
  function exportTimeMachineJson(){
    if(!state.timeMachineResult)return toast('Build an investigation first.');
    const d=state.timeMachineResult;
    // Derived display-only normalization is not a source result.
    const copy={...d};delete copy.color_scale_abs_max;
    download('AETHERIS_time_machine_evidence.json',JSON.stringify(copy,null,2),'application/json');
  }
  function exportTimeMachineCsv(){
    const d=state.timeMachineResult;if(!d)return toast('Build an investigation first.');
    const lines=['year,point_id,latitude,longitude,status,annual_value,anomaly,unit,baseline_start,baseline_end,baseline_value,source_sha256'];
    for(const frame of d.snapshots)for(const cell of frame.points){
      const point=d.points.find(p=>p.id===cell.id);
      lines.push([frame.year,cell.id,point.lat,point.lon,cell.status,cell.annual_value??'',cell.anomaly??'',d.unit,
                  point.baseline_start??'',point.baseline_end??'',point.baseline??'',point.evidence?.sha256_monthly||''].join(','));
    }
    download('AETHERIS_time_machine_annual_points.csv',lines.join('\n'),'text/csv;charset=utf-8');
  }
  function showTimeMachineFromCurrent(){
    const d=state.currentResult;if(!d)return toast('Run an Earth investigation first.');
    $('tm-location').value='custom';$('tm-lat').value=d.location.latitude;$('tm-lon').value=d.location.longitude;
    $('tm-start').value=d.period.requested_start;$('tm-end').value=d.period.requested_end;$('tm-variable').value=d.variable.id;
    go('timemachine');
  }

  async function init(){
    els('[data-view]').forEach(btn=>btn.addEventListener('click',()=>go(btn.dataset.view)));
    $('solar-quick-start')?.addEventListener('click',()=>{go('briefing');$('brief-form').requestSubmit();});
    $('mobile-menu-toggle').addEventListener('click',()=>{const open=$('sidebar').classList.toggle('menu-open');$('mobile-menu-toggle').setAttribute('aria-expanded',String(open));});
    els('[data-nav]').forEach(btn=>btn.addEventListener('click',()=>go(btn.dataset.nav)));
    const hash=location.hash.slice(1);if(['overview','briefing','explore','compare','discover','campaign','spatial','timemachine','systems','signals','breakpoints','forensics','notebook','science'].includes(hash))go(hash);
    $('investigate-form').addEventListener('submit',runAnalysis);$('retry-btn').addEventListener('click',runAnalysis);
    $('compare-form').addEventListener('submit',runComparison);
    $('export-csv').addEventListener('click',exportCSV);$('export-json').addEventListener('click',exportJSON);
    $('print-report').addEventListener('click',downloadPdf);
    $('save-investigation').addEventListener('click',saveInvestigation);
    $('refresh-notebook').addEventListener('click',renderNotebook);
    $('ai-analyze').addEventListener('click',runAI);
    $('discover-form').addEventListener('submit',runDiscovery);
    $('discover-download').addEventListener('click',exportDiscovery);
    $('forensics-form').addEventListener('submit',runForensics);
    $('spatial-form').addEventListener('submit',runSpatial);
    $('tm-form').addEventListener('submit',runTimeMachine);
    $('tm-year-slider').addEventListener('input',event=>{stopTimeMachinePlayback();showTimeMachineYear(Number(event.target.value));});
    $('tm-play').addEventListener('click',playTimeMachine);
    $('tm-previous').addEventListener('click',()=>shiftTimeMachine(-1));
    $('tm-next').addEventListener('click',()=>shiftTimeMachine(1));
    $('tm-export-json').addEventListener('click',exportTimeMachineJson);
    $('tm-export-csv').addEventListener('click',exportTimeMachineCsv);
    $('open-timemachine').addEventListener('click',showTimeMachineFromCurrent);
    $('open-briefing').addEventListener('click',()=>{if(!state.currentResult)return toast('Run an Earth investigation first.');go('briefing');window.AetherisBriefing?.openFromInvestigation(state.currentResult);});
    $('systems-form').addEventListener('submit',runSystems);
    $('signals-form').addEventListener('submit',runSignalLab);
    $('breakpoint-form').addEventListener('submit',runBreakpointLab);
    $('breakpoint-export-json').addEventListener('click',exportBreakpointJson);
    $('breakpoint-export-csv').addEventListener('click',exportBreakpointCsv);
    $('open-breakpoints').addEventListener('click',showBreakpointsFromCurrent);
    $('signals-export-json').addEventListener('click',exportSignalsJson);
    $('signals-export-csv').addEventListener('click',exportSignalsCsv);
    $('systems-export-json').addEventListener('click',exportSystemsJson);
    $('systems-export-csv').addEventListener('click',exportSystemsCsv);
    $('spatial-export-json').addEventListener('click',exportSpatialJson);
    $('spatial-export-csv').addEventListener('click',exportSpatialCsv);
    $('forensics-export').addEventListener('click',exportForensics);
    $('open-signals').addEventListener('click',showSignalsFromCurrent);
    $('open-forensics').addEventListener('click',showForensicsFromCurrent);
    $('open-spatial').addEventListener('click',()=>{const d=state.currentResult;if(!d)return toast('Run an investigation first.');$('spatial-location').value='custom';$('spatial-lat').value=d.location.latitude;$('spatial-lon').value=d.location.longitude;$('spatial-start').value=d.period.requested_start;$('spatial-end').value=d.period.requested_end;$('spatial-variable').value=d.variable.id;go('spatial');});
    $('reset-location').addEventListener('click',()=>setLocation(32.337,-6.349,'Beni Mellal'));
    $('place-select').addEventListener('change',event=>{if(event.target.value==='custom')return;const place=chosenPlace(event.target);if(place)setLocation(place.lat,place.lon,place.name);});
    for(const id of ['lat-input','lon-input'])$(id).addEventListener('change',()=>{const lat=Number($('lat-input').value),lon=Number($('lon-input').value);if(Number.isFinite(lat)&&Number.isFinite(lon)&&Math.abs(lat)<=90&&Math.abs(lon)<=180)setLocation(lat,lon);});
    try{const c=await api('/api/v1/catalog');state.locations=c.locations;setupLocations();setupDiscoverPlaces();setupSystemsLocations();setupSignalLocations();setupBreakpointLocations();}
    catch(err){toast('Preset catalog unavailable: '+err.message);}
    if(window.AetherisCampaign) window.AetherisCampaign.init({api,go,toast,locations:state.locations});
    if(window.AetherisBriefing){window.AetherisBriefing.init({go,api,toast,locations:state.locations});window.AetherisBriefing.restoreShared();}
    await loadMap();
    if(window.AetherisGlobe) window.AetherisGlobe.initialize();
    await checkAI();
  }
  init().catch(err=>toast('Initialization error: '+err.message));
})();
