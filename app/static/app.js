const state = {
  mode: 'vocal',
  jobId: null,
  pollTimer: null,
};

const genreSelect = document.getElementById('genreSelect');
const vocalStyleField = document.getElementById('vocalStyleField');
const vocalStyleSelect = document.getElementById('vocalStyleSelect');
const audioFile = document.getElementById('audioFile');
const referenceBlock = document.getElementById('referenceBlock');
const referenceFile = document.getElementById('referenceFile');
const statusLine = document.getElementById('statusLine');
const progressBar = document.getElementById('progressBar');
const progressLabel = document.getElementById('progressLabel');
const results = document.getElementById('results');

function setStatus(text) {
  statusLine.textContent = text;
}

function setProgress(value, label) {
  const pct = Math.max(0, Math.min(100, Math.round(value * 100)));
  progressBar.style.width = `${pct}%`;
  progressLabel.textContent = label || `${pct}%`;
}

function setMode(mode) {
  state.mode = mode;
  document.querySelectorAll('.tab').forEach((tab) => {
    tab.classList.toggle('is-active', tab.dataset.mode === mode);
  });
  vocalStyleField.classList.toggle('hidden', mode !== 'vocal');
  referenceBlock.classList.toggle('hidden', mode !== 'mix');
}

// Genre translation map
const genreMap = {
  'Rap/Trap': 'Rap/Trap',
  'Rap - BoomBap': 'Rap - Boom Bap',
  'Rap - Trap': 'Rap - Trap',
  'Pop': 'Pop',
  'R&B': 'R&B',
  'EDM': 'EDM',
  'EDM - Club': 'EDM - Club',
  'EDM - Chill': 'EDM - Chill',
  'House': 'House',
  'Techno': 'Techno',
  'Rock': 'Rock',
  'Metal': 'Metal',
  'Acoustic': 'Akustisk',
  'Singer-Songwriter': 'Visesang/Låtskriver',
  'Jazz': 'Jazz',
  'Lo-fi': 'Lo-fi'
};

const stageMap = {
  'queued': 'I kø',
  'ingest': 'Forbereder',
  'processing': 'Analyserer',
  'complete': 'Ferdig',
  'failed': 'Feilet'
};

function getGenreName(key) {
  return genreMap[key] || key;
}

function translateStage(stage) {
  return stageMap[stage] || stage;
}

async function loadGenres() {
  const fallback = [
    'Rap/Trap', 'Rap - BoomBap', 'Rap - Trap', 'Pop', 'R&B', 'EDM', 'EDM - Club',
    'EDM - Chill', 'House', 'Techno', 'Rock', 'Metal', 'Acoustic',
    'Singer-Songwriter', 'Jazz', 'Lo-fi'
  ];
  try {
    const response = await fetch('/api/genres');
    const data = await response.json();
    const genres = data.genres && data.genres.length ? data.genres : fallback;
    genreSelect.innerHTML = '';
    genres.forEach((genre) => {
      const opt = document.createElement('option');
      opt.value = genre;
      opt.textContent = getGenreName(genre);
      genreSelect.appendChild(opt);
    });
  } catch (err) {
    fallback.forEach((genre) => {
      const opt = document.createElement('option');
      opt.value = genre;
      opt.textContent = getGenreName(genre);
      genreSelect.appendChild(opt);
    });
  }
}

function renderResults(data) {
  results.innerHTML = '';

  const summary = document.createElement('div');
  summary.className = 'result-card';
  summary.innerHTML = `<h3>Sammendrag</h3><p>${data.summary}</p>`;
  results.appendChild(summary);

  const scoreCard = document.createElement('div');
  scoreCard.className = 'result-card';
  const scoreItems = Object.entries(data.scores || {}).map(([key, value]) => {
    // Translate score keys if needed, or keeping english terms is often acceptable in audio eng.
    const keyMap = {
      'loudness': 'Lydstyrke',
      'spectral_balance': 'Spekralbalanse',
      'stereo': 'Stereo',
      'dynamics': 'Dynamikk',
      'noise': 'Støy'
    };
    const translatedKey = keyMap[key] || key.replace('_', ' ');
    return `<div class="score"><span>${translatedKey}</span><strong>${Math.round(value)}</strong></div>`;
  }).join('');
  scoreCard.innerHTML = `<h3>Poengsum</h3><div class="score-grid">${scoreItems}</div>`;
  results.appendChild(scoreCard);

  const fixes = document.createElement('div');
  fixes.className = 'result-card';
  const recording = (data.recommendations?.recording || []).map((item) => `<li>${item}</li>`).join('');
  const mixing = (data.recommendations?.mixing || []).map((item) => `<li>${item}</li>`).join('');
  fixes.innerHTML = `
    <h3>Prioriterte tiltak</h3>
    <h4>Innspilling</h4>
    <ul class="list">${recording}</ul>
    <h4>Miksing</h4>
    <ul class="list">${mixing}</ul>
  `;
  results.appendChild(fixes);

  if (data.bpm_key) {
    const bpm = document.createElement('div');
    bpm.className = 'result-card';
    bpm.innerHTML = `
      <h3>BPM & Toneart</h3>
      <p><strong>BPM:</strong> ${data.bpm_key.bpm.toFixed(1)} (sikkerhet ${Math.round(data.bpm_key.confidence * 100)}%)</p>
      <p><strong>Toneart:</strong> ${data.bpm_key.key} (sikkerhet ${Math.round(data.bpm_key.key_confidence * 100)}%)</p>
      <p class="hint">${data.bpm_key.note || ''}</p>
    `;
    results.appendChild(bpm);
  }

  if (data.ab_compare) {
    const ab = document.createElement('div');
    ab.className = 'result-card';
    const suggestions = (data.ab_compare.match_suggestions || []).map((item) => `<li>${item}</li>`).join('');
    ab.innerHTML = `
      <h3>A/B Masteringssammenligning</h3>
      <p><strong>Loudness diff:</strong> ${data.ab_compare.loudness_diff_lufs.toFixed(1)} LUFS</p>
      <p><strong>True peak diff:</strong> ${data.ab_compare.true_peak_diff_db.toFixed(1)} dBTP</p>
      <p>${data.ab_compare.spectral_diff_summary}</p>
      <p>${data.ab_compare.stereo_diff_summary}</p>
      <p>${data.ab_compare.dynamics_diff_summary}</p>
      <h4>Forslag til match</h4>
      <ul class="list">${suggestions}</ul>
    `;
    results.appendChild(ab);
  }

  const appendix = document.createElement('details');
  appendix.className = 'details';
  appendix.innerHTML = `
    <summary>Teknisk vedlegg</summary>
    <pre>${JSON.stringify(data.metrics, null, 2)}</pre>
  `;
  results.appendChild(appendix);
}

async function pollJob(jobId) {
  try {
    const response = await fetch(`/api/jobs/${jobId}`);
    const data = await response.json();
    if (data.status === 'done') {
      setStatus('Analyse ferdig.');
      setProgress(1, 'Ferdig');
      renderResults(data.result);
      clearInterval(state.pollTimer);
      state.pollTimer = null;
      return;
    }
    if (data.status === 'failed') {
      setStatus('Analyse feilet.');
      setProgress(1, 'Feilet');
      clearInterval(state.pollTimer);
      state.pollTimer = null;
      return;
    }
    setStatus(`Prosesserer: ${translateStage(data.stage)}`);
    setProgress(data.progress || 0.2, `Steg: ${translateStage(data.stage)}`);
  } catch (err) {
    setStatus('Polling error.');
  }
}

function submitJob({ demo }) {
  const form = new FormData();
  form.append('mode', state.mode);
  form.append('genre', genreSelect.value);
  if (state.mode === 'vocal') {
    form.append('vocal_style', vocalStyleSelect.value);
  }
  if (demo) {
    form.append('demo', 'true');
  } else {
    if (!audioFile.files.length) {
      setStatus('Vennligst velg en lydfil.');
      return;
    }
    form.append('audio', audioFile.files[0]);
    if (state.mode === 'mix' && referenceFile.files.length) {
      form.append('reference', referenceFile.files[0]);
    }
  }

  setStatus('Laster opp...');
  setProgress(0.05, 'Laster opp');

  const xhr = new XMLHttpRequest();
  xhr.open('POST', '/api/jobs');
  xhr.upload.onprogress = (event) => {
    if (!event.lengthComputable) return;
    const uploadProgress = event.loaded / event.total;
    setProgress(Math.min(0.2, uploadProgress * 0.2), 'Laster opp');
  };
  xhr.onload = () => {
    if (xhr.status >= 200 && xhr.status < 300) {
      const data = JSON.parse(xhr.responseText);
      state.jobId = data.job_id;
      setStatus('I kø.');
      setProgress(0.2, 'I kø');
      if (state.pollTimer) clearInterval(state.pollTimer);
      state.pollTimer = setInterval(() => pollJob(state.jobId), 1000);
    } else {
      setStatus('Opplasting feilet.');
    }
  };
  xhr.onerror = () => setStatus('Nettverksfeil under opplasting.');
  xhr.send(form);
}

loadGenres();
setMode('vocal');

Array.from(document.querySelectorAll('.tab')).forEach((tab) => {
  tab.addEventListener('click', () => setMode(tab.dataset.mode));
});

document.getElementById('runBtn').addEventListener('click', () => submitJob({ demo: false }));
