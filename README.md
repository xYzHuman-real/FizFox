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
    └──────────────→ Planner / Modifier
```

## Repository Layout

```text
FizFox/
├── backend/          # API and orchestration
│   ├── app/
│   │   ├── main.py
│   │   └── models.py
│   └── requirements.txt
├── docs/             # Architecture and product decisions
│   └── ARCHITECTURE.md
└── .gitignore
```

## Development Principle

> Build the engine before the cosmetics.

Priority:

1. 🧠 Intelligence
2. ⚙️ Generation
3. 🔒 Sandbox
4. 🔍 Verification
5. 🔧 Auto-fix
6. 🎨 UI
7. 🚀 Deployment

The current repository intentionally starts with the backend foundation and explicit contracts so later generator/runtime components can be added without coupling everything together.