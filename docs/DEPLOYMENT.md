# FizFox Deployment

FizFox is split into a static frontend and a Python API. The frontend can run on GitHub Pages; the API should run on an HTTPS Python/Docker host.

## 1. Deploy the backend

Use the existing `backend/Dockerfile` on a container host, or run:

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

For a hosted deployment, configure:

- `PORT` — supplied by the hosting platform when applicable.
- `FIZFOX_ALLOWED_ORIGINS` — comma-separated frontend origins.
- `FIZFOX_AI_BASE_URL` — OpenAI-compatible API base URL.
- `FIZFOX_AI_API_KEY` — secret API key, supplied through the host's secret manager.
- `FIZFOX_AI_MODEL` — model identifier.
- `FIZFOX_AI_TIMEOUT` — optional request timeout in seconds.

Never commit the API key to GitHub.

## 2. Verify the API

Open:

- `/health` — basic liveness.
- `/api/system/status` — AI and sandbox capability status.

The API must be reachable over HTTPS before the GitHub Pages frontend can call it from a normal browser session.

## 3. Connect GitHub Pages

The frontend accepts the API URL through the `api` query parameter. Open the Pages URL once as:

`https://YOUR-PAGES-HOST/?api=https://YOUR-FIZFOX-API-HOST`

The browser stores that API address locally. The **API** button in the UI can also change and test the connection later.

## 4. CI

Backend tests run automatically on pushes and pull requests through `.github/workflows/backend-tests.yml`.

## 5. Security boundary

The API host must not execute generated source code directly on its own machine. The current worker path is designed around a separately managed Docker execution boundary with restricted containers. Keep the Docker daemon/socket away from generated-project containers.

The current worker performs constrained validation rather than being a finished multi-tenant live-preview platform. Production live preview still needs stronger isolation, authentication, resource quotas, cleanup, controlled ingress, observability and abuse/rate controls.
