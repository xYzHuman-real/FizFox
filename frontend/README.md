# FizFox Frontend

The current frontend is a dependency-free product shell for rapid iteration. It establishes the white/purple premium visual language and the first user interaction: submitting an application idea to the backend project API.

## Run locally

From the repository root, start the backend with:

```bash
cd backend
python -m uvicorn app.main:app --reload
```

Then serve `frontend/` with any static HTTP server.

## Connect GitHub Pages to the API

The frontend is static, so the API can be hosted separately. The runtime API base URL can be supplied with the `api` query parameter:

```text
https://YOUR-PAGES-URL/?api=https://YOUR-FIZFOX-API.example.com
```

You can also tap **API** in the top navigation and paste the HTTPS backend URL. The value is saved in browser local storage for later visits. The backend must be reachable over HTTPS from the browser and must allow the frontend origin through CORS.

Do not put an AI API key in the frontend. Model credentials belong only on the backend/server side through environment variables:

- `FIZFOX_AI_BASE_URL`
- `FIZFOX_AI_API_KEY`
- `FIZFOX_AI_MODEL`
- `FIZFOX_AI_TIMEOUT`

## Backend deployment

A root `render.yaml` blueprint is included for deploying the FastAPI backend as a Render web service. Configure `FIZFOX_ALLOWED_ORIGINS` with the exact GitHub Pages origin after deployment.

## Design direction

- White-first canvas
- Purple as the primary accent
- Apple-inspired minimalism
- Subtle glassmorphism
- Generous whitespace
- Quiet motion and restrained shadows
- Responsive layout
