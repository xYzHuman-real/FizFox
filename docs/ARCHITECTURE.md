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
Sandbox Runtime
  ↓
Verifier
  ↓
Preview
```

## 2. Backend Responsibilities

The backend owns orchestration, not UI rendering.

- Accept user prompts.
- Create and validate an `AppSpec`.
- Track project state and generated files.
- Invoke a code-generation provider.
- Manage generated project files.
- Later dispatch builds to isolated sandboxes.
- Later collect verification results and trigger repair loops.

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
```

The current planner and generator are deterministic MVP implementations. They establish the interfaces before a real model provider is connected.

## 5. Code Generation Boundary

`CodeGenerator` is a provider-agnostic interface. The current `HeuristicCodeGenerator` produces a small static web project containing `index.html`, `styles.css`, `app.js`, and `README.md`.

Generated source is treated as data at this stage. **FizFox must never execute generated code directly on the API host.** Execution belongs behind the future sandbox boundary.

## 6. Project Model

A project is identified by a stable project ID and contains:

```text
Project
├── id
├── prompt
├── status
├── spec
└── files/
```

Projects currently live in memory during the foundation phase. Persistence will be introduced later.

## 7. Runtime Boundary

Generated code must eventually execute in an isolated environment rather than directly on the FizFox host.

The runtime boundary must support limits for:

- filesystem access
- network access
- CPU
- memory
- execution time
- child processes
- environment/secrets exposure

Sandboxing is a core security boundary, not an optional product feature.

## 8. Verification Boundary

Verification will be split into progressively stronger checks:

1. generation validation
2. dependency/install validation
3. build validation
4. application startup validation
5. browser/page loading validation
6. basic interaction validation

Failures become structured diagnostic data for the repair system.

## 9. Repair Loop

```text
Failure
  ↓
Diagnose
  ↓
Identify affected files
  ↓
Generate correction
  ↓
Apply correction
  ↓
Build again
  ↓
Verify again
```

Repairs must have bounded attempts so a broken project cannot create an endless loop.

## 10. Implementation Boundary

v0.1 builds intelligence and generation behind explicit interfaces first. Real model providers, sandbox execution, browser verification, and deployment are added progressively without coupling them to the API request handlers.
