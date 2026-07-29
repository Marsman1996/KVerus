#!/usr/bin/env python3
"""Run benchmark fetch scripts under database/."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DATABASE_DIR = SCRIPT_DIR.parent
DEFAULT_BENCHMARKS = [
    DATABASE_DIR / "CortenMM",
    DATABASE_DIR / "mathspec",
    DATABASE_DIR / "sage",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run all fetch.sh scripts in benchmark directories under database/."
    )
    parser.add_argument(
        "targets",
        nargs="*",
        help=(
            "Optional benchmark directory names to fetch, such as CortenMM or mathspec. "
            "Defaults to CortenMM, mathspec, and sage."
        ),
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Keep running remaining fetch scripts after one fails.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List fetch scripts that would be run and exit.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands without executing them.",
    )
    return parser.parse_args()


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(DATABASE_DIR.parent))
    except ValueError:
        return str(path)


def discover_fetch_scripts(targets: list[str]) -> list[Path]:
    if targets:
        scripts = []
        for target in targets:
            target_path = Path(target)
            if target_path.is_absolute():
                benchmark_dir = target_path
            elif target_path.exists():
                benchmark_dir = target_path.resolve()
            else:
                benchmark_dir = (DATABASE_DIR / target_path).resolve()
            script = benchmark_dir / "fetch.sh"
            if not script.is_file():
                raise SystemExit(f"Fetch script not found: {script}")
            scripts.append(script)
        return scripts

    scripts = []
    for benchmark_dir in DEFAULT_BENCHMARKS:
        script = benchmark_dir / "fetch.sh"
        if not script.is_file():
            raise SystemExit(f"Fetch script not found: {script}")
        scripts.append(script)
    return scripts


def run_fetch(script: Path, dry_run: bool) -> int:
    cmd = ["bash", str(script)]
    print(f"\n==> {display_path(script)}", flush=True)
    if dry_run:
        print(f"cwd: {script.parent}")
        print("cmd:", " ".join(cmd))
        return 0

    result = subprocess.run(cmd, cwd=script.parent, check=False)
    return result.returncode


def main() -> int:
    args = parse_args()
    scripts = discover_fetch_scripts(args.targets)

    if not scripts:
        print(f"No fetch.sh scripts found under {DATABASE_DIR}", file=sys.stderr)
        return 2

    if args.list:
        for script in scripts:
            print(display_path(script))
        return 0

    failures: list[tuple[Path, int]] = []
    for script in scripts:
        returncode = run_fetch(script, args.dry_run)
        if returncode == 0:
            continue

        failures.append((script, returncode))
        print(
            f"Fetch failed with exit code {returncode}: {display_path(script)}",
            file=sys.stderr,
        )
        if not args.continue_on_error:
            break

    if failures:
        print("\nFailed fetch scripts:", file=sys.stderr)
        for script, returncode in failures:
            print(f"- {display_path(script)}: exit code {returncode}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
