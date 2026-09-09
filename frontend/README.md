# FizFox Frontend

The current frontend is a dependency-free product shell for rapid iteration. It establishes the white/purple premium visual language and the first user interaction: submitting an application idea to the backend project API.

## Run locally

From the repository root, start the backend with:

```bash
cd backend
python -m uvicorn app.main:app --reload
```

Then serve `frontend/` with any static HTTP server. The build button calls `POST /api/projects` when the frontend and API are served from compatible paths/proxy configuration.

## Design direction

- White-first canvas
- Purple as the primary accent
- Apple-inspired minimalism
- Subtle glassmorphism
- Generous whitespace
- Quiet motion and restrained shadows
- Responsive layout
