"""
Run AST based preprocessor to extract metadata from the source code.
"""

from pathlib import Path
from loguru import logger
from multiprocessing import cpu_count
from concurrent.futures import ThreadPoolExecutor
import subprocess
from tqdm import tqdm
from abc import ABC, abstractmethod
from typing import Optional
import json
import tempfile

import src.vars as global_vars
from src.utils import path_in_paths, with_progress_update, deep_merge

# from processor.rust.rust import RustParser
from .meta import Meta
from .tree import generate_tree


class ASTPreprocessor(ABC):
    """
    AST based preprocessor runner
    """

    POOL_SIZE = cpu_count()

    LANG_SUFFIX_MAP = {
        global_vars.SupportedLanguages.RUST: [".rs"],
    }

    def __init__(self):
        """
        Initialize the AST preprocessor, implemented by the subclass.
        The subclass should set self.source_files in the __init__ method.
        """
        self.source_files = []
        ...

    @classmethod
    @abstractmethod
    def from_library_config(cls, library_config: dict) -> "ASTPreprocessor":
        """
        Initialize the AST preprocessor from the library configuration.

        :param library_config: The library configuration.
        :return: The AST preprocessor.
        """
        ...

    def _get_source_files_from_source_paths(
        self, source_paths: list[Path]
    ) -> list[Path]:
        """
        Get the source files from the source paths.

        :param source_paths: The paths to the source code.
        :return: The source files.
        """
        SOURCE_SUFFIX = self.LANG_SUFFIX_MAP.get(global_vars.fvt_language)
        exclude_paths = [Path(_) for _ in global_vars.fvt_config["exclude_paths"]]
        source_files: list[Path] = []

        for source_path in source_paths:
            if source_path.is_file():
                source_files.append(source_path)
            elif source_path.is_dir():
                for suffix in SOURCE_SUFFIX:
                    source_files += list(source_path.rglob(f"*{suffix}"))
            else:
                logger.warning(f"Invalid source path {source_path}")

        # filter out the exclude paths
        source_files = [
            file.resolve()
            for file in source_files
            if not path_in_paths(file, exclude_paths)
        ]

        logger.debug(
            f"Found {len(source_files)} source files in source paths:\n{'\n'.join([str(file) for file in source_files])}"
        )

        return source_files

    @abstractmethod
    def run_once(self, source_file: Path) -> Meta:
        """
        Run the AST preprocessor for one source file.

        :param source_file: The source file.
        """
        pass

    def run(self) -> Meta:
        """
        Run the AST preprocessor.

        :return: The merged results.
        """
        logger.info(
            f"Running AST Preprocessor for all {len(self.source_files)} source files."
        )
        self.progress_bar = tqdm(
            total=len(self.source_files),
            desc="Running AST Preprocessor",
            unit="source files",
            colour="YELLOW",
            leave=False,
        )

        run_once_with_progress = with_progress_update(self.run_once)
        if self.POOL_SIZE > 1:
            # run the preprocessor for all source files in parallel
            with ThreadPoolExecutor(max_workers=self.POOL_SIZE) as pool:
                results = pool.map(
                    lambda source_file: run_once_with_progress(
                        source_file, progress=self.progress_bar
                    ),
                    self.source_files,
                )
        else:
            # run the preprocessor in serial, useful for debugging
            results = []
            for source_file in self.source_files:
                results.append(
                    run_once_with_progress(source_file, progress=self.progress_bar)
                )

        # merge the results
        meta = Meta.merge(results)

        self.progress_bar.close()
        logger.success(f"Preprocessed {len(self.source_files)} source files.")
        return meta


class RustASTPreprocessor(ASTPreprocessor):
    """
    Class for running the Rust Analyzer based AST preprocessor for Rust.
    """

    PROCESSOR_BIN: Optional[Path] = None

    def __init__(self, crate_path: Path):
        """
        Initialize the Rust AST preprocessor.

        :param crate_path: The path to target Rust crate.
        """
        self.crate_path = crate_path
        self.source_files = self._get_source_files_from_source_paths([crate_path])

    @classmethod
    def from_library_config(cls, library_config: dict) -> "RustASTPreprocessor":
        """
        Initialize the AST preprocessor from the library configuration.

        :param library_config: The library configuration.
        :return: The AST preprocessor.
        """
        crate_path = Path(library_config["crate_path"])
        return cls(crate_path)

    def run(self) -> dict:
        """
        Run the Rust AST preprocessor.
        We can run it once for the whole crate if there is Cargo.toml.
        Or we run for each file.

        :return: info dict
        """
        # # Analyze whole crate
        # if (self.crate_path / "Cargo.toml").exists():
        #     cmd = f"{self.PROCESSOR_BIN} info --filter-verus -c {self.crate_path}"
        #     logger.debug(f"Running Rust AST processor for {self.crate_path}: \n{cmd}")
        #     return self.run_once(cmd)

        # Analyze a single file
        self.progress_bar = tqdm(
            total=len(self.source_files),
            desc="Running AST Preprocessor",
            unit="source files",
            colour="YELLOW",
            leave=False,
        )
        run_once_with_progress = with_progress_update(self.run_once)
        cmds: list[str] = []
        for source_file in self.source_files:
            cmds.append(f"{self.PROCESSOR_BIN} single --file {source_file}")
        if self.POOL_SIZE > 1:
            with ThreadPoolExecutor(max_workers=self.POOL_SIZE) as pool:
                results = pool.map(
                    lambda cmd: run_once_with_progress(cmd, progress=self.progress_bar),
                    cmds,
                )
        else:
            results = []
            for cmd in cmds:
                results.append(run_once_with_progress(cmd, progress=self.progress_bar))

        # merge the results
        merged_info = dict()
        for result in results:
            merged_info = deep_merge(merged_info, result)

        self.progress_bar.close()
        logger.success(f"Preprocessed {len(self.source_files)} source files.")
        return merged_info

    def run_once(self, cmd: str) -> dict:
        """
        Run the Rust AST preprocessor for one source file or one crate.

        :param cmd: Analysis command line without output path.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            info_file = Path(tmp_dir) / "info.json"
            cmd += f" -o {info_file}"
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                errors="replace",
            )
            output = result.stderr
            if output:
                logger.warning(
                    f"AST preprocessor warning/error for {self.crate_path}: \n{output}"
                )

            if result.returncode != 0:
                logger.critical(
                    f"Failed to run Rust AST preprocessor for {self.crate_path}: \n{cmd}\nerror: \n{result.stderr}"
                )
                return {}

            try:
                return json.loads(info_file.read_text(encoding="utf-8"))
            except:
                logger.error(
                    f"Failed to load info data for cmd \n{cmd}\nAST preprocessor may fail"
                )
                return {}


class VerusASTPreprocessor(ASTPreprocessor):
    """
    Class for running the Verus Analyzer based AST preprocessor for Verus.
    """

    PROCESSOR_BIN: Optional[Path] = None

    def __init__(self, model_paths: list[Path]):
        """
        Initialize the Verus AST preprocessor.

        :param source_paths: The paths to the source code.
        """
        self.model_paths = model_paths
        self.source_files = self._get_source_files_from_source_paths(model_paths)

    @classmethod
    def from_library_config(cls, library_config: dict) -> "VerusASTPreprocessor":
        """
        Initialize the AST preprocessor from the library configuration.

        :param library_config: The library configuration.
        :return: The AST preprocessor.
        """
        model_paths = [Path(_) for _ in library_config["model_paths"]]
        return cls(model_paths)

    def run(self, out_path: Path):
        """
        Run the Rust AST preprocessor.
        Since the Rust Analyzer could scan the whole crate,
        we don't need to run it for each source file.
        Instead, we just run it once for the whole crate.
        Here we assume the "source_paths" is the crate path

        :param out_path: The output dir.
        """
        info = dict()
        api = dict()
        tree = dict()
        # FIXME: We only have 1 model path for now?
        for model_path in self.model_paths:
            tmp_info, tmp_api = self.run_once(model_path)
            info = deep_merge(info, tmp_info)
            api = api | tmp_api
            # generate dir tree
            tmp_tree = {str(model_path): generate_tree(model_path)}
            tree = tree | tmp_tree

        logger.success(f"Preprocessed {len(self.model_paths)} model crates.")
        info_path = out_path / "model.info.json"
        info_path.write_text(json.dumps(info, indent=2), encoding="utf-8")
        api_path = out_path / "model.api.json"
        api_path.write_text(json.dumps(api, indent=2), encoding="utf-8")
        tree_path = out_path / "model.tree.json"
        tree_path.write_text(json.dumps(tree, indent=2), encoding="utf-8")

    def run_once(self, model_path) -> tuple[dict, dict]:
        """
        Run the Rust AST preprocessor for one source file.

        :param source_file: The source file.
        :return: The dicts of info and api
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            info_path = Path(tmp_dir) / "info.json"
            cmd = f"{self.PROCESSOR_BIN} info --api-only -c {model_path} -o {info_path}"
            logger.debug(f"Running Verus AST processor for {model_path}: \n{cmd}")
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                errors="replace",
            )
            output = result.stderr
            if output:
                logger.warning(
                    f"AST preprocessor warning/error for {model_path}: \n{output}"
                )
            if result.returncode != 0:
                logger.error(
                    f"Failed to run Verus AST preprocessor for {model_path}:"
                    f"\n{cmd}\nerror: \n{result.stderr}"
                )

            # generate api.json
            api_path = Path(tmp_dir) / "api.json"
            return (
                json.loads(info_path.read_text(encoding="utf-8")),
                json.loads(api_path.read_text(encoding="utf-8")),
            )
