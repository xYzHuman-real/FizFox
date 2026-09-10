# FizFox API deployment

The backend is designed to run as a separate HTTPS service from the static GitHub Pages frontend.

## Container

The repository-root `Dockerfile` builds the FizFox API image. The container listens on the `PORT` environment variable and defaults to `8000`.

## Required AI environment variables

```text
FIZFOX_AI_BASE_URL=https://your-openai-compatible-provider/v1
FIZFOX_AI_API_KEY=your-secret-key
FIZFOX_AI_MODEL=your-model-name
```

Optional:

```text
FIZFOX_AI_TIMEOUT=60
FIZFOX_ALLOWED_ORIGINS=https://xYzHuman-real.github.io
```

Never put the AI API key in the frontend or commit it to Git.

## Frontend connection

The frontend accepts the public API origin through `?api=https://your-api.example.com` and stores that value locally in the browser. It can also use `window.FIZFOX_API_BASE` or the saved `fizfox_api_base` value.

The API must be served over HTTPS and must allow the GitHub Pages origin through CORS.

## Important MVP limitation

SQLite persistence is local to the backend container. For production, replace it with a managed database and persistent storage.
