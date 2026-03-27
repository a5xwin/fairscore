#!/usr/bin/env python3
"""Bootstrap and run FairScore backend + frontend in one command."""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterable, List


ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"
MODELS_DIR = BACKEND_DIR / "models"


def _run(cmd: List[str], cwd: Path | None = None, check: bool = True) -> int:
    print(f"[run] {' '.join(cmd)}")
    completed = subprocess.run(cmd, cwd=str(cwd) if cwd else None)
    if check and completed.returncode != 0:
        raise RuntimeError(f"Command failed ({completed.returncode}): {' '.join(cmd)}")
    return completed.returncode


def _python_requirements_files() -> List[Path]:
    files = [ROOT_DIR / "requirements.txt", BACKEND_DIR / "requirements.txt"]
    return [f for f in files if f.exists()]


def _python_deps_ready() -> bool:
    modules = ["fastapi", "uvicorn", "dotenv"]
    for mod in modules:
        code = f"import {mod}"
        result = subprocess.run([sys.executable, "-c", code], capture_output=True)
        if result.returncode != 0:
            return False
    return True


def _frontend_deps_ready() -> bool:
    return (FRONTEND_DIR / "node_modules").exists()


def ensure_python_dependencies(force_install: bool = False, skip: bool = False) -> None:
    if skip:
        print("[bootstrap] Skipping Python dependency installation (--skip-python-install).")
        return

    ready = _python_deps_ready()
    if ready and not force_install:
        print("[bootstrap] Python dependencies look available; skipping install.")
        return

    req_files = _python_requirements_files()
    if not req_files:
        print("[bootstrap] No requirements files found; skipping Python install.")
        return

    print("[bootstrap] Installing Python dependencies...")
    _run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], cwd=ROOT_DIR)
    for req in req_files:
        _run([sys.executable, "-m", "pip", "install", "-r", str(req)], cwd=ROOT_DIR)


def _npm_command() -> str:
    # On Windows, npm generally resolves to npm.cmd.
    return "npm.cmd" if os.name == "nt" else "npm"


def ensure_node_dependencies(force_install: bool = False, skip: bool = False) -> None:
    if skip:
        print("[bootstrap] Skipping Node dependency installation (--skip-node-install).")
        return

    ready = _frontend_deps_ready()
    if ready and not force_install:
        print("[bootstrap] Frontend dependencies look available; skipping install.")
        return

    print("[bootstrap] Installing frontend dependencies...")
    _run([_npm_command(), "install"], cwd=FRONTEND_DIR)


def _required_model_artifacts() -> List[Path]:
    return [
        MODELS_DIR / "random_forest_model.joblib",
        MODELS_DIR / "lightgbm_model.joblib",
        MODELS_DIR / "tab_transformer_model.pth",
        MODELS_DIR / "meta_learner.joblib",
        MODELS_DIR / "label_encoders.joblib",
        MODELS_DIR / "scaler.joblib",
        MODELS_DIR / "ensemble_config.json",
    ]


def model_preflight() -> List[Path]:
    missing = [artifact for artifact in _required_model_artifacts() if not artifact.exists()]
    if missing:
        print("[preflight] Missing model artifacts:")
        for item in missing:
            print(f"  - {item.relative_to(ROOT_DIR)}")
        print("[preflight] Services can still start, but prediction endpoints may fail.")
    else:
        print("[preflight] Model artifacts found.")
    return missing


def train_missing_models() -> None:
    scripts = [
        MODELS_DIR / "preprocessing.py",
        MODELS_DIR / "random_forest.py",
        MODELS_DIR / "lightgbm_model.py",
        MODELS_DIR / "tab_transformer.py",
        MODELS_DIR / "stacked_ensemble.py",
    ]

    print("[training] Training/refreshing model artifacts...")
    for script in scripts:
        if not script.exists():
            raise FileNotFoundError(f"Required training script is missing: {script}")
        _run([sys.executable, str(script)], cwd=ROOT_DIR)


def _start_process(cmd: List[str], cwd: Path) -> subprocess.Popen:
    kwargs = {
        "cwd": str(cwd),
        "stdin": None,
    }

    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

    return subprocess.Popen(cmd, **kwargs)


def _shutdown_processes(processes: Iterable[subprocess.Popen]) -> None:
    procs = [p for p in processes if p and p.poll() is None]
    if not procs:
        return

    print("\n[shutdown] Stopping services...")
    for p in procs:
        try:
            if os.name == "nt":
                p.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                p.terminate()
        except Exception:
            p.terminate()

    deadline = time.time() + 8
    while time.time() < deadline and any(p.poll() is None for p in procs):
        time.sleep(0.2)

    for p in procs:
        if p.poll() is None:
            p.kill()


def run_services(backend_host: str, backend_port: int, frontend_host: str, frontend_port: int) -> int:
    backend_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        backend_host,
        "--port",
        str(backend_port),
        "--reload",
    ]

    frontend_cmd = [
        _npm_command(),
        "run",
        "dev",
        "--",
        "--host",
        frontend_host,
        "--port",
        str(frontend_port),
    ]

    backend_proc = None
    frontend_proc = None

    try:
        print("[launch] Starting backend and frontend...")
        backend_proc = _start_process(backend_cmd, BACKEND_DIR)
        frontend_proc = _start_process(frontend_cmd, FRONTEND_DIR)

        print("[ready] Services started:")
        print(f"  - Backend:  http://{backend_host}:{backend_port}")
        print(f"  - Frontend: http://{frontend_host}:{frontend_port}")
        print("[ready] Press Ctrl+C once to stop both services.")

        while True:
            if backend_proc.poll() is not None:
                print("[exit] Backend exited.")
                return backend_proc.returncode or 0
            if frontend_proc.poll() is not None:
                print("[exit] Frontend exited.")
                return frontend_proc.returncode or 0
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[signal] Ctrl+C received.")
        return 0
    finally:
        _shutdown_processes([backend_proc, frontend_proc])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap and run FairScore services.")
    parser.add_argument("--backend-host", default="0.0.0.0")
    parser.add_argument("--backend-port", type=int, default=8000)
    parser.add_argument("--frontend-host", default="0.0.0.0")
    parser.add_argument("--frontend-port", type=int, default=5173)
    parser.add_argument("--force-install", action="store_true", help="Force dependency installation.")
    parser.add_argument("--train-missing-models", action="store_true", help="Train model artifacts before launch.")
    parser.add_argument("--skip-python-install", action="store_true", help="Skip Python dependency install.")
    parser.add_argument("--skip-node-install", action="store_true", help="Skip frontend dependency install.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    ensure_python_dependencies(force_install=args.force_install, skip=args.skip_python_install)
    ensure_node_dependencies(force_install=args.force_install, skip=args.skip_node_install)

    missing = model_preflight()
    if args.train_missing_models and missing:
        train_missing_models()
        model_preflight()

    return run_services(
        backend_host=args.backend_host,
        backend_port=args.backend_port,
        frontend_host=args.frontend_host,
        frontend_port=args.frontend_port,
    )


if __name__ == "__main__":
    raise SystemExit(main())
