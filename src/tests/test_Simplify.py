from pathlib import Path
from loguru import logger
import json
import sys

from src import vars as global_vars
from src.utils import (
    setup_default_config,
    ProgressTitle,
)
from src.prover.fvt import FVT
from src.refiner.simplifier import Simplifier


def _setup_output_path():
    """Setup and create output path."""
    out_path = Path(global_vars.fvt_config["output_path"]) / "test_simplify"
    out_path.mkdir(parents=True, exist_ok=True)
    return out_path


def run(arg):
    # Setup default config
    setup_default_config("lock-protocol")

    # set some configurations
    FVT.PROCESSOR_BIN = global_vars.config["paths"]["verus_processor"]
    FVT.VERUS_BIN = find_verus_binary(global_vars.config["paths"]["verus_dir"])
    fvt_crate_path = Path(global_vars.fvt_config["crate_path"])
    verify_base_path = Path(global_vars.fvt_config["verify_base_path"])
    out_path = _setup_output_path()
    fvt = FVT(fvt_crate_path, out_path, verify_base_path, None)
    fvt.set_verify_cmd(global_vars.fvt_config["verify_cmd"])
    fvt.preprocess(out_path)
    print(fvt.info.function_infos.keys())

    simplifier = Simplifier()
    simplifier.simplify(
        fvt,
        FUNC_LOC,
    )
