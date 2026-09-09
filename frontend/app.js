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

const API_BASE = window.FIZFOX_API_BASE || '';
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
};

async function api(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) }
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || `Request failed (${response.status})`);
  return body;
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
    setStatus(status, 'Planning your application…', true);
    await api(`/api/projects/${project.id}/plan`, { method: 'POST' });
    setStatus(status, 'Generating project files…', true);
    await api(`/api/projects/${project.id}/generate`, { method: 'POST' });
    setStatus(status, 'Building and verifying…', true);
    const built = await api(`/api/projects/${project.id}/build-and-repair`, { method: 'POST' });
    if (built.status !== 'ready') throw new Error('FizFox could not verify this project yet.');
    setStatus(status, 'Your app is ready. 🦊', false, 'success');
    await showPreview(built);
  } catch (error) {
    setStatus(status, `${error.message || 'Something went wrong.'}`, false, 'error');
  }
});

editButton.addEventListener('click', async () => {
  const instruction = editPrompt.value.trim();
  if (!currentProjectId) return;
  if (!instruction) { setStatus(editStatus, 'Tell FizFox what you want to change.', false, 'error'); editPrompt.focus(); return; }
  setStatus(editStatus, 'Applying your change…', true);
  try {
    const edited = await api(`/api/projects/${currentProjectId}/edit`, {
      method: 'POST', body: JSON.stringify({ instruction })
    });
    setStatus(editStatus, 'Rebuilding and verifying…', true);
    const built = await api(`/api/projects/${currentProjectId}/build-and-repair`, { method: 'POST' });
    if (built.status !== 'ready') throw new Error('The change needs another repair pass.');
    setStatus(editStatus, 'Change applied. ✨', false, 'success');
    editPrompt.value = '';
    await showPreview(built);
  } catch (error) {
    setStatus(editStatus, `${error.message || 'Could not apply the change.'}`, false, 'error');
  }
});
