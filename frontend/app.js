const prompt = document.getElementById('prompt');
const buildButton = document.getElementById('buildButton');
const status = document.getElementById('status');
const openBuilder = document.getElementById('openBuilder');
const previewPanel = document.getElementById('previewPanel');
const previewFrame = document.getElementById('previewFrame');

// Set this on deployment when the API lives on another origin.
// Example: window.FIZFOX_API_BASE = 'https://api.example.com';
const API_BASE = window.FIZFOX_API_BASE || '';

const setStatus = (message, busy = false, kind = '') => {
  status.textContent = message;
  status.dataset.kind = kind;
  buildButton.disabled = busy;
  buildButton.style.opacity = busy ? '0.7' : '1';
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

document.querySelectorAll('.chip').forEach((chip) => {
  chip.addEventListener('click', () => {
    prompt.value = chip.dataset.prompt || '';
    prompt.focus();
  });
});

openBuilder.addEventListener('click', () => {
  document.getElementById('builderCard').scrollIntoView({ behavior: 'smooth', block: 'center' });
  setTimeout(() => prompt.focus(), 450);
});

buildButton.addEventListener('click', async () => {
  const value = prompt.value.trim();
  if (!value) {
    setStatus('Tell FizFox what you want to build first.', false, 'error');
    prompt.focus();
    return;
  }

  setStatus('Creating your project…', true);
  try {
    const project = await api('/api/projects', {
      method: 'POST',
      body: JSON.stringify({ prompt: value })
    });

    setStatus('Planning your application…', true);
    await api(`/api/projects/${project.id}/plan`, { method: 'POST' });

    setStatus('Generating project files…', true);
    await api(`/api/projects/${project.id}/generate`, { method: 'POST' });

    setStatus('Building and verifying…', true);
    const built = await api(`/api/projects/${project.id}/build-and-repair`, { method: 'POST' });

    if (built.status !== 'ready') {
      throw new Error('FizFox could not verify this project yet.');
    }

    setStatus('Your app is ready. 🦊', false, 'success');
    const preview = await api(`/api/projects/${project.id}/preview`);
    previewFrame.srcdoc = preview.html;
    previewPanel.hidden = false;
    previewPanel.scrollIntoView({ behavior: 'smooth', block: 'center' });
  } catch (error) {
    setStatus(`${error.message || 'Something went wrong.'} Make sure the FizFox API is connected.`, false, 'error');
  }
});
