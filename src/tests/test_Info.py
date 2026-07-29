from pathlib import Path
from loguru import logger
import json
import sys

from src import vars as global_vars
from src.preprocessor.information import InfoRepository, RustFunctionInfo
from src.prover.collector import VerusInfoCollector


def run():
    # Test load info.json
    logger.info("Initializing the information repository.")
    path_info = Path("database/mathspec/out/preprocessor/info.json")
    if not path_info.exists():
        logger.error(f"File {path_info} does not exist, please run preprocess first.")
    dict_info = json.loads(path_info.read_text(encoding="utf-8"))
    info = InfoRepository.load_from_dict(dict_info)
    info.dump(path_info.parent / "info.pkl")
    info.dump_json(path_info.parent / "info2.json")

    # Test collect info
    func_infos = info.function_infos
    func_name = "lemma_sup_sup_distrib_right"
    for func_iter in func_infos.values():
        if func_iter.name == func_name:
            func_loc = func_iter.location
            break
    else:
        logger.error(f"Function {func_name} not found.")
        return
    logger.info(f"Collecting information for {func_name} ({func_loc}).")

    collector = VerusInfoCollector()
    code_knowledge = collector.collect_meta_knowledge(info, func_loc)
    logger.info(f"{code_knowledge}")
