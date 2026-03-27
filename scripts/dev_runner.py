#!/usr/bin/env python3
"""Legacy launcher: run backend + frontend without bootstrap/install steps."""

from __future__ import annotations

import argparse

from bootstrap_and_run import run_services


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run FairScore backend/frontend without bootstrap.")
    parser.add_argument("--backend-host", default="0.0.0.0")
    parser.add_argument("--backend-port", type=int, default=8000)
    parser.add_argument("--frontend-host", default="0.0.0.0")
    parser.add_argument("--frontend-port", type=int, default=5173)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return run_services(
        backend_host=args.backend_host,
        backend_port=args.backend_port,
        frontend_host=args.frontend_host,
        frontend_port=args.frontend_port,
    )


if __name__ == "__main__":
    raise SystemExit(main())
