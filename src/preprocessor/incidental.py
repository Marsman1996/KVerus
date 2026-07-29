"""
Get the incidental relations of the API functions.
If the API function A calls API function B, then B is incidental to A.
Any invocation of A will be considered as a potential invocation of B.
"""

from abc import abstractmethod
from loguru import logger
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import cpu_count
from functools import cached_property
from tqdm import tqdm
import subprocess
import tempfile
import json
import pickle

from .ast import RustASTPreprocessor
from .consumer import CallGraph


class LibraryCallGraphBuilder:
    """
    Class for building Call Graph from library source code.
    """

    # The path to the CGprocessor binary
    PROCESSOR_BIN: Path = None
    # The pool size
    POOL_SIZE: int = cpu_count()

    def __init__(self, source_files: list[Path], crate_path: Path):
        """
        Initialize the Call Graph Builder

        :param source_files: The list of source files
        :param crate_path: The path to the crate
        """
        self.source_files = source_files
        self.crate_path = crate_path

    @classmethod
    def from_ast_preprocessor(
        cls, ast_preprocessor: RustASTPreprocessor
    ) -> "LibraryCallGraphBuilder":
        """
        Initialize the Call Graph Builder from the AST Preprocessor

        :param ast_preprocessor: The AST Preprocessor
        :param api_collection: The API functions collection
        """
        return cls(ast_preprocessor.source_files, ast_preprocessor.crate_path)

    def build_graph(self) -> CallGraph:
        """
        Build the Call Graph from the source

        :return: The Call Graph
        """
        call_graph = CallGraph()

        for (
            caller_name,
            caller_location,
            callee_name,
            callee_location,
        ) in self.calling_pairs:
            call_graph.add_call(
                caller_name, caller_location, callee_name, callee_location
            )

        return call_graph

    @cached_property
    def calling_pairs(self) -> list[tuple[str, str, str, str]]:
        """
        Process the source files and get the caller-callee pairs

        :return: The list of position-caller-callee pairs, like (caller_name, caller_location, callee_name, callee_location)
        """
        pairs = []

        progress_bar = tqdm(
            total=len(self.source_files),
            desc="Running AST CallGraph Processor for library source code",
            unit="file",
            leave=False,
            colour="YELLOW",
        )

        def _process_one_source_with_progress(source_file: Path):
            result = self._process_one_source(source_file)
            progress_bar.update(1)
            return result

        if self.POOL_SIZE == 1:
            for source_file in self.source_files:
                pairs += _process_one_source_with_progress(source_file)
        else:
            with ThreadPoolExecutor(max_workers=self.POOL_SIZE) as executor:
                pairs = sum(
                    executor.map(_process_one_source_with_progress, self.source_files),
                    [],
                )

        return pairs

    def _parse_cg(
        self, cg_file: Path, source_file: Path
    ) -> list[tuple[str, str, str, str]]:
        # load the cg.json file
        try:
            with open(cg_file, "r") as f:
                cg = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load cg.json from {cg_file}: {e}")
            return []

        pairs = []
        for _, calling_info in cg.items():
            pairs.append(
                (
                    calling_info["callerName"],
                    calling_info["callerDeclLoc"],
                    calling_info["calleeName"],
                    calling_info["calleeDeclLoc"],
                )
            )
        if not pairs:
            logger.warning(f"No caller-callee pairs found for source {source_file}.")
        else:
            logger.debug(
                f"Found {len(pairs)} caller-callee pairs for source {source_file}."
            )
        return pairs

    @abstractmethod
    def _process_one_source(self, source_file: Path) -> list[tuple[str, str, str, str]]:
        """
        Process one source file and get the caller-callee pairs

        :param source_file: The source file to process
        :return: The list of caller-callee pairs, like (caller_name, caller_location, callee_name, callee_location)
        """
        pass


class RustLibraryCallGraphBuilder(LibraryCallGraphBuilder):
    """
    Class for building Call Graph from Rust library source code.
    """

    def _process_one_source(self, source_file):
        with tempfile.TemporaryDirectory() as tmp_dir:
            # run the CGprocessor binary
            cg_file = Path(tmp_dir) / "cg.json"
            cmd = f"{self.PROCESSOR_BIN} call -c {self.crate_path} -i {source_file} -o {cg_file}"
            logger.debug(f"Running CGprocessor for consumer {source_file}: \n{cmd}")

            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                errors="replace",
            )
            output = result.stdout + result.stderr
            if output:
                logger.warning(
                    f"CGprocessor warning/error for consumer {source_file}:\n{output}"
                )
            if result.returncode != 0:
                logger.error(
                    f"Failed to run CGprocessor for consumer {source_file}: \n{cmd}\nerror: \n{result.stderr}"
                )
                return []

            return self._parse_cg(cg_file, source_file)
