const prompt = document.getElementById('prompt');
const buildButton = document.getElementById('buildButton');
const status = document.getElementById('status');
const openBuilder = document.getElementById('openBuilder');
const previewPanel = document.getElementById('previewPanel');
const previewFrame = document.getElementById('previewFrame');
const fileList = document.getElementById('fileList');
const workspaceTitle = document.getElementById('workspaceTitle');
const workspaceMeta = document.getElementById('workspaceMeta');
const editPrompt = document.getElementById('editPrompt');
const editButton = document.getElementById('editButton');
const editStatus = document.getElementById('editStatus');
const apiSettings = document.getElementById('apiSettings');
const apiPanel = document.getElementById('apiPanel');
const apiBaseInput = document.getElementById('apiBaseInput');
const saveApiButton = document.getElementById('saveApiButton');
const apiStatus = document.getElementById('apiStatus');

let API_BASE = (window.FIZFOX_API_BASE || '').replace(/\/$/, '');
let currentProjectId = null;

const setStatus = (element, message, busy = false, kind = '') => {
  element.textContent = message;
  element.dataset.kind = kind;
  if (element === status) {
    buildButton.disabled = busy;
    buildButton.style.opacity = busy ? '0.7' : '1';
  }
  if (element === editStatus) {
    editButton.disabled = busy;
    editButton.style.opacity = busy ? '0.7' : '1';
  }
  if (element === apiStatus) {
    saveApiButton.disabled = busy;
    saveApiButton.style.opacity = busy ? '0.7' : '1';
  }
};

async function api(path, options = {}) {
  if (!API_BASE) throw new Error('Connect your FizFox API first using the API button above.');
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: { 'Content-Type': 'application/json', ...(options.headers || {}) }
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(body.detail || `Request failed (${response.status})`);
    return body;
  } catch (error) {
    if (error instanceof Error && error.message !== 'Failed to fetch') throw error;
    throw new Error('Could not reach the FizFox API. Check the backend URL and CORS settings.');
  }
}

function renderWorkspace(project) {
  currentProjectId = project.id;
  workspaceTitle.textContent = project.spec?.name || 'Your generated app.';
  workspaceMeta.textContent = `${project.status} · ${Object.keys(project.files || {}).length} project files`;
  fileList.innerHTML = '';
  Object.keys(project.files || {}).sort().forEach((path) => {
    const item = document.createElement('div');
    item.className = 'file-item';
    item.textContent = path;
    fileList.appendChild(item);
  });
}

async function showPreview(project) {
  renderWorkspace(project);
  const preview = await api(`/api/projects/${project.id}/preview`);
  previewFrame.srcdoc = preview.html;
  previewPanel.hidden = false;
  previewPanel.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

apiSettings.addEventListener('click', () => {
  apiPanel.hidden = !apiPanel.hidden;
  if (!apiPanel.hidden) {
    apiBaseInput.value = API_BASE;
    apiBaseInput.focus();
  }
});

saveApiButton.addEventListener('click', async () => {
  const value = apiBaseInput.value.trim().replace(/\/$/, '');
  if (!value) {
    API_BASE = '';
    window.FIZFOX_API_BASE = '';
    localStorage.removeItem('fizfox_api_base');
    setStatus(apiStatus, 'API connection cleared.', false, 'success');
    return;
  }
  let url;
  try { url = new URL(value); } catch {
    setStatus(apiStatus, 'Enter a valid backend URL.', false, 'error');
    return;
  }
  if (url.protocol !== 'https:' && !['localhost', '127.0.0.1'].includes(url.hostname)) {
    setStatus(apiStatus, 'Use an HTTPS backend URL for a deployed FizFox API.', false, 'error');
    return;
  }
  setStatus(apiStatus, 'Testing connection…', true);
  try {
    const response = await fetch(`${value}/health`, { headers: { Accept: 'application/json' } });
    if (!response.ok) throw new Error();
    const health = await response.json();
    if (health.service !== 'fizfox-api') throw new Error();
    API_BASE = value;
    window.FIZFOX_API_BASE = value;
    localStorage.setItem('fizfox_api_base', value);
    setStatus(apiStatus, 'Connected to FizFox API. 🦊', false, 'success');
  } catch {
    setStatus(apiStatus, 'Connection failed. Check the URL, HTTPS and CORS settings.', false, 'error');
  }
});

document.querySelectorAll('.chip').forEach((chip) => {
  chip.addEventListener('click', () => { prompt.value = chip.dataset.prompt || ''; prompt.focus(); });
});

openBuilder.addEventListener('click', () => {
  document.getElementById('builderCard').scrollIntoView({ behavior: 'smooth', block: 'center' });
  setTimeout(() => prompt.focus(), 450);
});

buildButton.addEventListener('click', async () => {
  const value = prompt.value.trim();
  if (!value) { setStatus(status, 'Tell FizFox what you want to build first.', false, 'error'); prompt.focus(); return; }
  setStatus(status, 'Creating your project…', true);
  try {
    const project = await api('/api/projects', { method: 'POST', body: JSON.stringify({ prompt: value }) });
    setStatus(status, 'FizFox is planning your application…', true);
    await api(`/api/projects/${project.id}/plan`, { method: 'POST' });
    setStatus(status, 'Generating project files…', true);
    await api(`/api/projects/${project.id}/generate`, { method: 'POST' });
    setStatus(status, 'Building, verifying and repairing…', true);
    const built = await api(`/api/projects/${project.id}/build-and-repair`, { method: 'POST' });
    if (built.status !== 'ready') throw new Error('FizFox could not verify this project yet.');
    setStatus(status, 'Your app is ready. 🦊', false, 'success');
    await showPreview(built);
  } catch (error) {
    setStatus(status, error.message || 'Something went wrong.', false, 'error');
  }
});

async function applyEdit(instruction) {
  if (!currentProjectId) throw new Error('Build a project before asking for changes.');
  await api(`/api/projects/${currentProjectId}/edit`, { method: 'POST', body: JSON.stringify({ instruction }) });
  const built = await api(`/api/projects/${currentProjectId}/build-and-repair`, { method: 'POST' });
  if (built.status !== 'ready') throw new Error('FizFox could not verify the updated project.');
  return built;
}

editButton.addEventListener('click', async () => {
  const instruction = editPrompt.value.trim();
  if (!instruction) { setStatus(editStatus, 'Tell FizFox what you want to change.', false, 'error'); editPrompt.focus(); return; }
  setStatus(editStatus, 'Editing the existing project…', true);
  try {
    const built = await applyEdit(instruction);
    setStatus(editStatus, 'Change verified and applied. ✨', false, 'success');
    editPrompt.value = '';
    await showPreview(built);
  } catch (error) {
    setStatus(editStatus, error.message || 'Could not apply the change.', false, 'error');
  }
});
