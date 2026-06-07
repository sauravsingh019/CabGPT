// ─────────────────────────────────────────────────
// LANDING PAGE ANIMATIONS
// ─────────────────────────────────────────────────
const revealObs = new IntersectionObserver((entries) => {
  entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('visible'); revealObs.unobserve(e.target); }});
}, { threshold: 0.1 });
document.querySelectorAll('.reveal').forEach(el => revealObs.observe(el));

// Typing animation in hero demo
const phrases = ['Meerut to Delhi at 9 AM','CP se airport kitna padega?','Cheapest cab in Bangalore','Andheri to Bandra right now','Noida to Gurgaon 6 PM today'];
let pi = 0, ci = 0, deleting = false;
const chatBubble = document.querySelector('.chat-user .bubble');
if (chatBubble) {
  function type() {
    const phrase = phrases[pi];
    if (!deleting) { chatBubble.textContent = phrase.slice(0, ci + 1); ci++;
      if (ci === phrase.length) { setTimeout(() => { deleting = true; type(); }, 2000); return; }
    } else { chatBubble.textContent = phrase.slice(0, ci - 1); ci--;
      if (ci === 0) { deleting = false; pi = (pi + 1) % phrases.length; }
    }
    setTimeout(type, deleting ? 40 : 80);
  }
  setTimeout(type, 1000);
}

// Nav scroll
window.addEventListener('scroll', () => {
  const nav = document.querySelector('nav');
  if (nav) nav.style.borderBottomColor = window.scrollY > 20 ? 'rgba(255,255,255,0.08)' : 'rgba(255,255,255,0.04)';
});

// ─────────────────────────────────────────────────
// MODAL OPEN / CLOSE
// ─────────────────────────────────────────────────
const bookingModal  = document.getElementById('booking-modal');
const closeModalBtn = document.getElementById('close-modal-btn');

function openModal(e) {
  if (e) e.preventDefault();
  if (!bookingModal) return;
  bookingModal.classList.remove('hidden');
  document.body.classList.add('modal-open');
  document.documentElement.classList.add('modal-open');
}
function closeModal() {
  if (!bookingModal) return;
  bookingModal.classList.add('hidden');
  document.body.classList.remove('modal-open');
  document.documentElement.classList.remove('modal-open');
}
['hero-estimate-btn','nav-try-now','cta-open-btn'].forEach(id => {
  const el = document.getElementById(id);
  if (el) el.addEventListener('click', openModal);
});
if (closeModalBtn) closeModalBtn.addEventListener('click', closeModal);
if (bookingModal) bookingModal.addEventListener('click', e => { if (e.target === bookingModal) closeModal(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

// ─────────────────────────────────────────────────
// TAB SWITCHING
// ─────────────────────────────────────────────────
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const targetPane = btn.getAttribute('data-pane');
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.booking-pane').forEach(pane => {
      pane.classList.toggle('hidden', pane.id !== targetPane);
    });
  });
});

// ─────────────────────────────────────────────────
// LOAD OLLAMA MODELS
// ─────────────────────────────────────────────────
const ollamaModelSelect = document.getElementById('ollama-model');
async function loadOllamaModels() {
  if (!ollamaModelSelect) return;
  try {
    const res = await fetch('/api/models');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    if (data.models && data.models.length > 0) {
      ollamaModelSelect.innerHTML = '';
      data.models.forEach(model => {
        const opt = document.createElement('option');
        opt.value = model; opt.textContent = model;
        ollamaModelSelect.appendChild(opt);
      });
    } else {
      ollamaModelSelect.innerHTML = '<option value="llama3.1">llama3.1 (default)</option>';
    }
  } catch (err) {
    ollamaModelSelect.innerHTML = `<option value="llama3.1">llama3.1</option><option value="mistral">mistral</option><option value="gemma2">gemma2</option><option value="phi3">phi3</option>`;
  }
}
loadOllamaModels();

// ─────────────────────────────────────────────────
// STATE & DOM REFS
// ─────────────────────────────────────────────────
let currentTripData = null;
let selectedCabClass = null;

const agentTraceCard  = document.getElementById('agent-trace-card');
const traceLogs       = document.getElementById('trace-logs');
const stageTracker    = document.getElementById('stage-tracker');
const outputPanel     = document.getElementById('output-panel');
const activeRidePanel = document.getElementById('active-ride-panel');
const valPickup    = document.getElementById('val-pickup');
const valDrop      = document.getElementById('val-drop');
const valDatetime  = document.getElementById('val-datetime');
const valDistance  = document.getElementById('val-distance');
const valDuration  = document.getElementById('val-duration');
const valWeather   = document.getElementById('val-weather');
const mapContainer = document.getElementById('map-container');
const surgeDetails = document.getElementById('surge-details');
const cabList      = document.getElementById('cab-list');
const bookBtn      = document.getElementById('book-btn');
const activePickup   = document.getElementById('active-pickup');
const activeDrop     = document.getElementById('active-drop');
const activeCabClass = document.getElementById('active-cab-class');
const driverChatBox  = document.getElementById('driver-chat-box');
const driverChatForm = document.getElementById('driver-chat-form');
const driverMsgInput = document.getElementById('driver-msg-input');
const cancelRideBtn  = document.getElementById('cancel-ride-btn');

const stageEls = {
  nlp:     document.getElementById('stage-nlp'),
  geocode: document.getElementById('stage-geocode'),
  route:   document.getElementById('stage-route'),
  weather: document.getElementById('stage-weather'),
  surge:   document.getElementById('stage-surge'),
  engine:  document.getElementById('stage-engine'),
};

// ─────────────────────────────────────────────────
// HELPERS
// ─────────────────────────────────────────────────
function setStage(key, status) {
  const el = stageEls[key];
  if (!el) return;
  el.className = 'stage-item';
  if (status === 'active')    el.classList.add('active');
  if (status === 'completed') el.classList.add('completed');
}
function resetStages() { Object.keys(stageEls).forEach(k => setStage(k, '')); }

function logLine(msg) {
  if (!traceLogs) return;
  const div = document.createElement('div');
  div.className = 'trace-line';
  div.innerHTML = `<span class="pfx">›</span> <span>${msg}</span>`;
  traceLogs.appendChild(div);
  traceLogs.scrollTop = traceLogs.scrollHeight;
}

function resetResults() {
  if (agentTraceCard) agentTraceCard.classList.add('hidden');
  if (stageTracker)   stageTracker.classList.add('hidden');
  if (outputPanel)    outputPanel.classList.add('hidden');
  if (activeRidePanel) activeRidePanel.classList.add('hidden');
  if (traceLogs) traceLogs.innerHTML = '';
  const prevCard = document.getElementById('ai-response-card');
  if (prevCard) prevCard.style.display = 'none';
  resetStages();
}

function delay(ms) { return new Promise(r => setTimeout(r, ms)); }

// ─────────────────────────────────────────────────
// SHOW AI TEXT RESPONSE CARD
// ─────────────────────────────────────────────────
function showAIResponse(text) {
  if (!text || !text.trim()) return;
  let card = document.getElementById('ai-response-card');
  if (!card) {
    card = document.createElement('div');
    card.id = 'ai-response-card';
    card.style.cssText = `
      background: rgba(255,183,3,0.04);
      border: 1px solid rgba(255,183,3,0.18);
      border-radius: 12px;
      padding: 14px 18px;
      margin-top: 14px;
      font-size: 0.88rem;
      line-height: 1.7;
      color: #c8cce0;
      white-space: pre-wrap;
      font-family: 'Instrument Sans', sans-serif;
    `;
    const traceCard = document.getElementById('agent-trace-card');
    if (traceCard && traceCard.parentNode) {
      traceCard.parentNode.insertBefore(card, traceCard.nextSibling);
    }
  }
  card.innerHTML = `
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">
      <span style="font-size:1.1rem">🚕</span>
      <span style="font-family:'Syne',sans-serif;font-weight:700;font-size:0.78rem;color:#ffb703;letter-spacing:0.3px;text-transform:uppercase;">AI Response</span>
    </div>
    <div style="border-top:1px solid rgba(255,255,255,0.05);padding-top:10px;">${text}</div>
  `;
  card.style.display = 'block';
}

// ─────────────────────────────────────────────────
// SVG MAP
// ─────────────────────────────────────────────────
const CITY_COORDS = {
  "chandigarh": {x:180,y:50,  name:"Chandigarh"}, "meerut":    {x:320,y:130,name:"Meerut"},
  "ghaziabad":  {x:290,y:170,name:"Ghaziabad"},   "delhi":     {x:250,y:200,name:"Delhi"},
  "new delhi":  {x:250,y:200,name:"Delhi"},         "gurgaon":  {x:205,y:230,name:"Gurgaon"},
  "gurugram":   {x:205,y:230,name:"Gurugram"},      "noida":    {x:285,y:220,name:"Noida"},
  "faridabad":  {x:260,y:250,name:"Faridabad"},     "agra":     {x:350,y:315,name:"Agra"},
  "jaipur":     {x:110,y:290,name:"Jaipur"},        "lucknow":  {x:450,y:350,name:"Lucknow"},
  "bangalore":  {x:230,y:340,name:"Bangalore"},     "bengaluru":{x:230,y:340,name:"Bengaluru"},
  "mumbai":     {x:140,y:310,name:"Mumbai"},         "pune":    {x:150,y:340,name:"Pune"},
  "hyderabad":  {x:270,y:330,name:"Hyderabad"},     "chennai":  {x:280,y:370,name:"Chennai"},
};

function renderSvgMap(pickup, drop) {
  if (!mapContainer) return;
  const pKey = pickup.toLowerCase().trim();
  const dKey = drop.toLowerCase().trim();
  const pInfo = CITY_COORDS[pKey] || {x:120,y:250,name:pickup};
  const dInfo = CITY_COORDS[dKey] || {x:380,y:150,name:drop};

  let dotsSvg = '';
  Object.entries(CITY_COORDS).forEach(([city,c]) => {
    if (city !== pKey && city !== dKey)
      dotsSvg += `<circle cx="${c.x}" cy="${c.y}" r="3" fill="rgba(255,255,255,0.1)"/><text x="${c.x}" y="${c.y-7}" font-size="8" fill="rgba(255,255,255,0.25)" text-anchor="middle">${c.name}</text>`;
  });

  const mx = (pInfo.x+dInfo.x)/2, my = (pInfo.y+dInfo.y)/2-40;
  const pathD = `M ${pInfo.x} ${pInfo.y} Q ${mx} ${my} ${dInfo.x} ${dInfo.y}`;

  mapContainer.innerHTML = `
    <svg width="100%" height="220" viewBox="0 0 500 400" style="background:rgba(8,10,22,0.5);border-radius:12px;border:1px solid rgba(255,255,255,0.06)">
      <defs>
        <pattern id="g" width="20" height="20" patternUnits="userSpaceOnUse">
          <path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(255,255,255,0.012)" stroke-width="1"/>
        </pattern>
        <linearGradient id="rg" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#ffb703"/><stop offset="100%" stop-color="#fb8500"/>
        </linearGradient>
      </defs>
      <rect width="100%" height="100%" fill="url(#g)"/>
      ${dotsSvg}
      <path d="${pathD}" fill="none" stroke="url(#rg)" stroke-width="2.5" stroke-linecap="round" stroke-dasharray="5,4" style="animation:dash 1.5s linear infinite"/>
      <g><text font-size="16" x="-8" y="6">🚕</text><animateMotion dur="3.5s" repeatCount="indefinite" path="${pathD}" rotate="auto"/></g>
      <circle cx="${pInfo.x}" cy="${pInfo.y}" r="7" fill="none" stroke="#ffb703" stroke-width="1.5" opacity="0.7"><animate attributeName="r" values="3;12;3" dur="2.5s" repeatCount="indefinite"/><animate attributeName="opacity" values="0.7;0;0.7" dur="2.5s" repeatCount="indefinite"/></circle>
      <circle cx="${pInfo.x}" cy="${pInfo.y}" r="4" fill="#ffb703"/>
      <rect x="${pInfo.x-32}" y="${pInfo.y-28}" width="64" height="16" rx="4" fill="#111424" stroke="#ffb703" stroke-width="0.8"/>
      <text x="${pInfo.x}" y="${pInfo.y-17}" font-size="8" font-weight="bold" fill="#e2e4f0" text-anchor="middle">📍 ${pInfo.name.slice(0,9)}</text>
      <circle cx="${dInfo.x}" cy="${dInfo.y}" r="7" fill="none" stroke="#fb8500" stroke-width="1.5" opacity="0.7"><animate attributeName="r" values="3;12;3" dur="2.5s" repeatCount="indefinite"/><animate attributeName="opacity" values="0.7;0;0.7" dur="2.5s" repeatCount="indefinite"/></circle>
      <circle cx="${dInfo.x}" cy="${dInfo.y}" r="4" fill="#fb8500"/>
      <rect x="${dInfo.x-32}" y="${dInfo.y-28}" width="64" height="16" rx="4" fill="#111424" stroke="#fb8500" stroke-width="0.8"/>
      <text x="${dInfo.x}" y="${dInfo.y-17}" font-size="8" font-weight="bold" fill="#e2e4f0" text-anchor="middle">🏁 ${dInfo.name.slice(0,9)}</text>
    </svg>
    <style>@keyframes dash{to{stroke-dashoffset:-18}}</style>`;
}

// ─────────────────────────────────────────────────
// RENDER TRIP DASHBOARD (used by both Quick + AI)
// ─────────────────────────────────────────────────
function renderTripDashboard(tripData) {
  if (!tripData) return;
  const trip = tripData.trip || {};
  if (valPickup)   valPickup.textContent   = trip.pickup || '—';
  if (valDrop)     valDrop.textContent     = trip.drop   || '—';
  if (valDatetime) valDatetime.textContent = `${trip.date||'Today'} at ${trip.time||'Now'}`;
  if (valDistance) valDistance.textContent = `${tripData.distance||0} km`;
  if (valDuration) valDuration.textContent = tripData.duration_mins ? `${Math.round(tripData.duration_mins)} min` : '—';
  const w = tripData.weather || {};
  if (valWeather) valWeather.textContent = w.condition ? `${w.condition} ${w.temp_celsius ? Math.round(w.temp_celsius)+'°C' : ''}` : '—';

  if (trip.pickup && trip.drop) renderSvgMap(trip.pickup, trip.drop);

  const peak = tripData.peak_info || {};
  const surgeTxt = [
    peak.peak_label || '',
    peak.surge_multiplier ? `(${peak.surge_multiplier}× surge)` : '',
    w.is_raining ? '🌧️ Rain' : '☀️ Clear'
  ].filter(Boolean).join(' · ');
  if (surgeDetails) surgeDetails.textContent = surgeTxt;

  // Cab list
  const fares = (tripData.fare_data || {}).fares || {};
  const cheapestProv = (tripData.fare_data || {}).cheapest;
  const fastestProv  = (tripData.fare_data || {}).fastest;
  const filters = tripData.filters || {};
  const cabPref = (filters.cab_pref || 'Any').toLowerCase();
  const vehPref = (filters.vehicle_pref || 'Any').toLowerCase();

  if (cabList) {
    cabList.innerHTML = '';
    let first = null;
    Object.entries(fares).forEach(([provider, val]) => {
      const pLow = provider.toLowerCase();
      if (cabPref !== 'any' && !pLow.includes(cabPref)) return;
      if (vehPref !== 'any') {
        const vm = {car:['mini','go','prime'],auto:['auto'],bike:['bike']};
        if (!(vm[vehPref]||[]).some(m => pLow.includes(m))) return;
      }
      let icon = '🚗';
      if (pLow.includes('bike')) icon = '🏍️';
      else if (pLow.includes('auto')) icon = '🛺';
      const item = document.createElement('div');
      item.className = 'cab-item';
      item.dataset.provider = provider;
      if (!first) { item.classList.add('selected'); first = provider; }
      if (provider === cheapestProv) item.classList.add('cheapest-item');
      let badgesHTML = '';
      if (provider === cheapestProv) badgesHTML += `<span class="cab-badge cheapest">CHEAPEST</span>`;
      if (provider === fastestProv && provider !== cheapestProv) badgesHTML += `<span class="cab-badge fastest">FASTEST</span>`;
      item.innerHTML = `
        <div class="cab-info">
          <span class="cab-emoji">${icon}</span>
          <div class="cab-meta">
            <b>${provider} ${badgesHTML}</b>
            <p>ETA: ${val.eta} min · Surge: ${val.surge_applied}</p>
          </div>
        </div>
        <div class="cab-price">₹${val.min}–${val.max}</div>`;
      item.addEventListener('click', () => {
        document.querySelectorAll('.cab-item').forEach(el => el.classList.remove('selected'));
        item.classList.add('selected');
        selectedCabClass = provider;
      });
      cabList.appendChild(item);
    });
    if (!first) {
      cabList.innerHTML = `<div style="color:var(--muted);font-size:0.85rem;padding:10px;text-align:center">No results for selected filters. Try "Any".</div>`;
    }
    selectedCabClass = first;
  }

  if (stageTracker) stageTracker.classList.remove('hidden');
  if (outputPanel)  outputPanel.classList.remove('hidden');
}

// ─────────────────────────────────────────────────
// QUICK FORM HANDLER (no LLM — direct tools)
// ─────────────────────────────────────────────────
const quickForm       = document.getElementById('quick-form');
const quickSubmitBtn  = document.getElementById('quick-submit-btn');
const quickBtnText    = document.getElementById('quick-btn-text');
const quickBtnSpinner = document.getElementById('quick-btn-spinner');

if (quickForm) {
  quickForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const pickup  = (document.getElementById('field-pickup')?.value || '').trim();
    const drop    = (document.getElementById('field-drop')?.value   || '').trim();
    const dateVal = document.getElementById('field-date')?.value || '';
    const timeVal = document.getElementById('field-time')?.value || '';
    const cabPref = document.getElementById('field-cab-pref')?.value || 'Any';
    const vehPref = document.getElementById('field-vehicle-type')?.value || 'Any';
    if (!pickup || !drop) { alert('Please enter both pickup and destination locations.'); return; }

    let travelHour = new Date().getHours();
    if (timeVal) travelHour = parseInt(timeVal.split(':')[0], 10);
    const timeLabel = [dateVal, timeVal].filter(Boolean).join(' ') || 'Now';

    resetResults();
    if (agentTraceCard) agentTraceCard.classList.remove('hidden');
    if (stageTracker)   stageTracker.classList.remove('hidden');
    if (quickBtnText)    quickBtnText.textContent = 'Searching...';
    if (quickBtnSpinner) quickBtnSpinner.classList.remove('hidden');
    if (quickSubmitBtn)  quickSubmitBtn.disabled = true;

    logLine(`Starting quick fare: ${pickup} → ${drop}`);
    setStage('geocode', 'active');

    try {
      const res = await fetch('/api/quick_fare', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ pickup, dropoff: drop, time_preference: timeLabel, cab_pref: cabPref, vehicle_pref: vehPref, travel_hour: travelHour })
      });
      const data = await res.json();
      if (data.error) { logLine(`❌ ${data.error}`); return; }

      if (data.tool_logs && data.tool_logs.length > 0) {
        for (const log of data.tool_logs) {
          await delay(250);
          if (log.tool === 'get_coordinates') {
            setStage('geocode', 'active');
            logLine(`📍 Geocoded "${log.args.location}" → ${(log.result.lat||0).toFixed(3)}, ${(log.result.lng||0).toFixed(3)}`);
            setStage('geocode', 'completed');
          } else if (log.tool === 'get_distance_and_duration') {
            setStage('route', 'active');
            logLine(`📏 Distance: ${log.result.distance_km} km · ${Math.round(log.result.duration_minutes||log.result.duration_mins||0)} min${log.result.is_fallback?' (estimated)':''}`);
            setStage('route', 'completed');
          } else if (log.tool === 'get_weather') {
            setStage('weather', 'active');
            logLine(`🌦 Weather: ${log.result.condition||'N/A'} · ${Math.round(log.result.temp_celsius||25)}°C · Rain: ${log.result.is_raining?'Yes ⚠️':'No'}`);
            setStage('weather', 'completed');
          } else if (log.tool === 'get_peak_hour_info') {
            setStage('surge', 'active');
            logLine(`⚡ Surge: ${log.result.peak_label||'Normal'} · ${log.result.surge_multiplier||1.0}× multiplier`);
            setStage('surge', 'completed');
          } else if (log.tool === 'estimate_fare') {
            setStage('engine', 'active');
            logLine(`💰 Fares calculated across ${Object.keys(log.result.fares||{}).length} providers`);
            setStage('engine', 'completed');
          }
        }
      }

      await delay(150);
      if (data.type === 'trip_options' && data.trip_data) {
        data.trip_data.filters = { cab_pref: cabPref, vehicle_pref: vehPref };
        currentTripData = data.trip_data;
        renderTripDashboard(data.trip_data);
        logLine(`✅ Done — showing ${Object.keys((data.trip_data.fare_data||{}).fares||{}).length} fares`);
      }
    } catch (err) {
      logLine(`❌ Error: ${err.message}`);
    } finally {
      if (quickBtnText)    quickBtnText.textContent = 'Get Fares';
      if (quickBtnSpinner) quickBtnSpinner.classList.add('hidden');
      if (quickSubmitBtn)  quickSubmitBtn.disabled = false;
    }
  });
}

// ─────────────────────────────────────────────────
// AI PROMPT FORM HANDLER (uses Ollama LLM)
// ─────────────────────────────────────────────────
const aiForm       = document.getElementById('ai-form');
const aiSubmitBtn  = document.getElementById('ai-submit-btn');
const aiBtnSpinner = document.getElementById('ai-btn-spinner');
const userQuery    = document.getElementById('user-query');

if (aiForm) {
  aiForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = (userQuery?.value || '').trim();
    if (!query) return;
    const modelName = ollamaModelSelect?.value || 'llama3.1';

    resetResults();
    if (agentTraceCard) agentTraceCard.classList.remove('hidden');
    if (stageTracker)   stageTracker.classList.remove('hidden');
    if (aiSubmitBtn)    aiSubmitBtn.disabled = true;
    if (aiBtnSpinner)   aiBtnSpinner.classList.remove('hidden');
    const aiLbl = document.getElementById('ai-btn-label');
    if (aiLbl) aiLbl.textContent = 'Asking...';

    logLine(`🤖 AI Assistant · Model: ${modelName}`);
    setStage('nlp', 'active');

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ query, model_name: modelName })
      });
      const data = await res.json();

      if (data.error) { logLine(`❌ ${data.error}`); return; }

      setStage('nlp', 'completed');
      logLine('✓ NLP: intent + entities extracted');

      // Walk tool logs at 180ms per step
      if (data.tool_logs && data.tool_logs.length > 0) {
        for (const log of data.tool_logs) {
          await delay(180);
          if (log.tool === 'get_coordinates') {
            setStage('geocode', 'active');
            logLine(`📍 Geocoded "${log.args.location}" → ${(log.result.lat||0).toFixed(3)}, ${(log.result.lng||0).toFixed(3)}`);
            setStage('geocode', 'completed');
          } else if (log.tool === 'get_distance_and_duration') {
            setStage('route', 'active');
            logLine(`📏 Distance: ${log.result.distance_km} km · ${Math.round(log.result.duration_minutes||log.result.duration_mins||0)} min${log.result.is_fallback?' (estimated)':''}`);
            setStage('route', 'completed');
          } else if (log.tool === 'get_weather') {
            setStage('weather', 'active');
            logLine(`🌦 Weather: ${log.result.condition||'N/A'} · ${Math.round(log.result.temp_celsius||25)}°C · Rain: ${log.result.is_raining?'Yes ⚠️':'No'}`);
            setStage('weather', 'completed');
          } else if (log.tool === 'get_peak_hour_info') {
            setStage('surge', 'active');
            logLine(`⚡ Surge: ${log.result.peak_label||'Normal'} · ${log.result.surge_multiplier||1.0}×`);
            setStage('surge', 'completed');
          } else if (log.tool === 'estimate_fare') {
            setStage('engine', 'active');
            logLine(`💰 Fares for ${Object.keys(log.result.fares||{}).length} providers`);
            setStage('engine', 'completed');
          }
        }
      }

      await delay(200);
      setStage('engine', 'completed');

      if (data.type === 'trip_options' && data.trip_data) {
        // Show the full booking dashboard — same as Quick Search
        currentTripData = data.trip_data;
        renderTripDashboard(data.trip_data);
        logLine(`✅ Dashboard ready`);
        // Show AI's commentary as a small note below the dashboard
        if (data.response && data.response.trim().length > 0) {
          showAIResponse(data.response);
        }
      } else if (data.type === 'general') {
        // General answer (e.g. "how does surge work?")
        showAIResponse(data.response);
        logLine('✅ Response ready');
      }

    } catch (err) {
      logLine(`❌ Error: ${err.message}`);
    } finally {
      if (aiSubmitBtn)  { aiSubmitBtn.disabled = false; }
      if (aiBtnSpinner) aiBtnSpinner.classList.add('hidden');
      const lbl = document.getElementById('ai-btn-label');
      if (lbl) lbl.textContent = 'Ask';
    }
  });
}

// ─────────────────────────────────────────────────
// BOOK CAB
// ─────────────────────────────────────────────────
if (bookBtn) {
  bookBtn.addEventListener('click', async () => {
    if (!currentTripData || !selectedCabClass) return;
    bookBtn.disabled = true;
    bookBtn.textContent = 'Confirming booking...';
    await delay(1000);
    if (activePickup)   activePickup.textContent   = currentTripData.trip?.pickup || '—';
    if (activeDrop)     activeDrop.textContent     = currentTripData.trip?.drop   || '—';
    if (activeCabClass) activeCabClass.textContent = selectedCabClass;
    if (outputPanel)    outputPanel.classList.add('hidden');
    if (agentTraceCard) agentTraceCard.classList.add('hidden');
    if (stageTracker)   stageTracker.classList.add('hidden');
    const prevCard = document.getElementById('ai-response-card');
    if (prevCard) prevCard.style.display = 'none';
    if (activeRidePanel) activeRidePanel.classList.remove('hidden');
    if (driverChatBox) driverChatBox.innerHTML = `<div class="chat-bubble driver"><b>Rahul:</b> Ram Ram bhaiya! Main location ke paas hi hu, 2 minute mein aa raha hu. 🚕</div>`;
    bookBtn.disabled = false;
    bookBtn.textContent = 'Confirm & Book Ride →';
  });
}

// ─────────────────────────────────────────────────
// DRIVER CHAT
// ─────────────────────────────────────────────────
if (driverChatForm) {
  driverChatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const msg = (driverMsgInput?.value || '').trim();
    if (!msg) return;
    appendChatBubble('user', `<b>You:</b> ${msg}`);
    if (driverMsgInput) driverMsgInput.value = '';
    try {
      const res = await fetch('/api/driver_chat', {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ user_message: msg, pickup: currentTripData?.trip?.pickup||'', drop: currentTripData?.trip?.drop||'', model_name: ollamaModelSelect?.value||'llama3.1' })
      });
      const data = await res.json();
      appendChatBubble('driver', `<b>Rahul:</b> ${data.reply||'...'}`);
    } catch (err) {
      appendChatBubble('driver', `<b>Rahul:</b> Haan bhaiya, 2 minute mein aa raha hu. 🚕`);
    }
  });
}

function appendChatBubble(type, html) {
  if (!driverChatBox) return;
  const div = document.createElement('div');
  div.className = `chat-bubble ${type}`;
  div.innerHTML = html;
  driverChatBox.appendChild(div);
  driverChatBox.scrollTop = driverChatBox.scrollHeight;
}

// ─────────────────────────────────────────────────
// CANCEL RIDE
// ─────────────────────────────────────────────────
if (cancelRideBtn) {
  cancelRideBtn.addEventListener('click', () => {
    if (activeRidePanel) activeRidePanel.classList.add('hidden');
    if (outputPanel)     outputPanel.classList.remove('hidden');
    if (agentTraceCard)  agentTraceCard.classList.remove('hidden');
    if (stageTracker)    stageTracker.classList.remove('hidden');
  });
}

// ─────────────────────────────────────────────────
// DEFAULT FIELD VALUES
// ─────────────────────────────────────────────────
const fieldDate = document.getElementById('field-date');
if (fieldDate) {
  const today = new Date();
  fieldDate.value = `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,'0')}-${String(today.getDate()).padStart(2,'0')}`;
}
const fieldTime = document.getElementById('field-time');
if (fieldTime) {
  const now = new Date();
  fieldTime.value = `${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}`;
}
