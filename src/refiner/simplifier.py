from typing import Optional
from loguru import logger
from pathlib import Path
import subprocess

from simplify_verus import SimplifyParser
from src.preprocessor.information import RustFunctionInfo
from src.prover.fvt import FVT
from src.prover.utils import VerifyStatus
from src.utils import parse_location


class Simplifier:
    """
    Class to simplify formal verification target (FVT) code
    """

    def __init__(self, deep_clean: bool):
        self.deep_clean = deep_clean

    @staticmethod
    def _is_unproven(simplify_parser: SimplifyParser) -> bool:
        """Check if the code contains unproven admits,
        assume, or external_body attr."""
        return (
            len(simplify_parser.admits) > 0
            or len(simplify_parser.assumes) > 0
            or "verifier::external_body" in simplify_parser.attributes
        )

    def simplify(self, fvt: FVT, func_loc: str):
        """
        Simplify the FVT code.
        Note: run preprocess on the FVT before calling this function.

        :param fvt: The formal verification target.
        :param func_loc: The location of the function to simplify.
        """
        logger.info(f"Simplification completed for function at {func_loc}.")
        func_info: Optional[RustFunctionInfo] = fvt.info.get_info(
            func_loc, RustFunctionInfo
        )
        if not func_info:
            logger.error(f"Function at {func_loc} not found in FVT info.")
            return

        code = func_info.get_impl_code()
        simplify_parser = SimplifyParser.from_code(code)
        simplify_parser.parse()
        if not self.deep_clean and self._is_unproven(simplify_parser):
            logger.info(f"Function at {func_loc} is unproven.")
            return

        func_file, line, col = parse_location(func_info.location)
        if func_file == None:
            logger.error(f"Function file not found for location {func_info.location}.")
            return

        path_func_file = Path(func_file)

        # Work with bytes since tree-sitter reports byte offsets,
        # which differ from Python string indices for multi-byte UTF-8 chars.
        code_bytes = code.encode("utf-8")
        for a in simplify_parser.asserts:
            a_start = a["start"]
            a_end = a["end"]
            new_code_bytes = (
                code_bytes[:a_start] + b" " * (a_end - a_start) + code_bytes[a_end:]
            )
            new_code = new_code_bytes.decode("utf-8")
            code_str = code_bytes.decode("utf-8")
            path_func_file.write_text(
                path_func_file.read_text().replace(code_str, new_code)
            )
            status, err_msg = fvt.run()
            if status == VerifyStatus.SUCCESS:
                code_bytes = new_code_bytes
            else:
                path_func_file.write_text(
                    path_func_file.read_text().replace(new_code, code_str)
                )

    def _get_modified_files(self, repo_path: Path) -> list[str]:
        cmd = ["git", "diff", "--name-only"]
        try:
            result = subprocess.run(
                cmd, cwd=repo_path, capture_output=True, text=True, check=True
            )
            return [f for f in result.stdout.splitlines() if f.strip()]
        except subprocess.CalledProcessError:
            logger.error(
                "Failed to run git diff. Make sure the directory is a git repository."
            )
            return []

    def _get_added_empty_lines(self, repo_path: Path, file_path: str) -> list[int]:
        cmd = ["git", "diff", "-U0", "--no-color", file_path]
        try:
            result = subprocess.run(
                cmd, cwd=repo_path, capture_output=True, text=True, check=True
            )
        except subprocess.CalledProcessError:
            logger.error(f"Failed to diff file {file_path}")
            return []

        lines_to_remove = []
        current_line_number = 0

        for line in result.stdout.splitlines():
            if line.startswith("@@"):
                parts = line.split(" ")
                new_hunk_info = next((p for p in parts if p.startswith("+")), None)

                if new_hunk_info:
                    new_hunk_info = new_hunk_info[1:]
                    if "," in new_hunk_info:
                        start = int(new_hunk_info.split(",")[0])
                    else:
                        start = int(new_hunk_info)
                    current_line_number = start

            elif line.startswith("+") and not line.startswith("+++"):
                content = line[1:]
                if not content.strip():
                    lines_to_remove.append(current_line_number)

                current_line_number += 1

        return lines_to_remove

    def _remove_lines(self, repo_path: Path, file_path: str, line_numbers: list[int]):
        if not line_numbers:
            return

        abs_path = repo_path / file_path

        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            logger.warning(f"Skipping non-UTF-8 file: {file_path}")
            return
        except FileNotFoundError:
            logger.warning(f"File not found: {file_path}")
            return

        line_numbers_sorted = sorted(list(set(line_numbers)), reverse=True)

        for ln in line_numbers_sorted:
            idx = ln - 1
            if 0 <= idx < len(lines):
                if not lines[idx].strip():
                    # logger.debug(f"Removing empty line {ln} from {file_path}")
                    del lines[idx]

        with open(abs_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

    def cleanup(self, fvt: FVT):
        """
        Cleanup the FVT code by removing the added spaces.
        Note: You shall only call this when all functions are simplified
        or you need to call preprocess again.

        :param fvt: The formal verification target.
        """
        logger.info("Starting cleanup of FVT code.")
        # TODO: what shall we do if `make fmt` fails?
        result = subprocess.run(
            f"make fmt",
            shell=True,
            capture_output=True,
            text=True,
            errors="replace",
            cwd=fvt.verify_base_path,
        )
        if result.returncode != 0:
            logger.error(
                f"Failed to run `make fmt` in {fvt.verify_base_path}: \n{result.stderr}"
            )
            return
        # format based on the git status
        modified_files = self._get_modified_files(fvt.verify_base_path)
        for file_path in modified_files:
            if not file_path.endswith(".rs"):
                continue
            lines_to_remove = self._get_added_empty_lines(
                fvt.verify_base_path, file_path
            )
            if lines_to_remove:
                logger.debug(
                    f"Removing {len(lines_to_remove)} empty lines from {file_path}"
                )
                self._remove_lines(fvt.verify_base_path, file_path, lines_to_remove)
