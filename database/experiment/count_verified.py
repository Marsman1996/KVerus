#!/usr/bin/env python3
"""Count Rust/Verus files that pass verification."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from loguru import logger
from tqdm import tqdm


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_VERUS = SCRIPT_DIR / "../CortenMM/code/tools/verus/source/target-verus/release/verus"
DEFAULT_TARGETS = (
    SCRIPT_DIR / "examples/HumanEval",
    SCRIPT_DIR / "examples/MBPP",
    SCRIPT_DIR / "examples/Verus-Bench",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Count how many .rs files pass Verus verification."
    )
    parser.add_argument(
        "target",
        nargs="*",
        type=Path,
        help=(
            "One or more .rs files or directories containing .rs files. "
            "Defaults to examples/HumanEval, examples/MBPP, and examples/Verus-Bench."
        ),
    )
    parser.add_argument(
        "--verus",
        type=Path,
        default=DEFAULT_VERUS,
        help="Path to the Verus binary. Defaults to the repository-local binary.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="Per-file timeout in seconds.",
    )
    parser.add_argument(
        "--json",
        type=Path,
        default=None,
        help="Optional path to write a JSON report.",
    )
    parser.add_argument(
        "-D",
        "--debug",
        action="store_true",
        help="Enable debug logging, including the failed file list.",
    )
    return parser.parse_args()


def resolve_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    return (Path.cwd() / path).resolve()


def collect_files(target: Path) -> list[Path]:
    target = resolve_path(target)
    if target.is_file():
        if target.suffix != ".rs":
            raise SystemExit(f"Target file is not a .rs file: {target}")
        return [target]
    if target.is_dir():
        return sorted(p for p in target.rglob("*.rs") if p.is_file())
    raise SystemExit(f"Target does not exist: {target}")


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(SCRIPT_DIR.parent.parent))
    except ValueError:
        return str(path)


def verify_file(verus: Path, file_path: Path, timeout: float) -> dict[str, object]:
    cmd = [str(verus), str(file_path), "--error-format=json"]
    try:
        result = subprocess.run(
            cmd,
            cwd=SCRIPT_DIR.parent.parent,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        passed = result.returncode == 0
        output = (result.stdout + result.stderr).strip()
        return {
            "file": str(file_path),
            "passed": passed,
            "returncode": result.returncode,
            "output": output,
        }
    except subprocess.TimeoutExpired as exc:
        output = "".join(
            part for part in [exc.stdout or "", exc.stderr or ""] if isinstance(part, str)
        ).strip()
        return {
            "file": str(file_path),
            "passed": False,
            "returncode": None,
            "timeout": True,
            "output": output,
        }


def verify_target(
    target: Path, verus: Path, timeout: float, debug: bool
) -> tuple[dict[str, object], int]:
    files = collect_files(target)
    resolved_target = resolve_path(target)
    if not files:
        logger.error(f"No .rs files found under {resolved_target}")
        return {
            "target": str(resolved_target),
            "total": 0,
            "passed": 0,
            "failed": 0,
            "details": [],
        }, 2

    logger.info(f"Target: {display_path(resolved_target)}")
    details = []
    pass_count = 0
    for file_path in tqdm(files, desc=f"Verifying {resolved_target.name}", unit="file"):
        detail = verify_file(verus, file_path, timeout)
        details.append(detail)
        if detail["passed"]:
            pass_count += 1

    fail_count = len(files) - pass_count
    report = {
        "target": str(resolved_target),
        "total": len(files),
        "passed": pass_count,
        "failed": fail_count,
        "details": details,
    }

    logger.info(f"Total:  {len(files)}")
    logger.success(f"Passed: {pass_count}")
    if fail_count:
        logger.error(f"Failed: {fail_count}")
    else:
        logger.success("Failed: 0")

    failed_files = [Path(d["file"]) for d in details if not d["passed"]]
    if failed_files and debug:
        logger.debug("Failed files:")
        for file_path in failed_files:
            logger.debug(f"- {display_path(file_path)}")

    return report, 0 if fail_count == 0 else 1


def main() -> int:
    args = parse_args()
    logger.remove()
    logger.add(sys.stderr, level="DEBUG" if args.debug else "INFO")

    verus = resolve_path(args.verus)
    if not verus.is_file():
        logger.error(f"Verus binary not found: {verus}")
        return 2

    targets = args.target or list(DEFAULT_TARGETS)
    target_reports = []
    exit_code = 0
    for target in targets:
        target_report, target_exit_code = verify_target(
            target, verus, args.timeout, args.debug
        )
        target_reports.append(target_report)
        exit_code = max(exit_code, target_exit_code)

    total = sum(int(r["total"]) for r in target_reports)
    pass_count = sum(int(r["passed"]) for r in target_reports)
    fail_count = sum(int(r["failed"]) for r in target_reports)
    report = {
        "verus": str(verus),
        "total": total,
        "passed": pass_count,
        "failed": fail_count,
        "targets": target_reports,
    }

    if len(target_reports) > 1:
        logger.info("Aggregate:")
        logger.info(f"Total:  {total}")
        logger.success(f"Passed: {pass_count}")
        if fail_count:
            logger.error(f"Failed: {fail_count}")
        else:
            logger.success("Failed: 0")

    if args.json:
        out_path = resolve_path(args.json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        logger.info(f"Report written to {out_path}")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
