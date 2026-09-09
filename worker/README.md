# FizFox isolated worker

The worker host runs generated projects only through `backend/app/container_worker.py`.

## Required controls

- Docker Engine available to the worker host.
- No Docker socket mounted into generated containers.
- Generated containers use `--network none`.
- Root filesystem is read-only.
- All Linux capabilities are dropped.
- `no-new-privileges` is enabled.
- CPU, memory, process-count, temporary-storage, and execution-time limits are applied.
- The project directory is an ephemeral read-only bind mount.
- No host secrets or environment variables are passed into generated containers.

## Configuration

Environment variables:

- `FIZFOX_WORKER_IMAGE` (default `node:22-alpine`)
- `FIZFOX_WORKER_TIMEOUT` (default `10` seconds)
- `FIZFOX_WORKER_MEMORY` (default `512m`)
- `FIZFOX_WORKER_CPUS` (default `1.0`)
- `FIZFOX_WORKER_PIDS` (default `64`)

The worker currently performs a constrained static/container validation pass. A future preview service can add a separately exposed HTTP port without weakening the container boundary.
