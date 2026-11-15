/* AETHERIS Scientific Quality Passport — deterministic display of server-calculated checks. */
(() => {
  'use strict';
  const el = id => document.getElementById(id);
  const h = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const num = (x, dp=3) => Number.isFinite(Number(x)) ? Number(x).toFixed(dp) : '—';
  let current = null;
  const download = (filename, content, mime) => {
    const object = URL.createObjectURL(new Blob([content], {type:mime}));
    const a = document.createElement('a');a.href=object;a.download=filename;document.body.append(a);a.click();a.remove();
    setTimeout(()=>URL.revokeObjectURL(object),5000);
  };
  function render(result) {
    const panel = el('quality-passport');
    if (!panel) return;
    const p = result?.quality_passport;
    if (!p) {panel.hidden = true;current=null;return;}
    current={passport:p,variable:result.variable.id,unit:result.trend.slope_unit,
      location:result.location,source:result.evidence,generated_at:result.generated_at};
    panel.hidden=false;
    const c=p.coverage, influence=p.influence;
    el('qp-coverage').textContent=`${num(c.monthly_percent,1)}%`;
    el('qp-years').textContent=`${c.complete_years}/${c.requested_years}`;
    el('qp-missing').textContent=String(c.expected_months-c.valid_months);
    el('qp-influence').textContent=influence.direction_stable?'Stable':'Sensitive';
    el('qp-review-status').textContent=p.review_required?'Review recommended':'No review flags';
    el('qp-review-status').dataset.state=p.review_required?'review':'complete';
    el('qp-checks').innerHTML=p.checks.map(check=>`<div class="qp-check">
      <span class="qp-indicator" data-state="${h(check.state)}" aria-hidden="true"></span>
      <div><b>${h(check.label)}</b><p>${h(check.detail)}</p></div>
      <strong>${h(check.value)}</strong>
    </div>`).join('');
    const original=Number(p.method_agreement.ols_per_decade),theil=Number(p.method_agreement.theil_sen_per_decade);
    const min=influence.minimum_slope_per_decade,max=influence.maximum_slope_per_decade;
    const magnitude=Math.max(Math.abs(min),Math.abs(max),Math.abs(original),Math.abs(theil),.01);
    const center=50, scale=42/magnitude;
    const clamp=x=>Math.max(4,Math.min(96,center+x*scale));
    const left=clamp(min),right=clamp(max);
    const axis=el('qp-range-plot');
    axis.innerHTML=`<div class="qp-axis"><span class="qp-zero" style="left:${center}%"></span>
      <span class="qp-range" style="left:${Math.min(left,right)}%;width:${Math.max(1,Math.abs(right-left))}%"></span>
      <span class="qp-dot" style="left:${clamp(original)}%" title="OLS ${h(num(original))}"></span>
      <span class="qp-diamond" style="left:${clamp(theil)}%" title="Theil–Sen ${h(num(theil))}"></span></div>`;
    el('qp-range-caption').textContent=`Leave-one-year-out range ${num(min)} to ${num(max)} ${result.trend.slope_unit} · OLS ${num(original)} · Theil–Sen ${num(theil)}`;
    const sourceHash=p.source_sha256_monthly;
    el('qp-source').textContent=`Source SHA-256: ${sourceHash.slice(0,20)}…  · ${c.valid_months}/${c.expected_months} requested months`;
    el('qp-limitations').innerHTML=p.limitations.map(text=>`<li>${h(text)}</li>`).join('');
    const monthNames=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    el('qp-month-matrix').innerHTML=`<thead><tr><th scope="col">Year</th>${monthNames.map(m=>`<th scope="col">${m}</th>`).join('')}</tr></thead><tbody>`+
      (c.monthly_matrix || []).map(row=>`<tr><th scope="row">${row.year}</th>${row.months.map((present,i)=>
        `<td class="${present?'qp-present':'qp-absent'}" title="${h(monthNames[i])} ${row.year}: ${present?'available':'missing'}" aria-label="${h(monthNames[i])} ${row.year}: ${present?'available':'missing'}"><span aria-hidden="true"></span></td>`).join('')}</tr>`).join('')+'</tbody>';
    const options = influence.leave_one_out || [];
    const picker = el('qp-omit-select');
    picker.innerHTML=options.map(item=>`<option value="${item.omitted_year}">${item.omitted_year}</option>`).join('');
    const choice=influence.most_influential_omitted_year;
    if(choice)picker.value=String(choice.omitted_year);
    const update=()=>{
      const item=options.find(x=>String(x.omitted_year)===picker.value);
      if(!item)return;
      el('qp-omitted-slope').textContent=`${item.slope_per_decade>0?'+':''}${num(item.slope_per_decade)} ${result.trend.slope_unit}`;
      const delta=item.slope_per_decade-original;
      el('qp-slope-change').textContent=`Change vs full series: ${delta>0?'+':''}${num(delta)} ${result.trend.slope_unit}`;
    };
    picker.onchange=update;update();
    el('qp-affected').textContent=c.excluded_or_unavailable_years.length?
      `Missing/incomplete calendar years: ${c.excluded_or_unavailable_years.join(', ')}.`:
      'All requested calendar years have complete usable monthly coverage.';
  }
  function setup() {
    el('qp-export')?.addEventListener('click',()=>{
      if(!current)return;
      download(`AETHERIS_Quality_Passport_${current.variable}.json`,JSON.stringify(current,null,2),'application/json;charset=utf-8');
    });
    el('qp-copy')?.addEventListener('click',async()=>{
      if(!current)return;
      const p=current.passport;
      const summary=`AETHERIS Quality Passport | ${current.variable} | ${p.period.start}–${p.period.end}\n`+
        `Coverage: ${p.coverage.valid_months}/${p.coverage.expected_months} months\n`+
        `Complete years: ${p.coverage.complete_years}/${p.coverage.requested_years}\n`+
        `OLS/Theil–Sen agreement: ${p.method_agreement.same_direction?'yes':'no'}\n`+
        `Leave-one-year-out direction stable: ${p.influence.direction_stable?'yes':'no'}\n`+
        `Review flags: ${p.review_required?'yes':'no'}\nSource SHA-256: ${p.source_sha256_monthly}\n`+
        `These are diagnostic checks, not proof of causation or model validity.`;
      try {await navigator.clipboard.writeText(summary);el('qp-copy').textContent='Copied ✓';setTimeout(()=>el('qp-copy').textContent='Copy summary',1600);}
      catch {download('AETHERIS_Quality_Summary.txt',summary,'text/plain;charset=utf-8');}
    });
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',setup);else setup();
  window.AetherisQuality={render};
})();
