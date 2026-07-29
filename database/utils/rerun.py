import json
import os
import shlex
import subprocess
from pathlib import Path
from loguru import logger


KVERUS_PATH = Path(__file__).parent.parent.parent
FVT_CONFIGS = {
    "HumanEval": Path("database/HumanEval/fvts.toml"),
    "MBPP": Path("database/MBPP/fvts.toml"),
    "Verus-Bench": Path("database/Verus-Bench/fvts.toml"),
}


def rerun_failed_tests(path_summary: Path, parent_path: Path, fvt_name: str):
    """
    Rerun verification commands for failed files based on the JSON summary.

    :param path_summary: Path to the JSON summary file.
    :param parent_path: Parent path of the files.
    :param fvt_name: FVT name (string input).
    """
    if not os.path.exists(path_summary):
        logger.error(f"Error: The file {path_summary} does not exist.")
        return

    try:
        with open(path_summary, "r") as file:
            data = json.load(file)
    except json.JSONDecodeError as e:
        logger.error(f"Error: Failed to parse JSON file. {e}")
        return

    target_parent = parent_path
    if not target_parent.exists():
        logger.error(f"Error: Parent path '{target_parent}' does not exist.")
        return

    fail_details = data.get("details", {})

    for file_name, details in fail_details.items():
        if not details.get("sanitized", True):
            logger.info(f"Rerunning verification for failed file: {file_name}")
            fvt_config = FVT_CONFIGS.get(fvt_name)
            if fvt_config is None:
                logger.error(f"Unknown FVT name: {fvt_name}")
                return
            cmd = [
                "uv",
                "run",
                "--",
                "python",
                "./KVerus.py",
                "-D",
                "-F",
                str(fvt_config),
                "prove",
                "--fvt",
                fvt_name,
                "single",
                "--file",
                str(target_parent / file_name),
                "-o",
                str(path_summary.parent.resolve()),
            ]
            logger.debug(f"Running command: {shlex.join(cmd)}")
            subprocess.run(cmd, cwd=KVERUS_PATH)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Rerun verification for failed files based on JSON summary."
    )
    parser.add_argument(
        "path_summary", type=Path, help="Path to the JSON summary file."
    )
    parser.add_argument("parent_path", type=Path, help="Parent path of the files.")
    parser.add_argument("fvt_name", type=str, help="FVT name.")

    args = parser.parse_args()

    parent_path = args.parent_path.resolve()

    rerun_failed_tests(args.path_summary, parent_path, args.fvt_name)
