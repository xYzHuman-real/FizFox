# FizFox API connection

FizFox keeps the browser frontend and AI backend separate. The GitHub Pages frontend must call a deployed HTTPS backend; the AI provider key must remain server-side.

## 1. Deploy the backend

The repository includes `render.yaml` and `backend/Dockerfile` for a Render web service.

Create a Render service from this repository and use the Blueprint configuration. Render will build `backend/Dockerfile` and expose `/health`.

## 2. Configure the AI provider

Set these environment variables on the backend service:

```text
FIZFOX_AI_BASE_URL=https://api.openai.com/v1
FIZFOX_AI_API_KEY=<your-secret-key>
FIZFOX_AI_MODEL=<your-model>
FIZFOX_AI_TIMEOUT=60
```

Never put the API key in `frontend/`, GitHub Pages, JavaScript, HTML, or committed source code.

FizFox uses an OpenAI-compatible `/chat/completions` interface, so the same backend boundary can support another compatible provider later.

## 3. Allow the Pages frontend

Set:

```text
FIZFOX_ALLOWED_ORIGINS=https://<your-github-pages-host>
```

Use the exact origin only, without a trailing path.

## 4. Connect GitHub Pages

The frontend reads `window.FIZFOX_API_BASE` from `frontend/config.js` and can persist a configured API base in browser storage.

Set the deployed API origin there, for example:

```javascript
window.FIZFOX_API_BASE = 'https://your-fizfox-api.example.com';
```

Do not place AI secrets here. This value is public.

## 5. Verify the connection

Open:

```text
https://<your-api-host>/health
https://<your-api-host>/api/system/status
```

The system status reports whether an AI provider is configured. A configured provider is required for model-backed planning/generation/editing; otherwise FizFox safely uses its deterministic MVP fallbacks.

## Security boundary

The browser never receives the AI provider key. Generated project code is not executed by the API host. Runtime execution belongs on the separately controlled worker/container boundary described in `worker/README.md`.
