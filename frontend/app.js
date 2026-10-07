const API = window.GOLD_API_URL || '';
const $ = (s) => document.querySelector(s);
const content = $('#content');
let meta = null, lastPrediction = null, page = 'dashboard';


// Multilingual UI: English, Telugu and Hindi. The selected language also controls the assistant.
const I18N={
  en:{Language:'Language',Dashboard:'Dashboard','AI-based gold purity estimation':'AI-based gold purity estimation','Live overview of the gold purity estimation system':'Live overview of the gold purity estimation system','Gold Sample Analysis':'Gold Sample Analysis','Run a real prediction with all three saved ML models':'Run a real prediction with all three saved ML models','Visual Analytics':'Visual Analytics','Live sample analytics plus model evaluation':'Live sample analytics plus model evaluation','Prediction History':'Prediction History','Every prediction saved by the application':'Every prediction saved by the application','Dataset Explorer':'Dataset Explorer','Complete dataset — all 1,200 rows':'Complete dataset — all 1,200 rows','Reports':'Reports','Open existing PDFs or generate a new report from a prediction':'Open existing PDFs or generate a new report from a prediction','Model & System':'Model & System','Live model configuration and comparison':'Live model configuration and comparison','Sample Comparison':'Sample Comparison','Compare two real test samples across all three models':'Compare two real test samples across all three models','Prediction Trends':'Prediction Trends','See how your saved predictions evolve over time':'See how your saved predictions evolve over time','About the Project':'About the Project','Project overview and workflow':'Project overview and workflow','System Ready':'System Ready','Backend not running':'Backend not running','AI Project Assistant':'AI Project Assistant','Project-grounded assistant':'Project-grounded assistant','Hi! Ask about the project, dataset, models, metrics, graphs, reports, or give all 8 measurements for a real prediction.':'Hi! Ask about the project, dataset, models, metrics, graphs, reports, or give all 8 measurements for a real prediction.','Ask about your project...':'Ask about your project...','Send':'Send','Thinking...':'Thinking...','Assistant error:':'Assistant error:','Density':'Density','Copper %':'Copper %','Silver %':'Silver %','Zinc %':'Zinc %','Nickel %':'Nickel %','XRF-like Gold Reading':'XRF-like Gold Reading','Temperature':'Temperature','Weight':'Weight','Reference Purity (optional)':'Reference Purity (optional)','Optional reference value':'Optional reference value','Dataset rows':'Dataset rows','Best model':'Best model','Best RMSE':'Best RMSE','Best R²':'Best R²','How it works':'How it works','Analyze a sample':'Analyze a sample','View Visual Analytics':'View Visual Analytics','Live model comparison':'Live model comparison','Sample measurements':'Sample measurements','Predict Purity':'Predict Purity','Load Dataset Sample':'Load Dataset Sample','Clear':'Clear','Current prediction':'Current prediction','All three model predictions for this sample':'All three model predictions for this sample','Sample-specific visual analysis':'Sample-specific visual analysis','Generate PDF Report':'Generate PDF Report','Current Sample Analytics':'Current Sample Analytics','Live Model Comparison':'Live Model Comparison','Feature Impact View':'Feature Impact View','Saved predictions':'Saved predictions','Export CSV':'Export CSV','New prediction':'New prediction','No predictions saved yet.':'No predictions saved yet.','Complete Dataset':'Complete Dataset','Total rows':'Total rows','Purity min':'Purity min','Purity mean':'Purity mean','Purity max':'Purity max','PDF Reports':'PDF Reports','Open PDF':'Open PDF','No generated reports yet. Run a prediction and generate a report.':'No generated reports yet. Run a prediction and generate a report.','Exact model metrics':'Exact model metrics','Selection:':'Selection:','Model':'Model','MAE':'MAE','MSE':'MSE','RMSE':'RMSE','R²':'R²','Load Two Samples':'Load Two Samples','New prediction':'New prediction','Prediction trend':'Prediction trend','Technologies':'Technologies','Workflow':'Workflow','Project note':'Project note','BEST MODEL':'BEST MODEL','Prediction for this sample':'Prediction for this sample','Selected-model predicted purity':'Selected-model predicted purity','Automatically selected model':'Automatically selected model','Reference:':'Reference:','Difference:':'Difference:','lower is better':'lower is better','higher is better':'higher is better'},
  te:{Language:'భాష',Dashboard:'డాష్‌బోర్డ్','AI-based gold purity estimation':'AI ఆధారిత బంగారం స్వచ్ఛత అంచనా','Live overview of the gold purity estimation system':'బంగారం స్వచ్ఛత అంచనా వ్యవస్థ యొక్క ప్రత్యక్ష అవలోకనం','Gold Sample Analysis':'బంగారం నమూనా విశ్లేషణ','Run a real prediction with all three saved ML models':'మూడు సేవ్ చేసిన ML మోడళ్లతో నిజమైన అంచనా చేయండి','Visual Analytics':'విజువల్ విశ్లేషణ','Live sample analytics plus model evaluation':'నమూనా విశ్లేషణ మరియు మోడల్ మూల్యాంకనం','Prediction History':'అంచనా చరిత్ర','Every prediction saved by the application':'అప్లికేషన్ సేవ్ చేసిన అన్ని అంచనాలు','Dataset Explorer':'డేటాసెట్ పరిశీలన','Complete dataset — all 1,200 rows':'పూర్తి డేటాసెట్ — మొత్తం 1,200 వరుసలు','Reports':'నివేదికలు','Open existing PDFs or generate a new report from a prediction':'ఇప్పటికే ఉన్న PDFలను తెరవండి లేదా అంచనా నుండి కొత్త నివేదిక రూపొందించండి','Model & System':'మోడల్ & సిస్టమ్','Live model configuration and comparison':'మోడల్ కాన్ఫిగరేషన్ మరియు పోలిక','Sample Comparison':'నమూనా పోలిక','Compare two real test samples across all three models':'మూడు మోడళ్లతో రెండు నిజమైన టెస్ట్ నమూనాలను పోల్చండి','Prediction Trends':'అంచనా ట్రెండ్లు','See how your saved predictions evolve over time':'సేవ్ చేసిన అంచనాలు కాలక్రమంలో ఎలా మారుతున్నాయో చూడండి','About the Project':'ప్రాజెక్ట్ గురించి','Project overview and workflow':'ప్రాజెక్ట్ అవలోకనం మరియు వర్క్‌ఫ్లో','System Ready':'సిస్టమ్ సిద్ధంగా ఉంది','Backend not running':'బ్యాక్‌ఎండ్ నడవడం లేదు','AI Project Assistant':'AI ప్రాజెక్ట్ సహాయకుడు','Project-grounded assistant':'ప్రాజెక్ట్ సమాచారం ఆధారిత సహాయకుడు','Hi! Ask about the project, dataset, models, metrics, graphs, reports, or give all 8 measurements for a real prediction.':'నమస్కారం! ప్రాజెక్ట్, డేటాసెట్, మోడళ్లు, మెట్రిక్స్, గ్రాఫ్‌లు, నివేదికలు గురించి అడగండి లేదా నిజమైన అంచనా కోసం 8 కొలతలు ఇవ్వండి.','Ask about your project...':'మీ ప్రాజెక్ట్ గురించి అడగండి...','Send':'పంపండి','Thinking...':'ఆలోచిస్తున్నాను...','Assistant error:':'సహాయకుడి లోపం:','Density':'సాంద్రత','Copper %':'రాగి %','Silver %':'వెండి %','Zinc %':'జింక్ %','Nickel %':'నికెల్ %','XRF-like Gold Reading':'XRF తరహా బంగారం రీడింగ్','Temperature':'ఉష్ణోగ్రత','Weight':'బరువు','Reference Purity (optional)':'రిఫరెన్స్ స్వచ్ఛత (ఐచ్ఛికం)','Optional reference value':'ఐచ్ఛిక రిఫరెన్స్ విలువ','Dataset rows':'డేటాసెట్ వరుసలు','Best model':'ఉత్తమ మోడల్','Best RMSE':'ఉత్తమ RMSE','Best R²':'ఉత్తమ R²','How it works':'ఇది ఎలా పనిచేస్తుంది','Analyze a sample':'నమూనాను విశ్లేషించండి','View Visual Analytics':'విజువల్ విశ్లేషణ చూడండి','Live model comparison':'మోడళ్ల ప్రత్యక్ష పోలిక','Sample measurements':'నమూనా కొలతలు','Predict Purity':'స్వచ్ఛత అంచనా వేయండి','Load Dataset Sample':'డేటాసెట్ నమూనా లోడ్ చేయండి','Clear':'క్లియర్','Current prediction':'ప్రస్తుత అంచనా','All three model predictions for this sample':'ఈ నమూనాకు మూడు మోడళ్ల అంచనాలు','Sample-specific visual analysis':'నమూనా ఆధారిత దృశ్య విశ్లేషణ','Generate PDF Report':'PDF నివేదిక రూపొందించండి','Current Sample Analytics':'ప్రస్తుత నమూనా విశ్లేషణ','Live Model Comparison':'మోడళ్ల ప్రత్యక్ష పోలిక','Feature Impact View':'ఫీచర్ ప్రభావం','Saved predictions':'సేవ్ చేసిన అంచనాలు','Export CSV':'CSV ఎగుమతి','New prediction':'కొత్త అంచనా','No predictions saved yet.':'ఇంకా అంచనాలు సేవ్ కాలేదు.','Complete Dataset':'పూర్తి డేటాసెట్','Total rows':'మొత్తం వరుసలు','Purity min':'కనిష్ట స్వచ్ఛత','Purity mean':'సగటు స్వచ్ఛత','Purity max':'గరిష్ట స్వచ్ఛత','PDF Reports':'PDF నివేదికలు','Open PDF':'PDF తెరవండి','No generated reports yet. Run a prediction and generate a report.':'ఇంకా నివేదికలు లేవు. ముందుగా అంచనా చేసి నివేదిక రూపొందించండి.','Exact model metrics':'ఖచ్చితమైన మోడల్ మెట్రిక్స్','Selection:':'ఎంపిక:','Model':'మోడల్','MAE':'MAE','MSE':'MSE','RMSE':'RMSE','R²':'R²','Load Two Samples':'రెండు నమూనాలు లోడ్ చేయండి','Prediction trend':'అంచనా ట్రెండ్','Technologies':'టెక్నాలజీలు','Workflow':'వర్క్‌ఫ్లో','Project note':'ప్రాజెక్ట్ గమనిక','BEST MODEL':'ఉత్తమ మోడల్','Prediction for this sample':'ఈ నమూనా అంచనా','Selected-model predicted purity':'ఎంచుకున్న మోడల్ అంచనా స్వచ్ఛత','Automatically selected model':'స్వయంచాలకంగా ఎంచుకున్న మోడల్','Reference:':'రిఫరెన్స్:','Difference:':'తేడా:','lower is better':'తక్కువ అయితే మంచిది','higher is better':'ఎక్కువ అయితే మంచిది'},
  hi:{Language:'भाषा',Dashboard:'डैशबोर्ड','AI-based gold purity estimation':'AI आधारित सोने की शुद्धता अनुमान','Live overview of the gold purity estimation system':'सोने की शुद्धता अनुमान प्रणाली का लाइव अवलोकन','Gold Sample Analysis':'सोने के नमूने का विश्लेषण','Run a real prediction with all three saved ML models':'तीनों सेव किए गए ML मॉडलों से वास्तविक अनुमान करें','Visual Analytics':'दृश्य विश्लेषण','Live sample analytics plus model evaluation':'नमूना विश्लेषण और मॉडल मूल्यांकन','Prediction History':'अनुमान इतिहास','Every prediction saved by the application':'एप्लिकेशन द्वारा सेव किए गए सभी अनुमान','Dataset Explorer':'डेटासेट एक्सप्लोरर','Complete dataset — all 1,200 rows':'पूरा डेटासेट — सभी 1,200 पंक्तियाँ','Reports':'रिपोर्ट','Open existing PDFs or generate a new report from a prediction':'मौजूदा PDF खोलें या अनुमान से नई रिपोर्ट बनाएं','Model & System':'मॉडल और सिस्टम','Live model configuration and comparison':'मॉडल कॉन्फ़िगरेशन और तुलना','Sample Comparison':'नमूना तुलना','Compare two real test samples across all three models':'तीनों मॉडलों से दो वास्तविक टेस्ट नमूनों की तुलना करें','Prediction Trends':'अनुमान ट्रेंड','See how your saved predictions evolve over time':'समय के साथ सेव किए गए अनुमानों को देखें','About the Project':'प्रोजेक्ट के बारे में','Project overview and workflow':'प्रोजेक्ट अवलोकन और वर्कफ़्लो','System Ready':'सिस्टम तैयार है','Backend not running':'बैकएंड नहीं चल रहा','AI Project Assistant':'AI प्रोजेक्ट सहायक','Project-grounded assistant':'प्रोजेक्ट जानकारी आधारित सहायक','Hi! Ask about the project, dataset, models, metrics, graphs, reports, or give all 8 measurements for a real prediction.':'नमस्ते! प्रोजेक्ट, डेटासेट, मॉडल, मेट्रिक्स, ग्राफ़ और रिपोर्ट के बारे में पूछें या वास्तविक अनुमान के लिए 8 माप दें।','Ask about your project...':'अपने प्रोजेक्ट के बारे में पूछें...','Send':'भेजें','Thinking...':'सोच रहा हूँ...','Assistant error:':'सहायक त्रुटि:','Density':'घनत्व','Copper %':'तांबा %','Silver %':'चाँदी %','Zinc %':'जस्ता %','Nickel %':'निकेल %','XRF-like Gold Reading':'XRF जैसा सोना रीडिंग','Temperature':'तापमान','Weight':'वजन','Reference Purity (optional)':'संदर्भ शुद्धता (वैकल्पिक)','Optional reference value':'वैकल्पिक संदर्भ मान','Dataset rows':'डेटासेट पंक्तियाँ','Best model':'सर्वश्रेष्ठ मॉडल','Best RMSE':'सर्वश्रेष्ठ RMSE','Best R²':'सर्वश्रेष्ठ R²','How it works':'यह कैसे काम करता है','Analyze a sample':'नमूने का विश्लेषण करें','View Visual Analytics':'दृश्य विश्लेषण देखें','Live model comparison':'लाइव मॉडल तुलना','Sample measurements':'नमूना माप','Predict Purity':'शुद्धता का अनुमान लगाएँ','Load Dataset Sample':'डेटासेट नमूना लोड करें','Clear':'साफ करें','Current prediction':'वर्तमान अनुमान','All three model predictions for this sample':'इस नमूने के लिए तीनों मॉडल अनुमान','Sample-specific visual analysis':'नमूना आधारित दृश्य विश्लेषण','Generate PDF Report':'PDF रिपोर्ट बनाएं','Current Sample Analytics':'वर्तमान नमूना विश्लेषण','Live Model Comparison':'लाइव मॉडल तुलना','Feature Impact View':'फीचर प्रभाव','Saved predictions':'सेव किए गए अनुमान','Export CSV':'CSV निर्यात','New prediction':'नया अनुमान','No predictions saved yet.':'अभी कोई अनुमान सेव नहीं है।','Complete Dataset':'पूरा डेटासेट','Total rows':'कुल पंक्तियाँ','Purity min':'न्यूनतम शुद्धता','Purity mean':'औसत शुद्धता','Purity max':'अधिकतम शुद्धता','PDF Reports':'PDF रिपोर्ट','Open PDF':'PDF खोलें','No generated reports yet. Run a prediction and generate a report.':'अभी कोई रिपोर्ट नहीं है। अनुमान चलाकर रिपोर्ट बनाएं।','Exact model metrics':'सटीक मॉडल मेट्रिक्स','Selection:':'चयन:','Model':'मॉडल','MAE':'MAE','MSE':'MSE','RMSE':'RMSE','R²':'R²','Load Two Samples':'दो नमूने लोड करें','Prediction trend':'अनुमान ट्रेंड','Technologies':'तकनीक','Workflow':'वर्कफ़्लो','Project note':'प्रोजेक्ट नोट','BEST MODEL':'सर्वश्रेष्ठ मॉडल','Prediction for this sample':'इस नमूने का अनुमान','Selected-model predicted purity':'चयनित मॉडल की अनुमानित शुद्धता','Automatically selected model':'स्वचालित रूप से चुना गया मॉडल','Reference:':'संदर्भ:','Difference:':'अंतर:','lower is better':'कम होना बेहतर है','higher is better':'अधिक होना बेहतर है'}
};
let language=localStorage.getItem('goldLanguage')||'en';
function t(text){return (I18N[language]&&I18N[language][text])||I18N.en[text]||text;}
const NAV_KEYS=['Dashboard','Sample Analysis','Visual Analytics','Sample Comparison','Prediction Trends','Prediction History','Dataset Explorer','Reports','Model & System','About'];
function applyTranslations(){
  document.documentElement.lang=language==='te'?'te-IN':language==='hi'?'hi-IN':'en';
  const sel=$('#language-select'); if(sel) sel.value=language;
  const ll=$('#language-label'); if(ll) ll.textContent=t('Language');
  document.querySelectorAll('#nav button span').forEach((el,i)=>el.textContent=t(NAV_KEYS[i]));
  const walker=document.createTreeWalker(document.querySelector('#content'),NodeFilter.SHOW_TEXT); const nodes=[]; let n; while(n=walker.nextNode()) nodes.push(n); nodes.forEach(x=>{const v=x.nodeValue.trim();if(v&&t(v)!==v)x.nodeValue=x.nodeValue.replace(v,t(v));});
  $('#ai-title').textContent=t('AI Project Assistant'); $('#ai-subtitle').textContent=t('Project-grounded assistant'); $('#ai-input').placeholder=t('Ask about your project...'); $('#ai-send').textContent=t('Send');
}
function setLanguage(l){language=l;localStorage.setItem('goldLanguage',l);document.documentElement.lang=l==='te'?'te-IN':l==='hi'?'hi-IN':'en';renderAssistantGreeting(); if(page) go(page);}
function renderAssistantGreeting(){const box=$('#ai-messages');if(!box)return; const greeting=t('Hi! Ask about the project, dataset, models, metrics, graphs, reports, or give all 8 measurements for a real prediction.'); if(!box.children.length){addMsg(greeting,'bot');} else if(box.children.length===1 && box.children[0].classList.contains('bot')){const span=box.children[0].querySelector('span');if(span)span.textContent=greeting; const b=box.children[0].querySelector('.msg-speaker');if(b)b.onclick=()=>speakText(greeting,b);}}

const fields = [
  ['density','Density','g/cm³'], ['copper_percent','Copper %','%'],
  ['silver_percent','Silver %','%'], ['zinc_percent','Zinc %','%'],
  ['nickel_percent','Nickel %','%'], ['xrf_gold_reading','XRF-like Gold Reading','%'],
  ['temperature','Temperature','°C'], ['weight','Weight','g']
];

async function api(path, opt = {}) {
  const r = await fetch(API + path, opt);
  const d = await r.json().catch(() => ({error:'Invalid server response'}));
  if (!r.ok) throw Error(d.error || 'Request failed');
  return d;
}
function setStatus(text, bad=false){ $('#status').textContent = `● ${text}`; $('#status').classList.toggle('bad', bad); }
function shell(title, sub){ $('#title').textContent=t(title); $('#subtitle').textContent=t(sub); document.querySelectorAll('#nav button').forEach(b=>b.classList.toggle('active',b.dataset.page===page)); applyTranslations(); }
function metric(label,val){ return `<div class="metric"><small>${label}</small><strong>${val}</strong></div>`; }
function esc(v){return String(v??'').replace(/[&<>"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));}
function downloadCsv(rows,name){if(!rows?.length)return;const keys=Object.keys(rows[0]);const csv=[keys,...rows.map(r=>keys.map(k=>String(r[k]??'').replace(/"/g,'""')))].map(r=>r.map(v=>`"${v}"`).join(',')).join('\n');const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv'}));a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),500);}

function formHtml(){ return `<div class="formgrid">${fields.map(([k,l,u])=>{const f=meta.features[k];return `<div class="field"><label>${t(l)}</label><input id="f_${k}" type="number" step="any" min="${f.minimum}" max="${f.maximum}" placeholder="${f.minimum}–${f.maximum}"><div class="hint">${f.minimum} to ${f.maximum} ${u}</div></div>`}).join('')}</div><div class="field" style="margin-top:14px"><label>${t('Reference Purity (optional)')}</label><input id="f_reference" type="number" step="any" min="0" max="100" placeholder="${t('Optional reference value')}"></div>`; }
function readInputs(){ const o={}; fields.forEach(([k])=>o[k]=$(`#f_${k}`).value); return o; }
function fillInputs(o){ fields.forEach(([k])=>{if(o[k]!==undefined) $(`#f_${k}`).value=o[k];}); }
function showErr(x){ $('#form-errors').innerHTML=`<div class="error">${x}</div>`; }

function predictionCards(p){
  const preds=p.all_model_predictions || {[p.model_name]:Number(p.predicted_purity)};
  return `<div class="model-predictions">${Object.entries(preds).map(([name,value])=>`<div class="model-prediction ${name===p.model_name?'selected':''}"><div><b>${name}</b>${name===p.model_name?'<span class="best-badge">BEST MODEL</span>':''}</div><strong>${Number(value).toFixed(2)}%</strong><small>Prediction for this sample</small></div>`).join('')}</div>`;
}
function purityGauge(p){
  const ref=p.reference_purity==null?null:Number(p.reference_purity);
  const refPart=ref==null?'':`<div class="muted">Reference: <b>${ref.toFixed(2)}%</b> · Difference: <b>${Number(p.difference).toFixed(2)}%</b></div>`;
  return `<div class="result"><div><div class="muted">Selected-model predicted purity</div><div class="purity">${Number(p.predicted_purity).toFixed(2)}%</div>${refPart}</div><div><b>${p.model_name}</b><div class="muted">Automatically selected model</div></div></div>`;
}
function featureBars(inputs){
  return `<div class="bars">${fields.map(([k,l])=>{const f=meta.features[k],v=Number(inputs[k]);const pct=Math.max(0,Math.min(100,(v-f.minimum)/(f.maximum-f.minimum)*100));return `<div class="barrow"><span>${l}</span><div class="bartrack"><div class="barfill" style="width:${pct}%"></div></div><b>${v.toFixed(2)}</b></div>`}).join('')}</div>`;
}
function modelPredictionBars(preds){
  const values=Object.values(preds).map(Number), max=Math.max(100,...values);
  return `<div class="live-bars">${Object.entries(preds).map(([name,value])=>`<div class="live-bar-row"><div class="live-bar-head"><span>${name}</span><b>${Number(value).toFixed(2)}%</b></div><div class="live-bar-track"><div class="live-bar-fill" style="width:${Math.max(0,Math.min(100,Number(value)/max*100))}%"></div></div></div>`).join('')}</div>`;
}
function metricBars(metrics){
  const models=metrics.models||{};
  const keys=[['mae','MAE','lower is better'],['rmse','RMSE','lower is better'],['r2','R²','higher is better']];
  return `<div class="metric-charts">${keys.map(([key,label,desc])=>{const vals=Object.entries(models).map(([n,v])=>[n,Number(v[key])]);const max=Math.max(...vals.map(x=>x[1]),1);return `<div class="mini-chart"><h4>${label}</h4><small>${desc}</small>${vals.map(([n,v])=>`<div class="mini-row"><span>${n}</span><div class="mini-track"><div class="mini-fill ${n===metrics.best_model?'best':''}" style="width:${v/max*100}%"></div></div><b>${v.toFixed(4)}</b></div>`).join('')}</div>`}).join('')}</div>`;
}

async function renderDashboard(){
  shell('Dashboard','Live overview of the gold purity estimation system');
  const m=meta.metrics.models,b=meta.metrics.best_model;
  content.innerHTML=`<div class="grid"><div class="span12"><div class="cards4">${metric('Dataset rows',meta.metrics.dataset_rows||1200)}${metric('Best model',b)}${metric('Best RMSE',Number(m[b].rmse).toFixed(4))}${metric('Best R²',Number(m[b].r2).toFixed(4))}</div></div><div class="span8 card"><h3>How it works</h3><p class="muted">Enter eight measurements. The backend validates them, runs the saved ML pipelines, compares all three algorithms and records the selected-model result.</p><div class="actions"><button class="btn gold" onclick="go('analysis')">Analyze a sample</button><button class="btn primary" onclick="go('analytics')">View Visual Analytics</button></div></div><div class="span4 card"><h3>Live model comparison</h3>${metricBars(meta.metrics)}</div></div>`;
}

async function renderAnalysis(){
  shell('Gold Sample Analysis','Run a real prediction with all three saved ML models');
  content.innerHTML=`<div class="grid"><div class="span6 card"><h3>Sample measurements</h3><p class="muted">All values are validated using the project's existing rules.</p><div id="form-errors"></div>${formHtml()}<div class="actions" style="margin-top:16px"><button class="btn gold" id="predict">Predict Purity</button><button class="btn primary" id="sample">Load Dataset Sample</button><button class="btn" id="clear">Clear</button></div></div><div class="span6 card"><h3>Current prediction</h3><div id="prediction"><div class="empty">Enter values and click Predict Purity.</div></div></div><div class="span12 card"><h3>All three model predictions for this sample</h3><div id="model-predictions"><div class="empty">Predictions from Linear Regression, Decision Tree and Random Forest will appear here.</div></div></div><div class="span12 card"><h3>Sample-specific visual analysis</h3><div id="sample-chart" class="empty">These visuals are generated from the current sample after prediction.</div></div></div>`;
  $('#predict').onclick=predict;
  $('#sample').onclick=async()=>{try{const d=await api('/api/sample');fillInputs(d.inputs);$('#f_reference').value=d.reference_purity}catch(e){showErr(e.message)}};
  $('#clear').onclick=()=>{fields.forEach(([k])=>$('#f_'+k).value='');$('#f_reference').value='';$('#prediction').innerHTML='<div class="empty">Enter values and click Predict Purity.</div>';$('#model-predictions').innerHTML='<div class="empty">No current sample.</div>';$('#sample-chart').innerHTML='<div class="empty">No current sample.</div>';lastPrediction=null;localStorage.removeItem('goldLastPrediction');};
}

async function predict(){
  try{
    $('#form-errors').innerHTML='';
    const ref=$('#f_reference').value;
    lastPrediction=await api('/api/predict',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({inputs:readInputs(),reference_purity:ref})});
    localStorage.setItem('goldLastPrediction',JSON.stringify(lastPrediction));
    $('#prediction').innerHTML=purityGauge(lastPrediction)+(lastPrediction.warnings||[]).map(w=>`<div class="warning">${w}</div>`).join('')+`<div class="actions" style="margin-top:12px"><button class="btn purple" onclick="makeReport()">Generate PDF Report</button></div>`;
    $('#model-predictions').innerHTML=predictionCards(lastPrediction);
    $('#sample-chart').innerHTML=`<div class="sample-analytics-grid"><div><h4>Input feature values — this sample</h4>${featureBars(lastPrediction.inputs)}</div><div><h4>Model predictions — this sample</h4>${modelPredictionBars(lastPrediction.all_model_predictions)}</div></div>`;
    setStatus('Prediction completed');
  }catch(e){showErr(e.message);setStatus('Prediction error',true)}
}
async function makeReport(){try{const d=await api('/api/report',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({inputs:lastPrediction.inputs,reference_purity:lastPrediction.reference_purity})});window.open(API+d.url,'_blank')}catch(e){alert(e.message)}}

function currentSampleAnalytics(p){
  if(!p)return `<div class="span12 card"><h3>Current Sample Analytics</h3><div class="empty">No prediction yet. Make a prediction and return here. The sample visuals will update to that exact sample.</div></div>`;
  return `<div class="span12 card"><div class="actions" style="justify-content:space-between"><div><h3>Current Sample Analytics</h3><p class="muted">These visuals are generated from the latest actual sample input and all three model predictions.</p></div><div class="sample-purity">${Number(p.predicted_purity).toFixed(2)}%</div></div><div class="sample-analytics-grid"><div><h4>Input feature values</h4>${featureBars(p.inputs)}</div><div><h4>Three-model prediction comparison</h4>${modelPredictionBars(p.all_model_predictions||{[p.model_name]:p.predicted_purity})}</div></div></div>`;
}

async function renderAnalytics(){
  shell('Visual Analytics','Live sample analytics plus model evaluation');
  let p=lastPrediction; try{if(!p){const saved=localStorage.getItem('goldLastPrediction');if(saved)p=JSON.parse(saved)}}catch(_){ }
  const g=await api('/api/graphs'); const insight=await api('/api/insights');
  content.innerHTML=`<div class="grid">${currentSampleAnalytics(p)}<div class="span12 card"><h3>Live Model Comparison</h3><p class="muted">This chart is rendered from the current saved metrics each time the page loads. Metric values change when the model is retrained or the dataset/model configuration changes.</p>${metricBars(meta.metrics)}</div><div class="span12 card"><h3>Feature Impact View</h3><p class="muted">Pearson correlation with dataset purity; this is an exploratory relationship, not a causal claim.</p>${insight.correlations.map(x=>`<div class="impact-row"><span>${x.label}</span><div class="impact-track"><span style="width:${Math.min(100,Math.abs(x.correlation)*100)}%"></span></div><b>${x.correlation.toFixed(3)}</b></div>`).join('')}</div>${g.graphs.filter(x=>x.label!=='Model Comparison').map(x=>`<div class="span6 card"><h3>${x.label}</h3><div class="chart"><img src="${API}/graphs/${encodeURIComponent(x.file)}" alt="${x.label}"></div></div>`).join('')}</div>`;
}

async function renderHistory(){
  shell('Prediction History','Every prediction saved by the application'); const d=await api('/api/history'); let rows=d.rows;
  window.currentHistory=rows; content.innerHTML=`<div class="grid"><div class="span12 card"><div class="actions" style="justify-content:space-between"><div><h3>Saved predictions (${d.count})</h3><p class="muted">This table updates after every real prediction.</p></div><div class="actions"><button class="btn primary" onclick="downloadCsv(window.currentHistory,'prediction_history.csv')">Export CSV</button><button class="btn primary" onclick="go('analysis')">New prediction</button></div></div>${rows.length?`<div class="tablewrap"><table><thead><tr>${Object.keys(rows[0]).map(k=>`<th>${k}</th>`).join('')}</tr></thead><tbody>${rows.slice().reverse().map(r=>`<tr>${Object.values(r).map(v=>`<td>${v}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`:'<div class="empty">No predictions saved yet.</div>'}</div></div>`;
}

async function renderDataset(){
  shell('Dataset Explorer','Complete dataset — all 1,200 rows'); const d=await api('/api/dataset');
  content.innerHTML=`<div class="grid"><div class="span4 card">${metric('Total rows',d.rows)}${metric('Purity min',d.purity.min.toFixed(2)+'%')}${metric('Purity mean',d.purity.mean.toFixed(2)+'%')}${metric('Purity max',d.purity.max.toFixed(2)+'%')}</div><div class="span12 card"><div class="actions dataset-head"><div><h3>Complete Dataset — ${d.rows} rows</h3><p class="muted">All records from <code>data/gold_dataset.csv</code>.</p></div><div class="actions"><span class="dataset-count">${d.rows} / ${d.rows} rows loaded</span><button class="btn primary" id="export-dataset">Export CSV</button></div></div><div class="tablewrap dataset-table"><table><thead><tr><th>#</th>${d.columns.map(c=>`<th>${c}</th>`).join('')}</tr></thead><tbody>${d.preview.map((r,i)=>`<tr><td>${i+1}</td>${d.columns.map(c=>`<td>${esc(r[c])}</td>`).join('')}</tr>`).join('')}</tbody></table></div></div></div>`;
  $('#export-dataset').onclick=()=>downloadCsv(d.preview,'gold_dataset.csv');
}
async function renderReports(){shell('Reports','Open existing PDFs or generate a new report from a prediction');const d=await api('/api/reports');content.innerHTML=`<div class="grid"><div class="span12 card"><h3>PDF Reports</h3><p class="muted">Click Open to view the actual PDF in your browser.</p>${d.reports.length?d.reports.map(r=>`<div class="report"><div><b>${r.name}</b><div class="muted">${(r.size/1024).toFixed(1)} KB</div></div><a class="btn primary" href="${API+r.url}" target="_blank">Open PDF</a></div>`).join(''):'<div class="empty">No generated reports yet. Run a prediction and generate a report.</div>'}</div></div>`}
async function renderSystem(){shell('Model & System','Live model configuration and comparison');const ms=meta.metrics;content.innerHTML=`<div class="grid"><div class="span4 card"><h3>Best model</h3><h2>${ms.best_model}</h2><p class="muted">Selection: ${ms.selection_criterion}</p></div><div class="span8 card"><h3>Live model comparison</h3>${metricBars(ms)}</div><div class="span12 card"><h3>Exact model metrics</h3><div class="tablewrap"><table><thead><tr><th>Model</th><th>MAE</th><th>MSE</th><th>RMSE</th><th>R²</th></tr></thead><tbody>${Object.entries(ms.models).map(([n,v])=>`<tr><td>${n}</td><td>${v.mae.toFixed(4)}</td><td>${v.mse.toFixed(4)}</td><td>${v.rmse.toFixed(4)}</td><td>${v.r2.toFixed(4)}</td></tr>`).join('')}</tbody></table></div></div></div>`}
async function renderComparison(){
  shell('Sample Comparison','Compare two real test samples across all three models');
  content.innerHTML=`<div class="grid"><div class="span12 card"><div class="actions"><button class="btn gold" id="load-compare">Load Two Samples</button><span class="muted">Samples are taken from the held-out test set.</span></div><div id="compare-result" class="empty">Load two samples to compare them.</div></div></div>`;
  $('#load-compare').onclick=async()=>{try{const [a,b]=await Promise.all([api('/api/sample'),api('/api/sample')]);const d=await api('/api/compare',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sample_a:a.inputs,reference_a:a.reference_purity,sample_b:b.inputs,reference_b:b.reference_purity})});$('#compare-result').innerHTML=`<div class="compare-grid">${comparisonCard('Sample A',d.a)}${comparisonCard('Sample B',d.b)}</div>`}catch(e){$('#compare-result').innerHTML=`<div class="error">${e.message}</div>`}};
}
function comparisonCard(title,p){return `<div class="card compare-card"><h3>${title}</h3><div class="sample-purity">${Number(p.predicted_purity).toFixed(2)}%</div><p class="muted">Selected: ${p.model_name}</p>${modelPredictionBars(p.all_model_predictions)}<details><summary>Measurements</summary>${featureBars(p.inputs)}</details></div>`}
async function renderTrends(){
  shell('Prediction Trends','See how your saved predictions evolve over time'); const d=await api('/api/history'); const rows=d.rows||[];
  if(!rows.length){content.innerHTML=`<div class="grid"><div class="span12 card empty">Make predictions to build a live trend chart.</div></div>`;return;}
  const vals=rows.map(r=>Number(r['Predicted Purity'])).filter(Number.isFinite), min=Math.min(...vals,0), max=Math.max(...vals,100); const span=Math.max(1,max-min);
  content.innerHTML=`<div class="grid"><div class="span12 card"><div class="actions dataset-head"><div><h3>Prediction trend</h3><p class="muted">${vals.length} saved prediction(s).</p></div><button class="btn primary" onclick="go('analysis')">New prediction</button></div><div class="trend-chart">${vals.map((v,i)=>`<div class="trend-col"><div class="trend-value">${v.toFixed(2)}%</div><div class="trend-bar"><span style="height:${Math.max(4,((v-min)/span)*100)}%"></span></div><small>#${i+1}</small></div>`).join('')}</div></div></div>`;
}
async function renderAbout(){shell('About the Project','Project overview and workflow');content.innerHTML=`<div class="grid"><div class="span12 card"><h3>${meta.title}</h3><p>${meta.subtitle}</p><h3>Technologies</h3><p>Python, Pandas, NumPy, Scikit-learn, Matplotlib, Joblib and ReportLab, with a browser-based frontend and Python API.</p><h3>Workflow</h3><p>Dataset → validation → preprocessing → Linear Regression / Decision Tree / Random Forest → evaluation → best-model selection → prediction → live sample analytics → history and PDF reporting.</p><h3>Project note</h3><p class="muted">Built as a practical AI/ML project demonstrating data-driven gold-purity estimation.</p></div></div>`}

async function go(p){page=p;try{await ({dashboard:renderDashboard,analysis:renderAnalysis,analytics:renderAnalytics,comparison:renderComparison,trends:renderTrends,history:renderHistory,dataset:renderDataset,reports:renderReports,system:renderSystem,about:renderAbout}[p]||renderDashboard)();applyTranslations()}catch(e){content.innerHTML=`<div class="error">${e.message}</div>`;setStatus(language==='te'?'API లోపం':language==='hi'?'API त्रुटि':'API error',true)}}
document.querySelectorAll('#nav button').forEach(b=>b.onclick=()=>go(b.dataset.page));

// Floating assistant: drag stays visible; click opens it; X closes only the panel.
const fab=$('#ai-fab'), panel=$('#ai-panel'); let drag=false,moved=false,ox=0,oy=0;
function openAssistant(){ fab.style.display='grid'; fab.style.visibility='visible'; fab.style.opacity='1'; panel.classList.remove('hidden'); setTimeout(()=>$('#ai-input')?.focus(),0); }
function stopSpeaking(){ if('speechSynthesis' in window){ window.speechSynthesis.cancel(); } document.querySelectorAll('.msg-speaker').forEach(b=>{b.textContent='🔊';b.classList.remove('speaking');}); }
function closeAssistant(){ stopSpeaking(); panel.classList.add('hidden'); fab.style.display='grid'; fab.style.visibility='visible'; fab.style.opacity='1'; $('#ai-input').value=''; }
fab.addEventListener('pointerdown',e=>{drag=true;moved=false;fab.setPointerCapture(e.pointerId);const r=fab.getBoundingClientRect();ox=e.clientX-r.left;oy=e.clientY-r.top});
fab.addEventListener('pointermove',e=>{if(!drag)return; if(Math.abs(e.movementX)+Math.abs(e.movementY)>2)moved=true; if(moved){fab.style.right='auto';fab.style.bottom='auto';fab.style.left=Math.max(4,Math.min(innerWidth-62,e.clientX-ox))+'px';fab.style.top=Math.max(82,Math.min(innerHeight-62,e.clientY-oy))+'px'}});
fab.addEventListener('pointerup',e=>{drag=false;fab.releasePointerCapture?.(e.pointerId);if(!moved)openAssistant();});
fab.addEventListener('pointercancel',()=>{drag=false;moved=false});
$('#ai-close').onclick=closeAssistant;

function speakText(text, button=null){
  if(!('speechSynthesis' in window)){return;}
  if(button && button.classList.contains('speaking')){ stopSpeaking(); return; }
  stopSpeaking();
  const u=new SpeechSynthesisUtterance(text);
  u.lang=(window.SPEECH_LANGS&&window.SPEECH_LANGS[language])||'en-IN';
  u.rate=.92;
  if(button){button.textContent='⏹';button.classList.add('speaking');}
  u.onend=()=>{if(button){button.textContent='🔊';button.classList.remove('speaking');}};
  u.onerror=()=>{if(button){button.textContent='🔊';button.classList.remove('speaking');}};
  window.speechSynthesis.speak(u);
}
function addMsg(t,c,id){const d=document.createElement('div');d.className='msg '+c;if(id)d.id=id;const span=document.createElement('span');span.textContent=t;d.appendChild(span);if(c==='bot' && id!=='typing'){const b=document.createElement('button');b.className='msg-speaker';b.type='button';b.title=language==='te'?'వినండి / ఆపండి':language==='hi'?'सुनें / रोकें':'Listen / Stop';b.textContent='🔊';b.onclick=()=>speakText(t,b);d.appendChild(b);}$('#ai-messages').appendChild(d);$('#ai-messages').scrollTop=999999;}

const mic=$('#ai-mic');
let recognition=null;
if(mic && ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)){const SR=window.SpeechRecognition||window.webkitSpeechRecognition; recognition=new SR(); recognition.continuous=false; recognition.interimResults=false; recognition.onstart=()=>{mic.classList.add('listening');mic.textContent='⏹';}; recognition.onend=()=>{mic.classList.remove('listening');mic.textContent='🎙';}; recognition.onerror=()=>{mic.classList.remove('listening');mic.textContent='🎙';}; recognition.onresult=e=>{$('#ai-input').value=e.results[0][0].transcript; $('#ai-form').requestSubmit();};}
if(mic){mic.onclick=()=>{if(!recognition){alert(language==='te'?'మీ Chrome బ్రౌజర్ వాయిస్ ఇన్‌పుట్‌ను మద్దతు ఇవ్వడం లేదు.':language==='hi'?'आपके Chrome ब्राउज़र में वॉइस इनपुट उपलब्ध नहीं है।':'Voice input is not supported by this browser.');return;} recognition.lang=(window.SPEECH_LANGS&&window.SPEECH_LANGS[language])||'en-IN'; recognition.start();};}
$('#ai-form').onsubmit=async e=>{e.preventDefault();const input=$('#ai-input'),q=input.value.trim();if(!q)return;addMsg(q,'user');input.value='';addMsg(t('Thinking...'),'bot','typing');try{const d=await api('/api/assistant',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q,language})});$('#typing')?.remove();addMsg(d.answer,'bot');}catch(err){$('#typing')?.remove();addMsg(t('Assistant error:')+' '+err.message,'bot');}};

$('#language-select').addEventListener('change',e=>setLanguage(e.target.value));
renderAssistantGreeting();

const mobileMenu=$('#mobile-menu'); mobileMenu.onclick=()=>document.querySelector('.sidebar').classList.toggle('open'); document.querySelectorAll('#nav button').forEach(b=>b.addEventListener('click',()=>document.querySelector('.sidebar').classList.remove('open')));

// Initialize the frontend only after the real backend metadata is loaded.
// This prevents the dashboard from trying to read meta.metrics while meta is still null.
async function initApp(){
  try{
    setStatus(language==='te'?'సిస్టమ్ సిద్ధంగా ఉంది':language==='hi'?'सिस्टम तैयार है':'System Ready');
    meta=await api('/api/meta');
    if(!meta || !meta.metrics || !meta.metrics.models) throw new Error('Backend returned incomplete model metadata.');
    await go(page);
  }catch(e){
    setStatus(language==='te'?'API లోపం':language==='hi'?'API त्रुटि':'API error',true);
    content.innerHTML=`<div class="error">${esc(e.message)}</div>`;
  }
}
initApp();
