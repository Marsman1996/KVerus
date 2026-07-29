#!/usr/bin/env python3
"""Run KVerus experiment targets and rerun failed files."""

from __future__ import annotations

import argparse
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
KVERUS_ROOT = SCRIPT_DIR.parent.parent
PYTHON = "python"


@dataclass(frozen=True)
class TargetConfig:
    name: str
    fvt_config: Path
    fvt_name: str
    unverified_path: Path
    output_path: Path
    restore_repo: Path
    restore_path: Path

    @property
    def prover_path(self) -> Path:
        return self.output_path / "prover"

    @property
    def summary_path(self) -> Path:
        return self.prover_path / "verusbench_summary.json"


TARGETS = {
    "HumanEval": TargetConfig(
        name="HumanEval",
        fvt_config=Path("database/HumanEval/fvts.toml"),
        fvt_name="HumanEval",
        unverified_path=Path("database/HumanEval/code/unverified"),
        output_path=Path("database/HumanEval/out"),
        restore_repo=KVERUS_ROOT,
        restore_path=Path("database/HumanEval/code/unverified"),
    ),
    "MBPP": TargetConfig(
        name="MBPP",
        fvt_config=Path("database/MBPP/fvts.toml"),
        fvt_name="MBPP",
        unverified_path=Path("database/MBPP/code/unverified"),
        output_path=Path("database/MBPP/out"),
        restore_repo=KVERUS_ROOT,
        restore_path=Path("database/MBPP/code/unverified"),
    ),
    "Verus-Bench": TargetConfig(
        name="Verus-Bench",
        fvt_config=Path("database/Verus-Bench/fvts.toml"),
        fvt_name="Verus-Bench",
        unverified_path=Path("database/Verus-Bench/code/unverified"),
        output_path=Path("database/Verus-Bench/out"),
        restore_repo=KVERUS_ROOT,
        restore_path=Path("database/Verus-Bench/code/unverified"),
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run one or all experiment targets, rerun failures twice, and parse results."
    )
    parser.add_argument(
        "mode",
        choices=("all", "one"),
        help="Use 'all' for every target or 'one' for a single target.",
    )
    parser.add_argument(
        "target",
        nargs="?",
        choices=tuple(TARGETS),
        help="Target to run when mode is 'one'.",
    )
    return parser.parse_args()


def run_cmd(cmd: list[str], *, cwd: Path = KVERUS_ROOT) -> None:
    print(f"$ {shlex.join(cmd)}", flush=True)
    subprocess.run(cmd, cwd=cwd, check=True)


def restore_unverified(config: TargetConfig) -> None:
    run_cmd(
        ["git", "restore", "--", str(config.restore_path)],
        cwd=config.restore_repo,
    )


def parse_results(config: TargetConfig) -> None:
    run_cmd(
        [
            PYTHON,
            "database/utils/parse_verusbench.py",
            str(config.prover_path),
        ]
    )


def rerun_failed(config: TargetConfig) -> None:
    run_cmd(
        [
            PYTHON,
            "database/utils/rerun.py",
            str(config.summary_path),
            str(config.unverified_path),
            config.fvt_name,
        ]
    )


def run_target(config: TargetConfig) -> None:
    print(f"\n== {config.name} ==", flush=True)
    run_cmd(
        [
            PYTHON,
            "./KVerus.py",
            "-D",
            "-F",
            str(config.fvt_config),
            "prove",
            "--fvt",
            config.fvt_name,
            "all",
        ]
    )
    restore_unverified(config)
    parse_results(config)

    for idx in range(2):
        print(f"\n== {config.name}: rerun {idx + 1}/2 ==", flush=True)
        rerun_failed(config)
        restore_unverified(config)
        parse_results(config)


def main() -> int:
    args = parse_args()
    if args.mode == "one" and args.target is None:
        raise SystemExit("mode 'one' requires a target")
    if args.mode == "all" and args.target is not None:
        raise SystemExit("mode 'all' does not accept a target")

    targets = TARGETS.values() if args.mode == "all" else [TARGETS[args.target]]
    for target in targets:
        run_target(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
