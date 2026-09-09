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
Generator
  ↓
Project
  ↓
Runtime
  ↓
Verifier
  ↓
Preview
```

## 2. Backend Responsibilities

The backend owns orchestration, not UI rendering.

- Accept user prompts.
- Create and validate an `AppSpec`.
- Persist project state.
- Invoke a code-generation provider.
- Manage generated project files.
- Later dispatch builds to isolated sandboxes.
- Later collect verification results and trigger repair loops.

## 3. AppSpec Contract

The planner should eventually produce a structure containing:

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

The contract is intentionally provider-agnostic so FizFox can use different AI models without changing the rest of the system.

## 4. Project Model

A project is identified by a stable project ID and contains:

```text
project/
├── metadata
└── files/
```

Generated source files are data owned by the project layer. The generator should not directly manipulate runtime infrastructure.

## 5. Runtime Boundary

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

## 6. Verification Boundary

Verification will be split into progressively stronger checks:

1. generation validation
2. dependency/install validation
3. build validation
4. application startup validation
5. browser/page loading validation
6. basic interaction validation

Failures become structured diagnostic data for the repair system.

## 7. Repair Loop

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

## 8. First Implementation Boundary

v0.1 starts with API contracts and project orchestration. Real model providers, sandbox execution, and browser verification will be added behind explicit interfaces rather than embedded into request handlers.
