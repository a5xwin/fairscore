# FairScore Full-Stack Run Guide

This project has a FastAPI backend and a Vite React frontend.

## One-command development run (cross-platform)

From the project root, run:

```bash
python scripts/bootstrap_and_run.py
```

This starts both services:
- Backend: http://0.0.0.0:8000
- Frontend: http://0.0.0.0:5173

Use Ctrl+C once to stop both.

Note:
- The bootstrap launcher auto-installs missing backend/frontend dependencies.
- The launcher performs a model preflight check.
- If ensemble model files are missing, services still start, but prediction endpoints may fail until training artifacts are generated.

## First-time setup on a new device

1. Create and activate a Python virtual environment.

Windows (PowerShell):

```bash
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Start everything.

```bash
python scripts/bootstrap_and_run.py
```

If model files are missing, generate them with:

```bash
python backend/models/preprocessing.py
python backend/models/random_forest.py
python backend/models/lightgbm_model.py
python backend/models/tab_transformer.py
python backend/models/stacked_ensemble.py
```

## Optional custom ports/hosts

```bash
python scripts/bootstrap_and_run.py --backend-port 9000 --frontend-port 5174 --backend-host 127.0.0.1 --frontend-host 127.0.0.1
```

## Optional bootstrap flags

```bash
# Reinstall dependencies even if checks pass
python scripts/bootstrap_and_run.py --force-install

# Train missing model artifacts before starting services
python scripts/bootstrap_and_run.py --train-missing-models

# Skip installs when dependencies are already present
python scripts/bootstrap_and_run.py --skip-python-install --skip-node-install

# Run without bootstrap logic (legacy launcher)
python scripts/dev_runner.py
```
