/* AETHERIS Evidence Command Center — real source-backed deterministic results. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const fmt = (x, d=2) => x == null || !Number.isFinite(Number(x)) ? 'unavailable' : Number(x).toFixed(d);
  const signed = (x, d=2) => x == null || !Number.isFinite(Number(x)) ? 'unavailable' : `${Number(x)>0?'+':''}${fmt(x,d)}`;
  const clamp = (n,min,max) => Math.max(min,Math.min(max,n));
  const minmax = (v,min,max) => Number.isFinite(v) ? clamp(v,min,max) : 0;
  const attr = (value) => esc(value);
  let data = null;
  let lastQuery = null;
  let go = null;
  let api = null;
  let toast = null;
  let active = null;
  const row = (y) => data?.observations.find(p => p.year===Number(y));

  const friendlyP = p => p == null ? 'HAC p unavailable' : `HAC p = ${fmt(p,4)} · exploratory`;
  function show(status) {
    for(const key of ['empty','loading','error','results'])$('brief-'+key).classList.toggle('hidden',key!==status);
  }
  function form() {
    const lat = Number($('brief-lat').value), lon = Number($('brief-lon').value);
    const start = Number($('brief-start').value),end = Number($('brief-end').value);
    if(!$('brief-lat').value||!$('brief-lon').value||!Number.isFinite(lat)||!Number.isFinite(lon)||Math.abs(lat)>90||Math.abs(lon)>180)throw Error('Choose valid geographic coordinates.');
    if(!Number.isInteger(start)||!Number.isInteger(end)||start<1981||end>2025||end-start<7||end-start>44)throw Error('Choose 8–45 valid historical calendar years, through 2025.');
    return {lat,lon,start,end};
  }
  function selectedName() {
    const label=$('brief-location').selectedOptions[0]?.textContent || 'Selected point';
    return $('brief-location').value==='custom'?'Selected geographic point':label;
  }
  function download(filename,body,contentType){
    const blob=new Blob([body],{type:contentType});const url=URL.createObjectURL(blob);
    const a=document.createElement('a');a.href=url;a.download=filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),5000);
  }

  // Scientific constellation: a scatterplot of annual standardized paired data.
  // No extrapolation, regional interpolation or machine-learned predictions.
  let constellationYear=null;
  const validZ=r=>Number.isFinite(r.temperature_z)&&Number.isFinite(r.precipitation_z);
  const constellationMatch=(r,filter)=>filter==='flagged'?r.joint_hot_dry_deviation:filter==='warm'?r.temperature_z>0:filter==='dry'?r.precipitation_z<0:true;
  function selectConstellationYear(year){
    constellationYear=year;
    if($('constellation-year'))$('constellation-year').value=String(year);
    const chosen=row(year);
    document.querySelectorAll('.constellation-dot').forEach(node=>{
      const active=Number(node.dataset.year)===year;
      node.classList.toggle('selected',active);node.setAttribute('aria-pressed',String(active));
    });
    const element=$('constellation-inspector');if(!element||!chosen)return;
    element.innerHTML=`<strong>${chosen.year}</strong><div class="constellation-observation"><span>Temperature</span><b>${fmt(chosen.temperature_c,2)} °C</b></div><div class="constellation-observation"><span>Temperature departure</span><b>${signed(chosen.temperature_departure_c,2)} °C</b></div><div class="constellation-observation"><span>Rainfall total</span><b>${fmt(chosen.precipitation_mm,1)} mm</b></div><div class="constellation-observation"><span>Rainfall departure</span><b>${signed(chosen.precipitation_departure_mm,1)} mm</b></div><div class="constellation-observation"><span>Exploratory hot / dry</span><b>${chosen.joint_hot_dry_deviation?'Flagged for review':'Not flagged'}</b></div>`;
  }
  function renderConstellation(){
    if(!data)return;
    const source=data.observations.filter(validZ);
    const container=$('constellation-chart');
    if(source.length===0){container.innerHTML='<div class="constellation-unavailable">Standardized analysis unavailable: at least one internal baseline has zero variance.</div>';$('constellation-inspector').textContent='No comparable standardized values available.';return;}
    const filter=$('constellation-filter').value;
    const yearPicker=$('constellation-year');
    if(yearPicker.options.length!==data.observations.length){yearPicker.innerHTML=data.observations.map(r=>`<option value="${r.year}">${r.year}</option>`).join('');}
    const maxExtent=Math.max(2,Math.ceil(Math.max(...source.flatMap(r=>[Math.abs(r.temperature_z),Math.abs(r.precipitation_z)]))));
    const W=680,H=450,l=66,r=30,t=26,b=66,pw=W-l-r,ph=H-t-b;
    const px=v=>l+((v+maxExtent)/(2*maxExtent))*pw;
    const py=v=>t+((maxExtent-v)/(2*maxExtent))*ph;
    const step=maxExtent>=8?Math.ceil(maxExtent/4):maxExtent>=4?2:1;
    const grid=[];
    for(let tick=-maxExtent;tick<=maxExtent;tick+=step){
      grid.push(`<line x1="${px(tick)}" y1="${t}" x2="${px(tick)}" y2="${H-b}" stroke="${tick===0?'#64737d':'#e2e3de'}" stroke-width="${tick===0?1.5:1}" stroke-dasharray="${tick===0?'5 4':'3 6'}"/><text x="${px(tick)}" y="${H-b+19}" fill="#59646a" font-size="12" text-anchor="middle">${tick}</text>`);
      grid.push(`<line y1="${py(tick)}" x1="${l}" y2="${py(tick)}" x2="${W-r}" stroke="${tick===0?'#64737d':'#e2e3de'}" stroke-width="${tick===0?1.5:1}" stroke-dasharray="${tick===0?'5 4':'3 6'}"/><text y="${py(tick)+4}" x="${l-14}" fill="#59646a" font-size="12" text-anchor="end">${tick}</text>`);
    }
    const points=source.map(r=>{
      const display=constellationMatch(r,filter);
      return `<circle class="constellation-dot ${r.joint_hot_dry_deviation?'flagged':''} ${display?'':'dimmed'}" data-year="${r.year}" role="button" tabindex="0" aria-label="Inspect ${r.year}: temperature ${signed(r.temperature_z,2)} standardized units; rainfall ${signed(r.precipitation_z,2)} standardized units" aria-pressed="false" cx="${px(r.temperature_z)}" cy="${py(r.precipitation_z)}" r="${r.joint_hot_dry_deviation?8:6.5}"><title>${r.year} — temp ${signed(r.temperature_z,2)} z · rain ${signed(r.precipitation_z,2)} z</title></circle>`;
    }).join('');
    container.innerHTML=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Scatterplot: horizontal temperature anomaly and vertical rainfall anomaly, standardized using the internal baseline"><rect x="${px(1)}" y="${py(-1)}" width="${px(maxExtent)-px(1)}" height="${py(-maxExtent)-py(-1)}" fill="#fff0c7" opacity=".7"/><text x="${W-r-8}" y="${H-b-12}" font-size="11" fill="#9e6d00" text-anchor="end">HOT / DRY EXPLORATORY QUADRANT</text>${grid.join('')}${points}<text x="${(l+W-r)/2}" y="${H-13}" font-size="13" text-anchor="middle" fill="#495a60">Air temperature departure (baseline standard deviations)</text><text transform="translate(18 ${(t+H-b)/2}) rotate(-90)" font-size="13" text-anchor="middle" fill="#495a60">Precipitation departure (baseline standard deviations)</text></svg>`;
    container.querySelectorAll('.constellation-dot').forEach(node=>{
      const activate=()=>showYear(node.dataset.year);
      node.addEventListener('click',activate);
      node.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();activate();}});
    });
    const visible=source.filter(r=>constellationMatch(r,filter));
    const requested=source.find(r=>r.year===constellationYear&&constellationMatch(r,filter));
    selectConstellationYear(requested?.year??visible.at(-1)?.year??source.at(-1).year);
  }
  function renderFindings() {
    $('brief-findings').innerHTML=data.findings.map((item,i)=>{
      const positive=item.trend_per_decade>0;
      const nochange=item.trend_per_decade===0;
      return `<article class="brief-finding brief-finding-${esc(item.id)}">
        <div class="brief-finding-top"><span>${esc(item.eyebrow)}</span><span>${i===0?'T2M':'PRECTOTCORR'}</span></div>
        <div class="brief-finding-main"><div><h3>${esc(item.title)}</h3><div class="brief-finding-direction">${esc(item.direction)}</div></div><div class="brief-big-number">${signed(item.trend_per_decade,2)}<small>${esc(item.unit)}</small></div></div>
        <div class="brief-finding-footer"><span class="brief-inference-dot"></span><span>${esc(friendlyP(item.p_hac))}</span></div>
        <p>${esc(item.description)}</p></article>`;
    }).join('');
  }
  function renderTimeline() {
    const values=data.observations;
    const w=860,h=252,lp=52,rp=22,tp=24,bp=38,innerW=w-lp-rp,innerH=h-tp-bp;
    const years=values.map(v=>v.year),minYear=years[0],maxYear=years.at(-1),N=Math.max(1,maxYear-minYear);
    const coords=(name)=>values.map(v=>{
      const val=v[name];if(val==null||!Number.isFinite(val))return null;
      return [lp+(v.year-minYear)/N*innerW,tp+innerH*(1-clamp((val+3)/6,0,1))];
    });
    const line=(c)=>{
      let out='',started=false;
      for(const p of c){if(!p){started=false;continue;}out+=(started?' L ':' M ')+p[0].toFixed(1)+' '+p[1].toFixed(1);started=true;}
      return out;
    };
    const grid=[-2,-1,0,1,2].map(n=>{const y=tp+innerH*(1-(n+3)/6);return `<line x1="${lp}" x2="${w-rp}" y1="${y}" y2="${y}" stroke="${n===0?'#b8b6a4':'#e4e3d7'}" stroke-dasharray="${n===0?'0':'3 7'}"/><text x="${lp-12}" y="${y+4}" text-anchor="end" fill="#59646a" font-size="12">${n>0?'+':''}${n}</text>`;}).join('');
    const ticks=[minYear,Math.round(minYear+N/4),Math.round(minYear+N/2),Math.round(minYear+3*N/4),maxYear].map(y=>`<text x="${lp+(y-minYear)/N*innerW}" y="${h-9}" text-anchor="middle" fill="#59646a" font-size="12">${y}</text>`).join('');
    $('brief-timeline').innerHTML=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="NASA annual standardized departures from internal baseline. Orange is temperature and blue is rainfall."><title>Annual standardized temperature and precipitation deviations</title>${grid}${ticks}<path d="${line(coords('temperature_z'))}" fill="none" stroke="#be8d00" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"/><path d="${line(coords('precipitation_z'))}" fill="none" stroke="#316fa5" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"/>${values.map(v=>{const x=lp+(v.year-minYear)/N*innerW;const y=tp+innerH*(1-clamp(((v.temperature_z??0)+3)/6,0,1));return v.temperature_z==null?'':`<circle cx="${x}" cy="${y}" r="3" fill="#be8d00"/>`;}).join('')}</svg>`;
  }
  function compareYears() {
    const a=row($('brief-year-a').value),b=row($('brief-year-b').value);if(!a||!b)return;
    const deltaT=b.temperature_c-a.temperature_c,deltaP=b.precipitation_mm-a.precipitation_mm;
    $('brief-year-compare').innerHTML=`<div class="brief-comparison-banner"><span>${a.year} <i>versus</i> ${b.year}</span><small>Two source-backed annual values</small></div>
      <div class="brief-comparison-row"><div><span>TEMPERATURE</span><strong>${signed(deltaT,2)} °C</strong><small>${fmt(a.temperature_c)} °C → ${fmt(b.temperature_c)} °C</small></div><div class="brief-change-icon">${deltaT>0?'Higher':deltaT<0?'Lower':'Unchanged'}</div></div>
      <div class="brief-comparison-row"><div><span>RAINFALL TOTAL</span><strong>${signed(deltaP,1)} mm</strong><small>${fmt(a.precipitation_mm,1)} mm → ${fmt(b.precipitation_mm,1)} mm</small></div><div class="brief-change-icon">${deltaP>0?'Higher':deltaP<0?'Lower':'Unchanged'}</div></div>`;
  }
  function showYear(year) {
    if(!row(year))return;
    $('brief-year-b').value=String(year);
    compareYears();
    selectConstellationYear(Number(year));
    document.querySelectorAll('.brief-year-cell').forEach(cell=>{
      cell.classList.toggle('selected',cell.dataset.year===String(year));
      cell.setAttribute('aria-pressed',String(cell.dataset.year===String(year)));
    });
  }
  function renderMatrix() {
    $('brief-year-a').innerHTML=$('brief-year-b').innerHTML=data.observations.map(x=>`<option value="${x.year}">${x.year}</option>`).join('');
    $('brief-year-a').value=String(data.observations[0].year);
    $('brief-year-b').value=String(data.observations.at(-1).year);
    const max=Math.max(0.1,...data.observations.map(x=>Math.max(Math.abs(x.temperature_z??0),Math.abs(x.precipitation_z??0))));
    $('brief-year-matrix').innerHTML=data.observations.map((x,i)=>{
      const t=x.temperature_z,p=x.precipitation_z;
      const tt=t==null?'No baseline variance':`${signed(x.temperature_departure_c,2)} °C from baseline`;
      const pp=p==null?'No baseline variance':`${signed(x.precipitation_departure_mm,1)} mm from baseline`;
      const bar=(val,kind)=>val==null?`<span class="brief-signal-bar empty"></span>`:`<span class="brief-signal-bar ${kind}" style="--strength:${minmax(Math.abs(val)/Math.max(max,1),.08,1).toFixed(2)}"><i style="--offset:${val>=0?'positive':'negative'}"></i></span>`;
      return `<button type="button" data-year="${x.year}" aria-pressed="false" class="brief-year-cell" aria-label="Inspect ${x.year}: temperature ${esc(tt)}, precipitation ${esc(pp)}"><span class="brief-year-label">${x.year}</span><div class="brief-mini-signals">${bar(t,'warm')}${bar(p,'cool')}</div><span class="brief-year-flag">${x.joint_hot_dry_deviation?'◎':'·'}</span></button>`;
    }).join('');
    for(const cell of document.querySelectorAll('.brief-year-cell'))cell.addEventListener('click',()=>showYear(cell.dataset.year));
    showYear(data.observations.at(-1).year);
  }
  function renderSupporting() {
    const e=data.contrast,j=data.joint_flags,a=data.association;
    $('brief-era').innerHTML=`<div class="brief-epoch"><span>EARLY RECORD</span><strong>${e.early[0]}–${e.early[1]}</strong></div><div class="brief-epoch-arrow">→</div><div class="brief-epoch"><span>LATE RECORD</span><strong>${e.late[0]}–${e.late[1]}</strong></div><div class="brief-era-stats"><div><span>Temperature period difference</span><b>${signed(e.temperature_change_c,2)} °C</b></div><div><span>Precipitation period difference</span><b>${signed(e.precipitation_change_mm,1)} mm</b></div></div>`;
    $('brief-joint').innerHTML=`<div class="brief-joint-stat"><span>EXPLORATORY HOT/DRY FLAGS</span><strong>${j.count}</strong><small>of ${data.period.shared_complete_years} shared complete years</small></div><div class="brief-joint-years">${j.years.length?j.years.map(y=>`<button type="button" data-year="${y}" class="brief-flag-year">${y}</button>`).join(''):'<span>No years crossed both exploratory thresholds.</span>'}</div><div class="brief-association">Detrended correlation: <b>${a.detrended_pearson_r==null?'not estimable':fmt(a.detrended_pearson_r,3)}</b><small>Descriptive association, not causal evidence.</small></div>`;
    for(const b of document.querySelectorAll('.brief-flag-year'))b.addEventListener('click',()=>{showYear(b.dataset.year);$('brief-year-compare').scrollIntoView({behavior:'smooth',block:'center'});});
    const evi=data.evidence;
    $('brief-ledger').innerHTML=[
      ['SOURCE','NASA POWER'],
      ['PRODUCT TYPE',data.product_type],
      ['COORDINATES',`${fmt(data.location.latitude,4)}, ${fmt(data.location.longitude,4)}`],
      ['PAIRED YEARS',String(data.period.shared_complete_years)],
      ['TEMPERATURE DATA SHA-256',evi.temperature.sha256_monthly],
      ['RAINFALL DATA SHA-256',evi.precipitation.sha256_monthly],
      ['BRIEFING SHA-256',evi.briefing_sha256],
      ['METHODOLOGY','Annual aggregates; OLS/HAC; paired evidence'],
    ].map(([label,value])=>`<div class="brief-ledger-row"><span>${esc(label)}</span><code title="${attr(value)}">${esc(value)}</code></div>`).join('');
    $('brief-limit-list').innerHTML=data.limitations.map(x=>`<li>${esc(x)}</li>`).join('');
  }
  function render() {
    const name=selectedName();
    $('brief-place').textContent=name+' · paired climate record';
    $('brief-time-range').textContent=`${data.period.paired_years[0]}–${data.period.paired_years[1]}  ·  ${fmt(data.location.latitude,3)}°, ${fmt(data.location.longitude,3)}°`;
    const product = String(data.evidence.temperature.product||'')+' '+String(data.evidence.precipitation.product||'');
    $('brief-source-status').textContent=/synthetic|fixture|test-only/i.test(product)?'SYNTHETIC TEST FIXTURE — NOT NASA OBSERVATIONS':`NASA POWER · ${data.product_type}`;
    $('brief-source-coverage').textContent=`${data.period.shared_complete_years} complete paired years`;
    renderFindings();renderTimeline();renderMatrix();renderSupporting();renderConstellation();show('results');
    window.dispatchEvent(new CustomEvent('aetheris:briefing-ready', { detail: { data, query:lastQuery, place:selectedName() } }));
  }
  async function run(event){
    if(event)event.preventDefault();
    let q;
    try{q=form();}catch(error){$('brief-error-message').textContent=error.message;show('error');return;}
    if(active)active.abort();active=new AbortController();
    show('loading');$('brief-submit').disabled=true;
    try{
      const path='/api/v1/briefing?'+new URLSearchParams(Object.fromEntries(Object.entries(q).map(([key,val])=>[key,String(val)])));
      const result=await api(path,{signal:active.signal});
      if(!result?.evidence?.briefing_sha256||!Array.isArray(result.observations)||!result.observations.length||result.findings?.length!==2)throw Error('Incomplete evidence returned; no results shown.');
      data=result;lastQuery=q;render();
      const fixture=/synthetic|fixture|test-only/i.test(String(result.evidence?.temperature?.product||'')+' '+String(result.evidence?.precipitation?.product||''));
      toast(fixture?'SYNTHETIC TEST FIXTURE loaded — not NASA observations.':'Source-backed climate evidence is ready.');
    }catch(error){if(error.name==='AbortError')return;$('brief-error-message').textContent=error.message;show('error');}
    finally{$('brief-submit').disabled=false;}
  }
  function init(options) {
    go=options.go;api=options.api;toast=options.toast;
    const places=options.locations.filter(x=>Number.isFinite(x.lat)&&Number.isFinite(x.lon));
    $('brief-location').innerHTML=places.map(x=>`<option value="${x.lat},${x.lon}">${esc(x.name)}, ${esc(x.country)}</option>`).join('')+'<option value="custom">Custom coordinates</option>';
    $('brief-location').value='32.337,-6.349';
    $('brief-location').addEventListener('change',()=>{const found=places.find(x=>`${x.lat},${x.lon}`===$('brief-location').value);if(found){$('brief-lat').value=found.lat;$('brief-lon').value=found.lon;}});
    for(const id of ['brief-lat','brief-lon'])$(id).addEventListener('change',()=>{$('brief-location').value='custom';});
    $('brief-form').addEventListener('submit',run);
    $('brief-retry').addEventListener('click',run);
    $('brief-year-a').addEventListener('change',compareYears);
    $('brief-year-b').addEventListener('change',()=>showYear($('brief-year-b').value));
    $('brief-share').addEventListener('click',share);
    $('brief-capsule').addEventListener('click', async()=>{
      if(!data || !lastQuery)return toast('Run an investigation first.');
      const button=$('brief-capsule');button.disabled=true;button.textContent='Preparing verified data…';
      try {
        const url='/api/v1/reproducibility.zip?'+new URLSearchParams(Object.fromEntries(Object.entries(lastQuery).map(([k,v])=>[k,String(v)])));
        const response=await fetch(url,{headers:{'Accept':'application/zip'}});
        if(!response.ok)throw Error('Capsule export unavailable. Check NASA connectivity.');
        const bytes=await response.blob();
        if(!bytes.size)throw Error('Empty capsule export.');
        const temp=URL.createObjectURL(bytes);const a=document.createElement('a');a.href=temp;a.download='AETHERIS_Reproducibility_Capsule.zip';a.click();setTimeout(()=>URL.revokeObjectURL(temp),12000);
        toast('Reproducibility capsule downloaded: data, source fingerprints and offline verifier.');
      }catch(error){toast(error.message);}finally{button.disabled=false;button.textContent='↓ Reproducibility ZIP';}
    });
    $('constellation-filter').addEventListener('change',renderConstellation);
    $('constellation-year').addEventListener('change',e=>showYear(e.target.value));
    $('constellation-reset').addEventListener('click',()=>{$('constellation-filter').value='all';renderConstellation();showYear(data.observations.at(-1).year);});
    $('brief-export-json').addEventListener('click',()=>{if(data)download('AETHERIS_evidence_briefing.json',JSON.stringify(data,null,2),'application/json');});
    $('brief-export-csv').addEventListener('click',()=>{
      if(!data)return;
      const cols=['year','temperature_c','precipitation_mm','temperature_departure_c','precipitation_departure_mm','temperature_z','precipitation_z','joint_hot_dry_deviation'];
      const rows=[cols.join(','),...data.observations.map(r=>cols.map(c=>r[c]??'').join(','))];
      download('AETHERIS_paired_annual_evidence.csv',rows.join('\n'),'text/csv;charset=utf-8');
    });
    $('brief-print').addEventListener('click',()=>{if(data)window.print();});
  }
  function share() {
    if (!data) return toast('Run an investigation first.');
    const q=lastQuery;
    if(!q)return toast('No completed investigation to share.');
    const url=new URL(window.location.href);
    url.searchParams.set('research','1');
    for(const [key,value] of Object.entries(q))url.searchParams.set(key,String(value));
    url.hash='briefing';
    const text=url.toString();
    const legacy=()=>{
      const field=document.createElement('textarea');field.value=text;field.setAttribute('readonly','');
      field.style.position='fixed';field.style.opacity='0';document.body.appendChild(field);field.select();
      const ok=document.execCommand('copy');field.remove();
      if(!ok)throw Error('Clipboard unavailable.');
      toast('Research setup link copied. It needs access to this AETHERIS server.');
    };
    if(navigator.clipboard && navigator.clipboard.writeText){
      navigator.clipboard.writeText(text).then(()=>toast('Research setup link copied. It needs access to this AETHERIS server.'),
        ()=>{try{legacy();}catch{toast('Copy unavailable; please use your browser address bar.');}});
    } else {
      try{legacy();}catch{toast('Copy unavailable; please use your browser address bar.');}
    }
  }
  function restoreShared() {
    const query=new URLSearchParams(window.location.search);
    if(query.get('research')!=='1')return;
    try {
      const keys=['lat','lon','start','end'];
      if(keys.some(key=>!query.has(key)))throw Error('Missing research parameters.');
      for(const key of keys){
        const raw=query.get(key);
        if(!raw||raw.length>22||!/^-?\d+(?:\.\d+)?$/.test(raw))throw Error('Invalid research parameter.');
        $('brief-'+key).value=raw;
      }
      form();
      const matched=$('brief-location').querySelector(`option[value="${$('brief-lat').value},${$('brief-lon').value}"]`);
      $('brief-location').value=matched?.value || 'custom';
      go('briefing');
      run();
    } catch(err) {
      toast('The saved research link is invalid; use the form to investigate.');
    }
  }
  function openFromInvestigation(investigation) {
    if(!investigation?.location||!investigation?.period)return;
    const loc=investigation.location;
    $('brief-lat').value=loc.latitude;
    $('brief-lon').value=loc.longitude;
    $('brief-location').value='custom';
    $('brief-start').value=investigation.period.requested_start;
    $('brief-end').value=investigation.period.requested_end;
    run();
  }
  window.AetherisBriefing={init,openFromInvestigation,restoreShared};
})();
