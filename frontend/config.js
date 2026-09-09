// Runtime API configuration for the static FizFox frontend.
// Priority: ?api=... URL -> explicit global -> saved browser value -> empty.
(() => {
  const params = new URLSearchParams(window.location.search);
  const queryApi = (params.get('api') || '').trim().replace(/\/$/, '');
  if (queryApi) {
    try { localStorage.setItem('fizfox_api_base', queryApi); } catch (_) {}
  }
  let savedApi = '';
  try { savedApi = (localStorage.getItem('fizfox_api_base') || '').trim(); } catch (_) {}
  window.FIZFOX_API_BASE = (queryApi || window.FIZFOX_API_BASE || savedApi || '').replace(/\/$/, '');
})();
