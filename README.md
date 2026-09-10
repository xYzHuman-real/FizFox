# 🦊 FizFox

FizFox is an AI software-building system designed to transform natural-language ideas into applications through planning, code generation, sandboxed validation, verification, automatic error correction, iterative editing, persistence, preview, and export.

## v0.1 Core Loop

**Idea → Plan → Generate → Build → Verify → Repair → Preview → Edit → Export**

## Architecture

```text
User Prompt
    ↓
AI / Heuristic Planner
    ↓
AppSpec
    ↓
AI / Heuristic Generator
    ↓
Project Files
    ↓
Safe Runtime Boundary
    ↓
Verifier
    ↓
Bounded Repair
    ↓
Safe Static Preview
    ↓
Follow-up Edit
    └──────────────→ same project
```

## Repository Layout

```text
FizFox/
├── backend/          # FastAPI API, pipeline and persistence
├── frontend/         # GitHub Pages-ready product UI
├── worker/           # isolated execution worker boundary
├── docs/             # architecture and deployment notes
├── Dockerfile        # backend container image
└── render.yaml       # Render deployment blueprint
```

## Local Development

```bash
cd backend
python -m uvicorn app.main:app --reload
```

The API exposes `/health` and `/api/system/status` for service and capability checks.

## AI Provider

FizFox uses an OpenAI-compatible HTTP boundary. Configure the backend only:

```text
FIZFOX_AI_BASE_URL=https://your-provider.example/v1
FIZFOX_AI_API_KEY=your-secret-key
FIZFOX_AI_MODEL=your-model
FIZFOX_AI_TIMEOUT=60
```

No provider credentials belong in the frontend or Git repository.

## GitHub Pages + API

The frontend can connect to a separately deployed HTTPS backend. Use the **API** button in the workspace, or open the Pages URL once with:

```text
?api=https://your-fizfox-api.example.com
```

The API origin is saved locally in the browser. In production, set `FIZFOX_ALLOWED_ORIGINS` to the exact GitHub Pages origin.

## Project Export

After a project is generated, verified, or edited, the workspace provides **Export project**. The backend returns the current project files as a ZIP archive without executing them.

## Security Boundary

Generated source is untrusted data. The API does not execute generated commands on its own host. The worker boundary uses restricted container controls including disabled networking, read-only project mounts, dropped Linux capabilities, no-new-privileges, CPU/memory/process limits, timeouts, and ephemeral storage.

The current preview is intentionally static and strips generated scripts. The container worker currently performs constrained validation rather than serving a production multi-tenant live preview. A production system still needs authentication, quotas, observability, stronger tenant isolation, persistent managed storage, and a dedicated preview service.

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
