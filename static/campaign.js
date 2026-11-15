/* AETHERIS Research Campaign Studio — only data returned by the science API. */
(() => {
  'use strict';
  const el = id => document.getElementById(id);
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const fmt = (value, n=2) => value == null || !Number.isFinite(Number(value)) ? 'N/A' : (Number(value) > 0 ? '+' : '') + Number(value).toFixed(n);
  let data = null, year = 2025, toast;
  function download(filename, content, type='application/json') {
    const url = URL.createObjectURL(new Blob([content], {type}));
    const link = document.createElement('a'); link.href=url;link.download=filename; document.body.appendChild(link);link.click();link.remove();
    setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  const results = () => data?.locations?.filter(r => r.status === 'ok') || [];
  function bars(variable) {
    const rows = results();
    if(!rows.length) return '<p class="campaign-help">No verified source observations available.</p>';
    const max = Math.max(.00001,...rows.map(r=>Math.abs(r[variable].slope_per_decade)));
    return rows.map(r=>{
      const slope = r[variable].slope_per_decade;
      const q = r[variable].q_bh;
      const width = Math.min(100,Math.abs(slope)/max*100);
      return `<div class="campaign-bar-row"><div class="campaign-bar-label"><strong>${esc(r.name)}</strong><span>${fmt(slope,3)} ${esc(r[variable].unit)}</span></div><div class="campaign-bar-track"><span style="width:${width.toFixed(2)}%;background:${variable==='temperature'?'#e2ac22':'#568aab'}"></span></div><small>HAC p ${r[variable].p_hac == null?'N/A':fmt(r[variable].p_hac,4)} · BH q ${q == null?'N/A':fmt(q,4)}${r[variable].exploratory_fdr_flag?' · exploratory flag':''}</small></div>`;
    }).join('');
  }
  function yearCard(row, chosenYear) {
    if(row.status !== 'ok') return `<article class="campaign-year-card unavailable"><span>${esc(row.name)}</span><strong>Source unavailable</strong><small>${esc(row.error)}</small></article>`;
    const d = row.annual.find(r=>r.year===chosenYear);
    if(!d) return `<article class="campaign-year-card unavailable"><span>${esc(row.name)}</span><strong>No complete paired record</strong><small>${chosenYear}</small></article>`;
    return `<article class="campaign-year-card"><div class="campaign-year-title"><strong>${esc(row.name)}</strong><span>${d.compound_flag?'Joint departure flag':'Two observed signals'}</span></div>
       <div class="campaign-year-numbers"><div><small>Temperature</small><b>${fmt(d.temperature_c,2)} °C</b><em>Δ ${fmt(d.temperature_departure_c,2)} °C</em></div><div><small>Precipitation</small><b>${fmt(d.precipitation_mm,1)} mm</b><em>Δ ${fmt(d.precipitation_departure_mm,1)} mm</em></div></div></article>`;
  }
  function setYear(next) {
    if(!data)return;
    year = Number(next);
    el('campaign-year').value=String(year);
    el('campaign-year-value').textContent=String(year);
    el('campaign-year-grid').innerHTML=data.locations.map(r=>yearCard(r,year)).join('');
    el('campaign-year-caption').textContent=`Annual point values and departures relative to each location's own first-up-to-ten-common-year internal baseline. ${year} is a historical observation, not a prediction.`;
  }
  function render(d) {
    data=d;
    el('campaign-completed').textContent=`${d.successful_count} / ${d.requested_count} locations`;
    el('campaign-period-value').textContent=`${d.period.start}–${d.period.end}`;
    el('campaign-sha').textContent=d.manifest.campaign_sha256;
    el('campaign-bar-temp').innerHTML=bars('temperature');
    el('campaign-bar-rain').innerHTML=bars('precipitation');
    el('campaign-source-list').innerHTML=d.locations.map(r=>r.status==='ok'?`<li><b>${esc(r.name)}</b>: ${r.shared_year_count} paired years · <code>${esc(r.source.paired_sha256.slice(0,20))}…</code></li>`:`<li><b>${esc(r.name)}</b>: UNAVAILABLE — ${esc(r.error)}</li>`).join('');
    el('campaign-limits').innerHTML=d.limitations.map(x=>`<li>${esc(x)}</li>`).join('');
    const ys = [...new Set(results().flatMap(r=>r.annual.map(x=>x.year)))].sort((a,b)=>a-b);
    if(ys.length){
      const slider=el('campaign-year');slider.min=ys[0];slider.max=ys[ys.length-1];slider.step=1;slider.disabled=false;
      const selector=el('campaign-year-options');selector.innerHTML=ys.map(y=>`<option value="${y}">${y}</option>`).join('');selector.disabled=false;
      const latest=ys.at(-1); slider.value=latest;selector.value=latest; setYear(latest);
    } else {el('campaign-year').disabled=true;el('campaign-year-options').disabled=true;el('campaign-year-grid').innerHTML='<p>No comparable annual data.</p>';}
    el('campaign-results').hidden=false;
    el('campaign-empty').hidden=true;
  }
  async function run(e, api) {
    e?.preventDefault?.();
    const chosen = [...el('campaign-locations').querySelectorAll('input:checked')].map(x=>x.value);
    const start = Number(el('campaign-start').value), end = Number(el('campaign-end').value);
    if(chosen.length < 2 || chosen.length > 6){toast('Choose between 2 and 6 cities.');return;}
    if(!Number.isInteger(start)||!Number.isInteger(end)||end-start<7||start<1981||end>2025){toast('Choose a valid historical window of at least 8 years.');return;}
    el('campaign-action').disabled=true; el('campaign-error').hidden=true; el('campaign-loading').hidden=false;
    try{
      const params = new URLSearchParams({locations:chosen.join(','),start:String(start),end:String(end)});
      render(await api(`/api/v1/campaign?${params}`));
      toast('Campaign evidence loaded. Inspect source fingerprints before interpreting trends.');
    }catch(err){el('campaign-error').textContent=err.message;el('campaign-error').hidden=false;}
    finally{el('campaign-action').disabled=false;el('campaign-loading').hidden=true;}
  }
  function csv() {
    if(!data)return;
    const q=x=>`"${String(x??'').replaceAll('"','""')}"`;
    const rows=[['location','latitude','longitude','year','temperature_c','precipitation_mm','temperature_departure_c','precipitation_departure_mm','compound_flag','paired_source_sha256']];
    data.locations.forEach(r=>{if(r.status==='ok')r.annual.forEach(y=>rows.push([r.name,r.lat,r.lon,y.year,y.temperature_c,y.precipitation_mm,y.temperature_departure_c,y.precipitation_departure_mm,y.compound_flag,r.source.paired_sha256]));});
    download('AETHERIS_campaign_annual_evidence.csv',rows.map(r=>r.map(q).join(',')).join('\n'),'text/csv;charset=utf-8');
  }
  function slides() {
    if(!data)return;
    const d=data;
    const t=d.highlights.largest_temperature_slope_in_sample;
    const p=d.highlights.smallest_precipitation_slope_in_sample;
    const page=(title,inner)=>`<section class="slide"><header>AETHERIS / EARTH INTELLIGENCE <span>NASA POWER · Independent Project</span></header><div class="slide-content"><h1>${esc(title)}</h1>${inner}</div><footer>${esc(d.period.start)}–${esc(d.period.end)} · Scientific evidence, not attribution</footer></section>`;
    const li=d.locations.map(r=>r.status==='ok'?`<tr><td>${esc(r.name)}</td><td>${fmt(r.temperature.slope_per_decade,3)} °C/decade</td><td>${fmt(r.precipitation.slope_per_decade,2)} mm/decade</td><td>${r.shared_year_count}</td></tr>`:`<tr><td>${esc(r.name)}</td><td colspan="3">Unavailable: ${esc(r.error)}</td></tr>`).join('');
    const html=`<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AETHERIS · Scientific Research Campaign</title><style>*{box-sizing:border-box}body{margin:0;font-family:Arial,Helvetica,sans-serif;color:#1e2d36;background:#f5f4ef}.slide{background:#fff;min-height:100vh;padding:4vw 6vw;display:flex;flex-direction:column;page-break-after:always;border-bottom:2px solid #f0e3b8}header,footer{font-size:13px;font-weight:bold;letter-spacing:2px}header{border-bottom:2px solid #e2ac22;padding-bottom:18px;display:flex;justify-content:space-between}header span{font-weight:normal;letter-spacing:0}.slide-content{flex:1;padding:5vh 0}.slide h1{font-size:clamp(38px,6vw,78px);line-height:1.08;max-width:1100px}.slide p{font-size:clamp(19px,2.1vw,28px);line-height:1.45;max-width:1100px}.gold{color:#a67a00}table{border-collapse:collapse;width:100%;font-size:18px}td,th{padding:13px 12px;border-bottom:1px solid #e0dfd7;text-align:left}th{background:#fff4d4}footer{padding-top:18px;border-top:1px solid #ddd;font-size:11px;color:#68757c}.chip{display:inline-block;padding:10px 16px;background:#fff1c4;border-radius:12px;margin:8px;font-size:20px}code{font-size:12px;word-break:break-all}@media print{.slide{height:100vh;min-height:0}@page{size:landscape;margin:0}}</style>
     ${page('Discover Earth’s hidden changes','<p>Four questions: What changed? Where? By how much? How strong is the evidence?</p><p class="gold">A reproducible climate investigation using NASA POWER observations.</p>')}
     ${page('Study design',`<p><span class="chip">${d.requested_count} selected points</span><span class="chip">${d.successful_count} verified points</span><span class="chip">Two climate signals</span></p><p>Temperature (°C) and estimated annual precipitation (mm) are analyzed separately at each point, with HAC-robust trend inference and exploratory BH adjustment within each signal family.</p>`)}
     ${page('Observed trends',`<table><thead><tr><th>Sample point</th><th>Temperature slope</th><th>Precipitation slope</th><th>Paired years</th></tr></thead><tbody>${li}</tbody></table>`)}
     ${page('Read the results carefully',`<p>Within these selected points, the largest estimated temperature slope is <b>${t?esc(t.name)+' ('+fmt(t.slope_per_decade,3)+' °C/decade)':'unavailable'}</b>.</p><p>The smallest estimated precipitation slope is <b>${p?esc(p.name)+' ('+fmt(p.slope_per_decade,2)+' mm/decade)':'unavailable'}</b>.</p><p>These are comparisons within a user-selected sample, not global or regional extremes.</p>`)}
     ${page('Scientific limits',`<p>${d.limitations.slice(0,4).map(esc).join('</p><p>')}</p>`)}
     ${page('Verify the evidence',`<p>Provider: NASA POWER · Gridded / model-derived point data.</p><p>Record SHA-256 campaign fingerprint:</p><p><code>${esc(d.manifest.campaign_sha256)}</code></p><p>Full annual values and source hashes are available from the original AETHERIS campaign JSON/CSV exports. This fingerprint is an integrity marker, not a NASA signature.</p>`)}
     </html>`;
    download('AETHERIS_campaign_presentation.html',html,'text/html;charset=utf-8');
  }
  function init({api,toast: notify,locations}) {
    toast=notify;
    const defaults=new Set(['Beni Mellal','Marrakech','Casablanca','Ouarzazate']);
    el('campaign-locations').innerHTML=locations.map(x=>`<label class="campaign-place"><input type="checkbox" value="${esc(x.name)}" ${defaults.has(x.name)?'checked':''}/><span><strong>${esc(x.name)}</strong><small>${esc(x.country)}</small></span></label>`).join('');
    el('campaign-form').addEventListener('submit',e=>run(e,api));
    el('campaign-year').addEventListener('input',e=>{el('campaign-year-options').value=e.target.value;setYear(e.target.value);});
    el('campaign-year-options').addEventListener('change',e=>setYear(e.target.value));
    el('campaign-export-json').addEventListener('click',()=>data&&download('AETHERIS_campaign_evidence.json',JSON.stringify(data,null,2)));
    el('campaign-export-csv').addEventListener('click',csv);
    el('campaign-export-slides').addEventListener('click',slides);
  }
  window.AetherisCampaign={init};
})();
