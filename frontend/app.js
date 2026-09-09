const prompt = document.getElementById('prompt');
const buildButton = document.getElementById('buildButton');
const status = document.getElementById('status');
const openBuilder = document.getElementById('openBuilder');

const setStatus = (message, busy = false) => {
  status.textContent = message;
  buildButton.disabled = busy;
  buildButton.style.opacity = busy ? '0.7' : '1';
};

document.querySelectorAll('.chip').forEach((chip) => {
  chip.addEventListener('click', () => {
    prompt.value = chip.dataset.prompt;
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
    setStatus('Tell FizFox what you want to build first.');
    prompt.focus();
    return;
  }

  setStatus('Creating your project…', true);
  try {
    const response = await fetch('../api/projects', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt: value })
    });

    if (!response.ok) throw new Error('API unavailable');
    const project = await response.json();
    setStatus(`Project ${project.id.slice(0, 8)} created. The planner is next. ✦`);
  } catch (error) {
    // The static frontend can still be explored when the API is not running.
    setStatus('Your idea is ready. Start the FizFox API to create the project.');
  } finally {
    buildButton.disabled = false;
    buildButton.style.opacity = '1';
  }
});
