# FizFox backend deployment

The backend is containerized with `backend/Dockerfile` and listens on the platform-provided `PORT`.

Required AI environment variables:

- `FIZFOX_AI_BASE_URL`
- `FIZFOX_AI_API_KEY`
- `FIZFOX_AI_MODEL`

Optional:

- `FIZFOX_AI_TIMEOUT` (default `60`)
- `FIZFOX_DB_PATH` (default `/data/fizfox.db` in the container)

The API is designed to run separately from the static GitHub Pages frontend. Set the frontend runtime API base to the deployed HTTPS API origin.
