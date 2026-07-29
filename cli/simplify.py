"""
Simplifier command line interface
"""

import click
from loguru import logger
from pathlib import Path
from tqdm import tqdm
import sys

from src import vars as global_vars
from src.utils import setup_default_config, find_verus_binary
from src.preprocessor.information import InfoRepository
from src.prover.fvt import FVT
from src.refiner.simplifier import Simplifier


def _setup_output_path():
    """Setup and create output path."""
    out_path = Path(global_vars.fvt_config["output_path"]) / "simplify"
    out_path.mkdir(parents=True, exist_ok=True)
    return out_path


def _resolve_target_to_files(target: str) -> list[Path]:
    """Resolve --target to a list of .rs file paths. Must be a valid path."""
    candidate = Path(target)
    if candidate.is_file() and candidate.suffix == ".rs":
        return [candidate.resolve()]
    if candidate.is_dir():
        files = sorted(candidate.rglob("*.rs"))
        if not files:
            logger.error(f"No .rs files found in directory '{target}'")
            sys.exit(1)
        return files
    logger.error(f"--target '{target}' is not a valid .rs file or directory")
    sys.exit(1)


def _build_info_from_tree_sitter(file_paths: list[Path]) -> InfoRepository:
    """Build an InfoRepository using tree-sitter parsing (no Verus-Analyzer needed)."""
    from promex_verus import VerusParser

    all_functions = {}
    all_composites = {}
    all_typedefs = {}
    all_traits = {}
    all_impls = {}

    for file_path in file_paths:
        parser = VerusParser.from_file(file_path.resolve())
        parser.parse()
        result = parser.get()

        for loc, func_dict in result["functions"].items():
            func_dict["isPub"] = func_dict.pop("is_pub")
            all_functions[loc] = func_dict

        for loc, record_dict in result["records"].items():
            all_composites[loc] = record_dict

        for loc, typedef_dict in result["typedefs"].items():
            all_typedefs[loc] = typedef_dict

        for loc, trait_dict in result["traits"].items():
            all_traits[loc] = trait_dict

        for loc, impl_dict in result["impls"].items():
            all_impls[loc] = impl_dict

    dict_info = {
        "function_infos": all_functions,
        "composite_infos": all_composites,
        "typedef_infos": all_typedefs,
        "trait_infos": all_traits,
        "impl_infos": all_impls,
    }

    return InfoRepository.load_from_dict(dict_info)


@click.command(help="Simplifies the Verus verify codes in the given directory.")
@click.option(
    "-F",
    "--fvt",
    "fvt_name",
    default=None,
    help="The name of the formal verify target for simplification. You should have it configured in the fvts.toml. \
If the fvts.toml contains only one fvt, you can omit this option.",
)
@click.option(
    "--deep-clean",
    is_flag=True,
    default=False,
    help="Enable deep cleaning during simplification.",
)
@click.option(
    "--target",
    "target",
    default=None,
    type=click.Path(exists=True),
    help="Target .rs file or directory to simplify. If not provided, simplifies all files in the crate.",
)
def simplify(fvt_name, deep_clean, target):
    """
    Simplifies the Verus verify codes in the given directory.
    """
    setup_default_config(fvt_name)

    FVT.VERUS_BIN = find_verus_binary(global_vars.config["paths"]["verus_dir"])

    fvt_crate_path = Path(global_vars.fvt_config["crate_path"])
    verify_base_path = Path(global_vars.fvt_config["verify_base_path"])
    out_path = _setup_output_path()

    fvt = FVT(fvt_crate_path, out_path, verify_base_path, None)
    fvt.set_verify_cmd(global_vars.fvt_config["verify_cmd"])

    if target:
        file_paths = _resolve_target_to_files(target)
    else:
        file_paths = sorted(fvt_crate_path.rglob("*.rs"))
        if not file_paths:
            logger.error(f"No .rs files found in crate path '{fvt_crate_path}'")
            sys.exit(1)

    logger.info(f"Parsing {len(file_paths)} file(s) with tree-sitter")
    fvt.info = _build_info_from_tree_sitter(file_paths)

    simplifier = Simplifier(deep_clean)
    for func_loc in tqdm(fvt.info.function_infos.keys()):
        logger.info(f"Simplifying function at {func_loc}")
        simplifier.simplify(
            fvt,
            func_loc,
        )

    simplifier.cleanup(fvt)


if __name__ == "__main__":
    simplify()
