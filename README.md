# 🦊 FizFox

FizFox is an AI software-building system designed to transform natural-language ideas into working applications through planning, code generation, sandboxed execution, verification, automatic error correction, and iterative user-directed development.

## v0.1 Mission

Build the core loop first:

**Idea → Plan → Generate → Build → Verify → Preview → Iterate**

## Architecture

```text
User Prompt
    ↓
Planner
    ↓
App Specification
    ↓
Code Generator
    ↓
Project Files
    ↓
Sandbox Runtime
    ↓
Build / Verify
    ↓
Preview
    ↓
Follow-up Prompt
    └──────────────→ Modifier
```

## Repository Layout

```text
FizFox/
├── backend/          # FastAPI API and orchestration
├── frontend/         # GitHub Pages-ready product UI
├── worker/           # isolated execution worker boundary
├── docs/             # architecture and product decisions
├── Dockerfile        # backend container image
└── render.yaml       # backend deployment configuration
```

## Local Development

Backend:

```bash
cd backend
python -m uvicorn app.main:app --reload
```

The API exposes `/health` and `/api/system/status` for service/capability checks.

## AI Provider Configuration

FizFox uses an OpenAI-compatible HTTP boundary. Configure the backend environment with:

```text
FIZFOX_AI_BASE_URL=https://your-provider.example/v1
FIZFOX_AI_API_KEY=your-secret-key
FIZFOX_AI_MODEL=your-model
FIZFOX_AI_TIMEOUT=60
```

No provider credentials are stored in the repository.

## GitHub Pages + API

The frontend is static and can be hosted independently from the FastAPI backend. Open the Pages site once with the backend URL as a query parameter:

```text
?api=https://your-fizfox-api.example.com
```

FizFox remembers that API URL in the browser. The backend should use HTTPS and configure `FIZFOX_ALLOWED_ORIGINS` to the exact frontend origin in production.

## Security Boundary

Generated source is treated as untrusted. The API does not execute generated code on its own host. The worker boundary is designed for isolated container validation with network disabled, read-only project mounts, dropped capabilities, no-new-privileges, CPU/memory/process limits, and ephemeral storage.

The current worker performs constrained validation rather than acting as a production multi-tenant preview platform. Production deployment should add stronger isolation, authentication, quotas, observability, and a dedicated preview service.

## Development Principle

> **Build the engine before the cosmetics.**

Priority:

1. 🧠 Intelligence
2. ⚙️ Generation
3. 🔒 Sandbox
4. 🔍 Verification
5. 🔧 Auto-fix
6. 🎨 UI
7. 🚀 Deployment
