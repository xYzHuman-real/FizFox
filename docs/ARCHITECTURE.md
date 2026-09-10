# FizFox v0.1 Architecture

## 1. Core Loop

FizFox turns natural-language product ideas into structured application plans, generated files, verified previews, iterative edits, and exportable projects.

```text
Prompt
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
Iterative Edit
  └──────────────→ same project
```

## 2. Backend Responsibilities

The backend owns orchestration and persistence, not UI rendering.

- Accept and validate user prompts.
- Create and validate an `AppSpec`.
- Persist projects in SQLite for the MVP.
- Invoke provider-agnostic planning, generation, editing, and repair interfaces.
- Validate model output as untrusted data.
- Verify generated files without executing them on the API host.
- Run bounded repair for known or model-diagnosed failures.
- Build a safe static preview artifact.
- Export project files as a ZIP archive.

## 3. AppSpec Contract

The planner produces:

- project name
- application type
- pages
- components
- features
- routes
- data requirements
- dependencies
- styling direction
- generation constraints

The contract is provider-agnostic so FizFox can switch compatible model providers without changing the rest of the product pipeline.

## 4. Current Pipeline

```text
POST /api/projects
        ↓
Project (persisted)
        ↓
POST /api/projects/{id}/plan
        ↓
AppSpec
        ↓
POST /api/projects/{id}/generate
        ↓
Project files
        ↓
POST /api/projects/{id}/build-and-repair
        ↓
Verified / failed + diagnostics
        ↓
GET /api/projects/{id}/preview
        ↓
Static preview
        ↓
POST /api/projects/{id}/edit
        ↓
Rebuild / verify / repair
```

When AI environment variables are absent, FizFox uses deterministic heuristic fallbacks. When configured, the AI planner, generator, editor, and repairer are used through the provider transport boundary.

## 5. AI Boundary

All model communication goes through `AITransport` and `AIRequest`.

Model output is treated as untrusted text. Before it enters the project model it is:

1. parsed as JSON
2. schema/shape validated
3. path validated
4. file-count and file-size limited
5. total source size limited

Provider credentials are server-side environment variables only.

## 6. Code Generation

The provider-neutral `CodeGenerationProvider` produces a `GeneratedProject` containing safe relative paths and complete UTF-8 file contents.

The deterministic fallback currently creates a small static project containing `index.html`, `styles.css`, `app.js`, and `README.md`.

**Generated source must never be executed directly by the API process.**

## 7. Runtime and Sandbox

`SafeStaticRuntime` and `StaticVerifier` provide the non-executing MVP safety layer. The separate Docker worker boundary is designed for constrained validation on a trusted worker host.

Worker controls include:

- no network
- read-only project mount
- read-only container root
- dropped capabilities
- `no-new-privileges`
- CPU and memory limits
- process limits
- execution timeout
- ephemeral `/tmp`

The worker is not yet a production multi-tenant live-preview service.

## 8. Preview

The MVP preview is intentionally inert. `StaticPreviewBuilder` strips generated `<script>` blocks and embeds the generated HTML/CSS into a preview document. This lets users inspect the visual result without executing arbitrary generated JavaScript inside the API process.

A future dedicated preview service can run applications inside stronger isolated sandboxes and return an opaque preview URL.

## 9. Iterative Editing

Users request changes through:

```text
POST /api/projects/{id}/edit
```

The model-backed editor receives the current AppSpec, project files, and instruction, then returns only complete contents for changed files. Safe path and size validation is applied before persistence.

A deterministic editor remains available when no AI provider is configured.

## 10. Repair Loop

```text
Build / Verify
      ↓
Failure
      ↓
Diagnose
      ↓
AI repairer if configured
      ↓
Safe output validation
      ↓
Verify again
      ↓
Ready / report failure
```

The deterministic `BoundedRepairEngine` remains the fallback and has a hard attempt limit.

## 11. Persistence and Export

Projects are stored in SQLite through `ProjectStore`.

```text
Project
├── id
├── prompt
├── status
├── spec
├── files
├── build diagnostics
├── preview_html
└── repair_attempts
```

The API exposes project listing, retrieval, file retrieval, deletion, and ZIP export. Production should move persistence to a managed database/object store.

## 12. Deployment

The FastAPI backend has a container image and Render blueprint. The frontend is a dependency-free static application suitable for GitHub Pages.

The frontend can be pointed at the deployed API using the API settings panel or `?api=` query parameter. Production CORS must allow the exact frontend origin.

## 13. Production Gaps

The v0.1 foundation intentionally does not claim production multi-tenancy. Before public scale, add:

- authentication and authorization
- per-user project ownership
- request quotas and rate limiting
- managed database and object storage
- job queue for long builds
- stronger sandbox isolation
- dedicated live-preview service
- structured observability and audit logs
- abuse prevention
- secret isolation
- resource billing/limits
