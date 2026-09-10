from __future__ import annotations

# This module documents the public API landing payload without changing
# the existing application routing. Kept intentionally small for deployment.

API_ROOT_PAYLOAD = {
    "service": "FizFox API",
    "status": "online",
    "version": "0.1.0",
    "message": "FizFox backend is running. 🦊",
    "health": "/health",
    "system_status": "/api/system/status",
    "docs": "/docs",
}
