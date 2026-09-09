# FizFox v0.1 Architecture

## 1. Core Loop

FizFox receives natural language and turns it into a structured application specification. That specification becomes the source of truth for generation and later edits.

```text
Prompt
  ↓
Planner
  ↓
AppSpec
  ↓
Code Generator
  ↓
Project Files
  ↓
Safe Runtime Boundary
  ↓
Verifier
  ↓
Repair Loop
  ↓
Preview
```

## 2. Backend Responsibilities

The backend owns orchestration, not UI rendering.

- Accept user prompts.
- Create and validate an `AppSpec`.
- Track project state and generated files.
- Invoke provider-agnostic planning and generation interfaces.
- Apply user-directed project edits.
- Dispatch builds through a runtime boundary.
- Verify generated output.
- Run bounded automatic repair for known failures.

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

The contract is provider-agnostic so FizFox can use different AI models without changing the rest of the system.

## 4. Current MVP Pipeline

```text
POST /api/projects
        ↓
Project (created)
        ↓
POST /api/projects/{id}/plan
        ↓
AppSpec (planned)
        ↓
POST /api/projects/{id}/generate
        ↓
Static project files (generated)
        ↓
POST /api/projects/{id}/build-and-repair
        ↓
Ready / failed + diagnostics
```

The current planner, generator, editor, runtime, verifier, and repair engine are deterministic MVP implementations. They establish the architecture before a real model provider and executable container runtime are connected.

## 5. Code Generation Boundary

`CodeGenerator` is a provider-agnostic interface. The current `HeuristicCodeGenerator` produces a small static web project containing `index.html`, `styles.css`, `app.js`, and `README.md`.

Generated source is treated as data. **FizFox must never execute generated code directly on the API host.** Execution belongs behind the sandbox boundary.

## 6. Runtime Boundary

`SafeStaticRuntime` is deliberately non-executing. It validates the generated project before any future executable sandbox is introduced.

It currently checks:

- project has generated files
- file-count limit
- file-size limit
- allowed file types
- path traversal / project-boundary escapes
- required `index.html` entrypoint
- basic HTML document validity

A future container-backed runtime will add actual build/start execution with explicit restrictions for filesystem access, network access, CPU, memory, execution time, child processes, and environment/secrets exposure.

## 7. Verification Boundary

`StaticVerifier` performs deterministic output checks without executing untrusted project code. It checks the HTML entrypoint and basic JavaScript structure and returns structured diagnostics.

Verification is intentionally layered so stronger checks can be added later:

1. generation validation
2. runtime/build validation
3. application startup validation
4. browser/page loading validation
5. basic interaction validation

## 8. Iterative Editing

Users can request changes after generation through:

```text
POST /api/projects/{id}/edit
```

The current `HeuristicProjectEditor` supports a small safe set of presentation edits such as dark mode, purple accents, hero-section insertion, and larger headings. A future model-backed editor will replace this implementation while keeping the same boundary.

## 9. Repair Loop

```text
Build / Verify
      ↓
Failure
      ↓
Diagnose
      ↓
Known safe repair?
   ┌──┴──┐
  YES    NO
   ↓      ↓
Repair   Report
   ↓
Build again
   ↓
Verify again
```

`BoundedRepairEngine` limits repair attempts and only applies explicitly supported deterministic repairs. Unknown failures are not blindly modified.

## 10. Project Model

A project is identified by a stable project ID and contains:

```text
Project
├── id
├── prompt
├── status
├── spec
├── files/
├── build
│   └── diagnostics[]
└── repair_attempts
```

Projects currently live in memory during the foundation phase. Persistence, authentication, and deployment will be introduced later.

## 11. Next Runtime Boundary

The next production-grade runtime must be container-backed and isolated. Generated applications should execute only inside a restricted sandbox with explicit filesystem, network, CPU, memory, time, process, and secret controls.

That runtime will enable real build/start execution and browser verification without weakening the host security boundary.
