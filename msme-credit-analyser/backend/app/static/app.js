const $=s=>document.querySelector(s);let token=localStorage.getItem('credlens_token'),currentUser=null,demos=[];
const fields=[['company_name','Company name','text','business'],['industry','Industry','select','business','Manufacturing|Retail|Wholesale|Logistics|Food Processing|Textiles|IT Services|Construction|Healthcare|Other Services'],['business_age','Business age (years)','number','business'],['employees','Employees','number','business'],['revenue','Annual revenue (INR)','number','financial'],['ebitda','EBITDA (INR)','number','financial'],['net_profit','Net profit (INR)','number','financial'],['total_assets','Total assets (INR)','number','financial'],['current_assets','Current assets (INR)','number','financial'],['current_liabilities','Current liabilities (INR)','number','financial'],['total_liabilities','Total liabilities (INR)','number','financial'],['net_worth','Net worth (INR)','number','financial'],['existing_debt','Existing debt (INR)','number','credit'],['annual_interest_expense','Annual interest expense','number','credit'],['cash_balance','Cash balance','number','credit'],['inventory','Inventory','number','credit'],['monthly_emi','Monthly EMI','number','credit'],['previous_defaults','Previous defaults','number','credit'],['credit_history_years','Credit history (years)','number','credit'],['active_loans','Active loans','number','credit'],['credit_utilization','Credit utilisation (0–1)','number','credit'],['payment_history','Payment history (0–1)','number','credit'],['avg_monthly_balance','Average bank balance','number','credit'],['monthly_inflows','Monthly inflows','number','credit'],['monthly_outflows','Monthly outflows','number','credit'],['bounced_payments','Bounced payments','number','credit'],['banking_relationship_years','Banking relationship (years)','number','credit']];
const defaults={employees:1,payment_history:.9,credit_history_years:1,banking_relationship_years:1,credit_utilization:0,active_loans:0,previous_defaults:0,bounced_payments:0,inventory:0,monthly_emi:0};
function toast(t){$('#toast').textContent=t;$('#toast').style.display='block';setTimeout(()=>$('#toast').style.display='none',3000)}
async function api(url,opts={}){opts.headers={...(opts.headers||{}),...(token?{Authorization:`Bearer ${token}`}:{})};let r=await fetch(url,opts);if(r.status===401&&token){localStorage.removeItem('credlens_token');location.reload()}if(!r.ok){let d=await r.json().catch(()=>({}));throw new Error(d.detail||'Unable to complete this request.')}return r.json()}
function renderFields(){for(const area of ['business','financial','credit']){$('#'+area+'Fields').innerHTML=fields.filter(x=>x[3]===area).map(([n,l,t,,opts])=>`<div class="field"><label>${l}</label>${t==='select'?`<select name="${n}">${opts.split('|').map(v=>`<option>${v}</option>`).join('')}</select>`:`<input required type="${t}" step="any" name="${n}" value="${defaults[n]??''}">`}</div>`).join('')}}
function setView(view){document.querySelectorAll('.view').forEach(x=>x.classList.add('hidden'));$('#'+view+'View').classList.remove('hidden');document.querySelectorAll('nav a').forEach(x=>x.classList.toggle('active',x.dataset.view===view));const copy={dashboard:['PORTFOLIO OVERVIEW',`Good morning, ${currentUser?.name?.split(' ')[0]||'Priya'}.`,`Here’s the current credit picture across your MSME portfolio.`],assessment:['UNDERWRITING WORKBENCH','New credit assessment','Turn financial evidence into an explainable credit decision.'],history:['PORTFOLIO RECORDS','Assessment history','Review previously saved MSME credit analyses.'],model:['MODEL GOVERNANCE','Model & governance','Review methodology, evaluation signals and model performance.']}[view];$('#pageKicker').textContent=copy[0];$('#pageTitle').textContent=copy[1];$('#pageSubtitle').textContent=copy[2];window.scrollTo({top:0,behavior:'smooth'})}
function riskClass(r){return r.toLowerCase()}
async function dashboard(){let d=await api('/api/dashboard');let cards=[['TOTAL ASSESSMENTS',d.total_applications,'Stored portfolio analyses'],['LOW RISK',d.risk_distribution.Low,'Eligible for approval pathway'],['MEDIUM RISK',d.risk_distribution.Medium,'Require manual review'],['AVG CREDIT SCORE',d.average_credit_score||'—','ML + ratio based score']];$('#cards').innerHTML=cards.map(x=>`<div class="card"><label>${x[0]}</label><strong>${x[1]}</strong><small>${x[2]}</small></div>`).join('');let max=Math.max(1,...Object.values(d.risk_distribution));$('#riskBars').innerHTML=Object.entries(d.risk_distribution).map(([k,v])=>`<div class="risk-bar"><span>${k} risk</span><div class="track"><div class="fill ${riskClass(k)}" style="width:${v/max*100}%"></div></div><b>${v}</b></div>`).join('');$('#recent').innerHTML=d.recent.length?d.recent.slice(0,4).map(x=>`<div class="recent-row"><div class="company-icon">${x.company.slice(0,2).toUpperCase()}</div><div><b>${x.company}</b><br><small>${x.industry} · ${x.score}/100 · ${(x.probability*100).toFixed(1)}% PD</small></div><span class="risk-pill ${riskClass(x.risk)}">${x.risk.toUpperCase()}</span></div>`).join(''):'<p class="muted">No saved assessments yet. Load a demo case to begin.</p>';$('#historydata').innerHTML=d.recent.map(x=>`<div class="table-row"><span><b>${x.company}</b></span><span>${x.industry}</span><span>${x.score}/100</span><span><i class="risk-pill ${riskClass(x.risk)}">${x.risk}</i></span><span><a href="#" data-pdf="${x.id}">PDF</a></span></div>`).join('')||'<div class="table-row"><span>No assessments saved.</span></div>';let worst=d.risk_distribution.High?'High-risk cases need immediate analyst attention.':'Portfolio has no high-risk cases in the current saved assessments.';$('#insightTitle').textContent=worst;$('#insightText').textContent=`Average default probability: ${(d.average_default_probability*100).toFixed(1)}%. Each recommendation remains subject to human underwriting review.`}
function money(v){return '₹'+Number(v||0).toLocaleString('en-IN')}
function showResult(r){let factor=(x,c)=>x.length?x.map(f=>`<div class="factor ${c}"><b>${f.feature}</b><br>${f.detail}</div>`).join(''):'<div class="factor">No material contributors identified.</div>';let ratio=Object.entries(r.ratios).map(([k,v])=>`<div class="metric">${k}<b>${v.value.toFixed(2)} ${v.healthy?'✓':'⚠'}</b></div>`).join('');$('#result').innerHTML=`<div class="result-top"><div><p class="eyebrow">ASSESSMENT COMPLETE</p><h2>${r.company}</h2></div><button class="primary" data-report="${r.assessment_id}">Download PDF report</button></div><div class="result-grid"><div><div class="score">${r.credit_score}</div><span class="risk-pill ${riskClass(r.risk_category)}">${r.risk_category.toUpperCase()} RISK</span><p>Default probability<br><b>${(r.default_probability*100).toFixed(1)}%</b></p><p><b>${r.decision}</b></p></div><div><div class="metrics"><div class="metric">RECOMMENDED LIMIT<b>${money(r.recommended_credit_limit)}</b></div><div class="metric">MAX EXPOSURE<b>${money(r.maximum_suggested_exposure)}</b></div><div class="metric">REPAYMENT CAPACITY<b>${money(r.estimated_repayment_capacity)}</b></div></div><h3 style="margin:21px 0 10px">Financial health indicators</h3><div class="metrics">${ratio}</div></div></div><div class="factors"><div><h3>Positive model contributors</h3>${factor(r.positive_factors,'')}</div><div><h3>Risk factors for review</h3>${factor(r.risk_factors,'risk')}</div></div><p class="muted">${r.methodology}</p>`;$('#result').classList.remove('hidden');$('#result').scrollIntoView({behavior:'smooth'})}
async function report(id){let r=await fetch(`/api/assessment/${id}/report.pdf`,{headers:{Authorization:`Bearer ${token}`}});if(!r.ok)return toast('Unable to generate the report.');let a=document.createElement('a');a.href=URL.createObjectURL(await r.blob());a.download=`CredLens_Assessment_${id}.pdf`;a.click();URL.revokeObjectURL(a.href)}
async function model(){let m=await api('/api/model-info');let q=k=>m.metrics?.[k]??0;$('#modeldata').innerHTML=`<article><p class="eyebrow">SELECTED PREDICTOR</p><h3>${m.model_name||'Model unavailable'}</h3><p class="muted">${m.dataset||''}</p><div class="metric-list"><div>TRAINING RECORDS<b>${m.dataset_size||0}</b></div><div>FEATURES<b>${m.features||0}</b></div><div>ROC-AUC<b>${Number(q('roc_auc')).toFixed(3)}</b></div></div></article><article><p class="eyebrow">EVALUATION SNAPSHOT</p><h3>Classification quality</h3><div class="metric-list"><div>ACCURACY<b>${Number(q('accuracy')).toFixed(3)}</b></div><div>PRECISION<b>${Number(q('precision')).toFixed(3)}</b></div><div>RECALL<b>${Number(q('recall')).toFixed(3)}</b></div><div>F1 SCORE<b>${Number(q('f1')).toFixed(3)}</b></div><div>PR-AUC<b>${Number(q('pr_auc')).toFixed(3)}</b></div><div>TRAINED<b>${String(m.training_date||'').slice(0,10)}</b></div></div><p class="muted">${m.false_negative_note||''}</p></article>`}
async function openApp(){let me=await api('/api/auth/me');currentUser=me;$('#analystName').textContent=me.name;$('#analystRole').textContent=me.role;$('#avatar').textContent=me.name.split(' ').map(x=>x[0]).join('').slice(0,2);$('#loginScreen').classList.add('hidden');$('#appShell').classList.remove('hidden');renderFields();demos=await api('/api/demo-cases');$('#demo').innerHTML+='<option disabled>────────</option>'+demos.map((x,i)=>`<option value="${i}">${x.label}</option>`).join('');await Promise.all([dashboard(),model()])}
$('#loginForm').onsubmit=async e=>{e.preventDefault();try{let d=await api('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:$('#email').value,password:$('#password').value})});token=d.access_token;localStorage.setItem('credlens_token',token);await openApp()}catch(e){$('#loginError').textContent=e.message}};
document.addEventListener('click',e=>{let view=e.target.closest('[data-view]')?.dataset.view;if(view)setView(view);let id=e.target.closest('[data-pdf]')?.dataset.pdf||e.target.closest('[data-report]')?.dataset.report;if(id){e.preventDefault();report(id)}});$('#newAssessment').onclick=()=>setView('assessment');$('#logout').onclick=async()=>{await api('/api/auth/logout',{method:'POST'}).catch(()=>{});localStorage.removeItem('credlens_token');location.reload()};$('#demo').onchange=e=>{let x=demos[e.target.value];if(!x)return;Object.entries(x).forEach(([k,v])=>{let el=$(`[name="${k}"]`);if(el)el.value=v});toast('Curated demo case loaded')};$('#template').onclick=async e=>{e.preventDefault();let r=await fetch('/api/sample-csv',{headers:{Authorization:`Bearer ${token}`}});let a=document.createElement('a');a.href=URL.createObjectURL(await r.blob());a.download='msme_upload_template.csv';a.click()};$('#form').onsubmit=async e=>{e.preventDefault();let x=Object.fromEntries(new FormData(e.target));for(let k in x)if(!['company_name','industry'].includes(k))x[k]=Number(x[k]);try{showResult(await api('/api/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(x)}));dashboard();toast('Assessment saved to portfolio')}catch(e){toast(e.message)}};$('#csv').onchange=async e=>{let f=e.target.files[0];if(!f)return;let fd=new FormData();fd.append('file',f);try{let r=await api('/api/upload-csv',{method:'POST',body:fd});toast(`Processed ${r.processed} records; ${r.errors.length} validation issues.`);dashboard();if(r.results[0])showResult(r.results[0])}catch(e){toast(e.message)}};if(token)openApp().catch(()=>localStorage.removeItem('credlens_token'));
// One-click, full-parameter borrower scenario for project demonstrations.
function loadDemoCase(index = 0) {
  const sample = demos[index];
  if (!sample) return toast('Demo cases are still loading. Please try again.');
  setView('assessment');
  Object.entries(sample).forEach(([key, value]) => {
    const input = document.querySelector(`[name="${key}"]`);
    if (input) input.value = value;
  });
  $('#demo').value = String(index);
  toast(`Loaded ${sample.company_name} with complete financial, credit and banking parameters.`);
}

document.addEventListener('click', event => {
  if (!event.target.closest('#quickDemo')) return;
  loadDemoCase(0);
  setTimeout(() => $('#form').requestSubmit(), 250);
});

const _openCredLens = openApp;
openApp = async function () {
  await _openCredLens();
  if (!document.querySelector('#quickDemo')) {
    const button = document.createElement('button');
    button.id = 'quickDemo'; button.className = 'primary';
    button.textContent = '▶ Run sample AI demo';
    document.querySelector('.header-actions').prepend(button);
  }
};

// Company-name lookup uses the NSE-listed equity universe. Private banking,
// financial-statement and credit-bureau fields remain explicitly manual/consented.
const _openCredLensWithDemo = openApp;
openApp = async function () {
  await _openCredLensWithDemo();
  if (!document.querySelector('#companyLookup')) {
    const section = document.querySelector('#assessmentView .section-title');
    section.insertAdjacentHTML('afterend', `<div id="companyLookup" class="form-section"><h3>NSE listed company lookup</h3><p class="muted">Search the NSE equity universe by company name or symbol. It fills listing identity only; bank, credit and financial fields stay manual and verified.</p><div class="lookup-row"><input id="companyQuery" placeholder="Try Reliance, Infosys, TCS, HDFCBANK or a listed-company symbol"><button class="primary" id="searchCompany" type="button">Search NSE companies</button></div><div id="companyMatches" class="lookup-results"></div></div>`);
  }
};

document.addEventListener('click', async event => {
  const searchButton = event.target.closest('#searchCompany');
  const companyOption = event.target.closest('[data-company-id]');
  if (searchButton) {
    const query = $('#companyQuery').value.trim();
    if (!query) return toast('Type a company name to search.');
    try {
      const response = await api(`/api/company-search?q=${encodeURIComponent(query)}`);
      const status = response.degraded ? ' The live NSE list is temporarily unavailable; showing the offline fallback catalogue.' : ` ${response.count.toLocaleString()} listed securities available.`;
      $('#companyMatches').innerHTML = response.results.length ? `<p class="muted">${response.source}.${status}</p>` + response.results.map(item => `<button type="button" class="company-match" data-company-id="${item.id}"><b>${item.company_name}</b><span>${item.symbol} · ${item.series} · NSE listed</span></button>`).join('') : `<p class="muted">No NSE-listed company matches this search.${status} Try a full company name or trading symbol.</p>`;
    } catch (error) { toast(error.message); }
  }
  if (companyOption) {
    try {
      const profile = await api(`/api/company-profile/${companyOption.dataset.companyId}`);
      Object.entries(profile).forEach(([key, value]) => {
        const input = document.querySelector(`[name="${key}"]`);
        if (input && value !== undefined) input.value = value;
      });
      $('#companyMatches').innerHTML = `<p class="lookup-note"><b>Profile loaded:</b> ${profile.source_note}</p>`;
      toast(`${profile.company_name} loaded. Review the public profile, then add confidential banking data if available.`);
    } catch (error) { toast(error.message); }
  }
});

