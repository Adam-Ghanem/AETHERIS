/* AETHERIS Mission Theater 11.0 — present only verified briefing responses. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const esc = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  const fmt = (number, digits=2) => number == null || !Number.isFinite(Number(number)) ? 'Not available' : Number(number).toFixed(digits);
  const signed = (number, digits=2) => number == null || !Number.isFinite(Number(number)) ? 'Not available' : `${Number(number) > 0 ? '+' : ''}${fmt(number,digits)}`;
  const titles = ['The investigation','Four questions','The measured signals','Travel through time','Patterns worth checking','The evidence trail','Research verdict'];
  let state = {data:null, query:null, place:'Selected geographic point', index:0, opened:false, focus:null};
  const cssExport = `
    *{box-sizing:border-box}body{margin:0;background:#f5f4ed;color:#161a18;font:16px/1.5 system-ui,Segoe UI,sans-serif}
    header{position:sticky;top:0;z-index:2;background:#fff;border-bottom:1px solid #deddd1;padding:14px 3vw;display:flex;align-items:center;justify-content:space-between;gap:12px}
    header strong{letter-spacing:.15em}header nav{display:flex;align-items:center;gap:8px}button{cursor:pointer;border:1px solid #252923;border-radius:9px;padding:9px 16px;background:#fff;color:#20241e;font-weight:700}
    button:last-of-type{background:#fbd85e}.slide{display:none;min-height:calc(100vh - 82px);padding:6vh 6vw 8vh;background:linear-gradient(115deg,#fff 0%,#fffdf2 100%)}
    .slide.active{display:block}.slide-inner{max-width:1320px;margin:auto}.tag{letter-spacing:.17em;font:700 12px system-ui;color:#68674b;text-transform:uppercase}
    h1{font-size:clamp(48px,7vw,114px);line-height:.97;letter-spacing:-.07em;margin:26px 0}h2{font-size:clamp(40px,5vw,76px);line-height:1.02;letter-spacing:-.06em;margin:22px 0 24px}
    p{max-width:920px;line-height:1.6;color:#484b44}.hero-lead{font-size:clamp(20px,2.5vw,31px)}.yellow{background:#ffe06a;box-shadow:8px 0 #ffe06a,-8px 0 #ffe06a}
    .track{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px;margin:35px 0}.panel{background:#fff;border:1px solid #dbdbcf;border-radius:18px;padding:26px;min-width:0}
    .panel h3{font-size:22px;letter-spacing:-.04em;margin:10px 0}.value{font-size:clamp(32px,4vw,72px);font-weight:850;letter-spacing:-.055em}.muted{color:#666960}
    .note{margin-top:28px;padding:17px 20px;background:#fff6d8;border-left:4px solid #d4a800}.chart{width:100%;height:auto;max-height:350px}.source{word-break:break-all;font-family:monospace;font-size:13px}
    .year-pills{display:flex;gap:8px;flex-wrap:wrap}.year-pills span{background:#ffe48d;border-radius:30px;padding:8px 16px;font-weight:700}
    .steps{margin-top:30px;display:flex;gap:10px}.steps span{height:5px;flex:1;background:#d8d5c8}.steps .selected{background:#e5b31e}
    .topline{display:flex;justify-content:space-between;align-items:center;gap:20px;border-bottom:1px solid #deddd1;padding-bottom:15px}
    @media(max-width:650px){.slide{padding:25px 20px}.track{grid-template-columns:1fr}h1{font-size:51px}.value{font-size:38px}}
    @media print{header{display:none}.slide,.slide.active{display:block!important;min-height:0;height:190mm;padding:8mm 10mm;break-after:page;page-break-after:always}.slide:last-child{break-after:auto}.track{gap:10px}.panel{padding:12px}.chart{max-height:80mm}body{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
  `;
  function valid(d) {
    return d && Array.isArray(d.observations) && d.observations.length >= 8 && Array.isArray(d.findings) && d.findings.length === 2 && typeof d.evidence?.briefing_sha256 === 'string' && /^[a-f0-9]{64}$/i.test(d.evidence.briefing_sha256);
  }
  function hasFixture(d) { return /synthetic|fixture|test.only/i.test(JSON.stringify(d.evidence || {})); }
  function loc(d) {
    const latitude=d.location?.latitude,longitude=d.location?.longitude;
    return `${fmt(latitude,3)}°, ${fmt(longitude,3)}°`;
  }
  function meta(d) {
    const r=d.period || {};
    const years=r.paired_years || [d.observations[0].year,d.observations.at(-1).year];
    return `${years[0]} — ${years[1]}  ·  ${d.observations.length} shared complete years`;
  }
  function pointLine(rows,key,color,unit) {
    const values = rows.map(r=>({year:Number(r.year),y:Number(r[key])})).filter(r=>Number.isFinite(r.year)&&Number.isFinite(r.y));
    if (!values.length) return '<p>Insufficient observations for chart.</p>';
    const minX=Math.min(...values.map(v=>v.year)), maxX=Math.max(...values.map(v=>v.year));
    const min0=Math.min(...values.map(v=>v.y)),max0=Math.max(...values.map(v=>v.y));
    const span=Math.max(.000001,max0-min0),minY=min0-span*.16,maxY=max0+span*.16;
    const X=x=>65+(x-minX)/Math.max(1,maxX-minX)*770, Y=y=>244-(y-minY)/(maxY-minY)*208;
    const path=values.map((p,i)=>`${i?'L':'M'}${X(p.year).toFixed(2)} ${Y(p.y).toFixed(2)}`).join(' ');
    const ygrid=[0,.25,.5,.75,1].map(p=>{const y=244-p*208;const val=minY+p*(maxY-minY);return `<line x1="65" x2="840" y1="${y}" y2="${y}" stroke="#dedfd3"/><text x="55" y="${y+4}" font-size="12" text-anchor="end" fill="#646963">${fmt(val,1)}</text>`;}).join('');
    const xticks=[minX,Math.round((minX+maxX)/2),maxX].map(y=>`<text x="${X(y)}" y="272" text-anchor="middle" font-size="13" fill="#646963">${y}</text>`).join('');
    return `<svg class="chart" viewBox="0 0 870 292" role="img" aria-label="Observed ${esc(key)} from ${minX} to ${maxX} in ${esc(unit)}"><title>${esc(key)} (${esc(unit)})</title>${ygrid}${xticks}<path d="${path}" fill="none" stroke="${color}" stroke-width="4" stroke-linejoin="round" stroke-linecap="round"/>${values.map(p=>`<circle cx="${X(p.year)}" cy="${Y(p.y)}" r="3.5" fill="${color}"><title>${p.year}: ${fmt(p.y,2)} ${esc(unit)}</title></circle>`).join('')}</svg>`;
  }
  function scene(i,d,place){
    const t=d.findings.find(f=>f.id==='temperature') || d.findings[0],p=d.findings.find(f=>f.id==='precipitation') || d.findings[1];
    const evidence=d.evidence || {}, era=d.contrast || {}, joint=d.joint_flags || {}, rows=d.observations || [], tempHash=evidence.temperature?.sha256_monthly || '',rainHash=evidence.precipitation?.sha256_monthly || '';
    const prefix=`<div class="tag">AETHERIS / SCIENTIFIC MISSION THEATER  ·  ${String(i+1).padStart(2,'0')} / 07</div>`;
    const note=hasFixture(d) ? '<div class="note"><strong>SYNTHETIC TEST FIXTURE — NOT NASA OBSERVATIONS.</strong> This presentation is a UI test. Do not interpret its numbers as measured climate findings.</div>' : '<div class="note">Historical NASA POWER gridded/model-derived point data. Exploratory analysis; not a forecast, local station record, or causal attribution.</div>';
    switch(i) {
      case 0: return `${prefix}<h1>Earth is changing.<br><span class="yellow">Show the evidence.</span></h1><p class="hero-lead">A source-backed climate investigation of <strong>${esc(place)}</strong>.</p><div class="track"><div class="panel"><div class="tag">GEOGRAPHIC POINT</div><div class="value">${esc(loc(d))}</div><div class="muted">${esc(d.location?.country || 'Point observation')}</div></div><div class="panel"><div class="tag">RESEARCH WINDOW</div><div class="value">${rows.length}</div><div>shared complete calendar years · NASA POWER</div><div class="muted">${esc(meta(d))}</div></div></div>${note}`;
      case 1: return `${prefix}<h2>Four questions.<br><span class="yellow">One investigation.</span></h2><div class="track"><article class="panel"><div class="tag">01 / WHAT?</div><h3>Temperature and precipitation</h3><p>Two independently validated annual climate signals at the same coordinates.</p></article><article class="panel"><div class="tag">02 / WHERE?</div><h3>${esc(place)}</h3><p>NASA POWER point at ${esc(loc(d))}, not a citywide average.</p></article><article class="panel"><div class="tag">03 / HOW MUCH?</div><h3>${esc(signed(t.trend_per_decade,3))} °C / decade</h3><p>Estimated temperature slope; precipitation slope ${esc(signed(p.trend_per_decade,2))} mm / decade.</p></article><article class="panel"><div class="tag">04 / HOW CERTAIN?</div><h3>Inspect the evidence</h3><p>HAC exploratory tests and scientific caveats are shown, without claiming causality.</p></article></div>`;
      case 2: return `${prefix}<h2>Two signals.<br><span class="yellow">Different stories.</span></h2><div class="track"><article class="panel"><div class="tag">AIR TEMPERATURE · T2M</div><div class="value">${esc(signed(t.trend_per_decade,3))}<small> °C / decade</small></div><h3>${esc(t.direction)}</h3><p>${esc(t.description)}</p><div class="muted">${esc(t.assessment)} · HAC p = ${esc(fmt(t.p_hac,4))}</div></article><article class="panel"><div class="tag">PRECIPITATION · PRECTOTCORR</div><div class="value">${esc(signed(p.trend_per_decade,2))}<small> mm / decade</small></div><h3>${esc(p.direction)}</h3><p>${esc(p.description)}</p><div class="muted">${esc(p.assessment)} · HAC p = ${esc(fmt(p.p_hac,4))}</div></article></div>${note}`;
      case 3: return `${prefix}<h2>Every year<br><span class="yellow">leaves a signal.</span></h2><div class="track"><article class="panel"><div class="tag">ANNUAL AIR TEMPERATURE / °C</div>${pointLine(rows,'temperature_c','#d4a000','°C')}</article><article class="panel"><div class="tag">ANNUAL PRECIPITATION / mm</div>${pointLine(rows,'precipitation_mm','#2575a6','mm')}</article></div><p>Each dot represents a paired complete calendar year. Two separate axes preserve correct physical units.</p>`;
      case 4: return `${prefix}<h2>Changes worth<br><span class="yellow">investigating.</span></h2><div class="track"><article class="panel"><div class="tag">EARLY vs LATE · BALANCED GROUPS</div><h3>Temperature contrast</h3><div class="value">${esc(signed(era.temperature_change_c,2))} °C</div><p>${esc((era.early||[]).join('–'))} vs ${esc((era.late||[]).join('–'))}. Descriptive difference between period means.</p></article><article class="panel"><div class="tag">EARLY vs LATE · BALANCED GROUPS</div><h3>Precipitation contrast</h3><div class="value">${esc(signed(era.precipitation_change_mm,1))} mm</div><p>Different yearly rainfall totals do not prove causation or a climate mechanism.</p></article></div><div class="panel"><div class="tag">JOINT HOT / DRY SCREENING FLAGS · EXPLORATORY</div><div class="value">${joint.count ?? '—'}</div><div class="year-pills">${(joint.years||[]).length ? joint.years.map(y=>`<span>${esc(y)}</span>`).join('') : '<span>No screened years in the selected record</span>'}</div><p>Flags compare with an internal baseline using exploratory ±1 sample-SD thresholds. They are not validated drought classifications.</p></div>`;
      case 5: return `${prefix}<h2>No black box.<br><span class="yellow">Follow the trail.</span></h2><div class="track"><article class="panel"><div class="tag">SOURCE DATA</div><h3>NASA POWER</h3><p>Two independently retrieved annual products: T2M and PRECTOTCORR.</p><div class="source">TEMPERATURE ${esc(tempHash || 'Not available')}</div><div class="source">PRECIPITATION ${esc(rainHash || 'Not available')}</div></article><article class="panel"><div class="tag">REPRODUCIBILITY</div><h3>Evidence fingerprint</h3><p>SHA-256 of this exact briefing's source-linked inputs and year coverage.</p><div class="source">${esc(evidence.briefing_sha256)}</div><p class="muted">Fingerprint is traceability, not scientific proof.</p></article></div><div class="panel"><div class="tag">SCIENTIFIC LIMITATIONS</div><p>${esc((d.limitations || []).slice(0,3).join('  •  '))}</p></div>`;
      default: return `${prefix}<h1>From observation<br>to <span class="yellow">understanding.</span></h1><p class="hero-lead">${esc(place)} · ${esc(meta(d))}</p><div class="track"><div class="panel"><div class="tag">THERMAL ESTIMATE</div><div class="value">${esc(signed(t.trend_per_decade,3))}<small> °C / decade</small></div><p>Observed trend estimate, not a prediction.</p></div><div class="panel"><div class="tag">RAINFALL ESTIMATE</div><div class="value">${esc(signed(p.trend_per_decade,2))}<small> mm / decade</small></div><p>Observed trend estimate, not causal attribution.</p></div></div><h3>Explore. Verify. Question.</h3><p>AETHERIS turns NASA Earth-system data into reproducible investigations. Every finding is linked to its source, methodology, and limitations.</p>${note}`;
    }
  }
  function render(){
    if (!valid(state.data)) return;
    const d=state.data,i=state.index;
    $('mission-scene').innerHTML=`<div class="mission-content">${scene(i,d,state.place)}</div>`;
    $('mission-counter').textContent=`${String(i+1).padStart(2,'0')} / 07`;
    $('mission-slide-title').textContent=hasFixture(d) ? 'TEST FIXTURE — '+titles[i] : titles[i];
    $('mission-prev').disabled=i===0;
    $('mission-next').textContent=i===6?'Restart ↺':'Next →';
    [...$('mission-steps').children].forEach((button,idx)=>{button.classList.toggle('active',idx===i);button.setAttribute('aria-current',idx===i?'step':'false');});
    $('mission-scene').scrollTop=0;
  }
  function setSlide(n){state.index=Math.max(0,Math.min(6,n));render();}
  function open(){
    if(!valid(state.data)) return false;
    state.focus=document.activeElement;
    $('mission-overlay').classList.remove('hidden');$('mission-overlay').setAttribute('aria-hidden','false');
    state.opened=true;document.body.classList.add('mission-is-open');setSlide(0);$('mission-close').focus();return true;
  }
  function close(){state.opened=false;$('mission-overlay').classList.add('hidden');$('mission-overlay').setAttribute('aria-hidden','true');document.body.classList.remove('mission-is-open');state.focus?.focus?.();}
  function askToPresent(){
    if(open())return;
    const openBrief=document.querySelector('[data-view="briefing"]');openBrief?.click();
    $('brief-form')?.scrollIntoView({block:'start',behavior:'smooth'});
    $('brief-location')?.focus();
    const note=$('mission-prompt');if(note){note.hidden=false;note.textContent='Run a source-backed briefing first. Mission Theater uses the retrieved evidence — never invented values.';}
  }
  function offlineHtml(){
    if(!valid(state.data))throw Error('No complete verified investigation.');
    const slides=titles.map((name,i)=>`<section class="slide ${i===0?'active':''}" data-slide="${i}"><div class="slide-inner"><div class="topline"><strong>AETHERIS / ${esc(name.toUpperCase())}</strong><span>NASA POWER · ${esc(state.place)}</span></div>${scene(i,state.data,state.place)}<div class="steps">${titles.map((_,j)=>`<span class="${i===j?'selected':''}"></span>`).join('')}</div></div></section>`).join('');
    const offlineJS=`(()=>{let i=0;const slides=[...document.querySelectorAll('.slide')],count=document.getElementById('count');function show(n){i=(n+slides.length)%slides.length;slides.forEach((s,j)=>s.classList.toggle('active',j===i));count.textContent=(i+1)+' / '+slides.length;scrollTo(0,0)}document.getElementById('prev').onclick=()=>show(i-1);document.getElementById('next').onclick=()=>show(i+1);document.getElementById('print').onclick=()=>print();document.addEventListener('keydown',e=>{if(e.key==='ArrowRight')show(i+1);if(e.key==='ArrowLeft')show(i-1)});})();`;
    return `<!doctype html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>AETHERIS Research Mission — ${esc(state.place)}</title><style>${cssExport}</style></head><body><header><strong>◉ AETHERIS / OFFLINE EVIDENCE DECK</strong><nav><button id="prev">←</button><span id="count">1 / 7</span><button id="next">→</button><button id="print">Print / PDF</button></nav></header><main>${slides}</main><script>${offlineJS}<\/script></body></html>`;
  }
  function download(name,body,type){const blob=new Blob([body],{type});const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),4000);}
  function init(){
    if(!$('mission-overlay'))return;
    $('mission-steps').innerHTML=titles.map((name,i)=>`<button type="button" aria-label="Go to slide ${i+1}: ${esc(name)}" title="${esc(name)}">${String(i+1).padStart(2,'0')} · ${esc(name)}</button>`).join('');
    [...$('mission-steps').children].forEach((btn,i)=>btn.addEventListener('click',()=>setSlide(i)));
    $('mission-prev').addEventListener('click',()=>setSlide(state.index-1));
    $('mission-next').addEventListener('click',()=>setSlide(state.index===6?0:state.index+1));
    $('mission-close').addEventListener('click',close);
    $('mission-download').addEventListener('click',()=>{if(!valid(state.data))return;download('AETHERIS_Mission_Theater_OFFLINE.html',offlineHtml(),'text/html;charset=utf-8');});
    $('mission-json').addEventListener('click',()=>{if(valid(state.data))download('AETHERIS_Mission_Evidence.json',JSON.stringify(state.data,null,2),'application/json');});
    $('mission-present')?.addEventListener('click',askToPresent);
    $('mission-launch-home')?.addEventListener('click',askToPresent);
    $('mission-launch-spotlight')?.addEventListener('click',askToPresent);
    window.addEventListener('aetheris:briefing-ready',ev=>{
      if(!valid(ev.detail?.data))return;
      state.data=ev.detail.data;state.query=ev.detail.query;state.place=ev.detail.place || 'Selected geographic point';
      $('mission-present').disabled=false;
      $('mission-overlay').dataset.sourceKind = hasFixture(state.data) ? 'synthetic-test' : 'source-backed';
      const note=$('mission-prompt');if(note)note.hidden=true;
    });
    document.addEventListener('keydown',ev=>{
      if(!state.opened)return;
      if(ev.key==='Escape'){ev.preventDefault();close();}
      if(ev.key==='ArrowRight' || ev.key==='PageDown'){ev.preventDefault();setSlide(Math.min(6,state.index+1));}
      if(ev.key==='ArrowLeft' || ev.key==='PageUp'){ev.preventDefault();setSlide(Math.max(0,state.index-1));}
      if(ev.key==='Home'){ev.preventDefault();setSlide(0);}
      if(ev.key==='End'){ev.preventDefault();setSlide(6);}
      if(ev.key==='Tab'){
        const focusable=[...$('mission-overlay').querySelectorAll('button:not([disabled])')].filter(el=>el.getClientRects().length);
        const first=focusable[0],last=focusable.at(-1);
        if(ev.shiftKey&&document.activeElement===first){ev.preventDefault();last.focus();}
        else if(!ev.shiftKey&&document.activeElement===last){ev.preventDefault();first.focus();}
      }
    });
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
  window.AetherisMissionTheater={open,close,getState:()=>({loaded:valid(state.data),index:state.index,opened:state.opened})};
})();
