"""
Comprehender command line interface.
"""

import click
from loguru import logger
from pathlib import Path
from enum import StrEnum, auto
import traceback
import pickle
import sys

from src import vars as global_vars
from src.utils import setup_default_config, setup_llm
from src.preprocessor.information import InfoRepository
from src.preprocessor.lemma import LemmaCollection
from src.comprehender.knowledge import ModelKnowledge, Knowledge
from src.comprehender.comprehender import GeneralComprehender
from src.comprehender.summarizer import RefineHintSummarizer


class TaskOptions(StrEnum):
    """
    Enum for the comprehension task
    """

    ALL = auto()
    LIBPURP = auto()
    LEMMAPURP = auto()
    SUMMARY = auto()


def setup_rag_for_vstd():
    try:
        ModelKnowledge.from_config(global_vars.config, global_vars.fvt_config)
    except Exception as e:
        logger.critical(f"Failed to setup the knowledge retriever: {e}")
        traceback.print_exc()
        sys.exit(1)


def _setup_comprehension_llm():
    comprehender_config = global_vars.config["comprehender"]
    try:
        return setup_llm(comprehender_config["comprehension_llm"])
    except Exception as e:
        logger.critical(f"Failed to setup the LLM client: {e}")
        traceback.print_exc()
        sys.exit(1)


def _run_refine_hint_summary(llm_client, comprehend_path: Path):
    try:
        summarizer = RefineHintSummarizer(llm_client)
        summarizer.summarize_from_config(
            fvt_name=global_vars.fvt_name,
            document_paths=global_vars.fvt_config.get("document_paths", []),
            exclude_paths=global_vars.fvt_config.get("exclude_paths", []),
            output_dir=comprehend_path / "docs",
        )
    except Exception as e:
        logger.critical(f"Failed to generate refinement hint summary: {e}")
        traceback.print_exc()
        sys.exit(1)


@click.command(help="Use LLM to comprehend the FVT.")
@click.option(
    "-F",
    "--fvt",
    "library_name",
    default=None,
    help="The name of the FVT to comprehend. You should have it configured in the libraries.toml.",
)
@click.option(
    "--task",
    "task",
    type=click.Choice([t for t in TaskOptions]),
    help="The task to perform, either comprehend the library purpose, function purpose and usage, or function relevance.",
    default=TaskOptions.ALL,
)
@click.option(
    "--pool-size",
    "pool_size",
    type=int,
    help="The parallel pool size for the comprehension tasks. Default is 5.",
    default=5,
)
def comprehend(
    library_name: str,
    task: str,
    pool_size: int,
):
    """
    KVerus Comprehender CLI
    """
    # setup the default configuration
    setup_default_config(library_name)

    # set configs
    comprehender_config = global_vars.config["comprehender"]
    ModelKnowledge.RETRIEVE_TOP_K = comprehender_config["retrieve_top_k"]
    do_library_purpose = task == TaskOptions.LIBPURP or task == TaskOptions.ALL
    do_lemma_purpose = task == TaskOptions.LEMMAPURP or task == TaskOptions.ALL
    do_summary = task == TaskOptions.SUMMARY or task == TaskOptions.ALL

    # create the output path
    comprehend_path = Path(global_vars.fvt_config["output_path"]) / "comprehender"
    comprehend_path.mkdir(parents=True, exist_ok=True)

    # setup RAG for VSTD
    if global_vars.fvt_name == "vstd":
        setup_rag_for_vstd()
        if do_summary:
            _run_refine_hint_summary(_setup_comprehension_llm(), comprehend_path)
        return

    llm_client = None
    if do_summary:
        llm_client = _setup_comprehension_llm()
        _run_refine_hint_summary(llm_client, comprehend_path)

    if not do_library_purpose and not do_lemma_purpose:
        return

    # Then we will comprehend the lemma functions
    # load API functions, info repository
    preprocess_path = Path(global_vars.fvt_config["output_path"]) / "preprocessor"
    try:
        info_repo = InfoRepository.load(preprocess_path / "info.pkl")
        lemma_collection = LemmaCollection.load(preprocess_path / "lemma.pkl")
    except Exception as e:
        logger.critical(
            f"Failed to load library preprocessing results, please run preprocessor first: {e}"
        )
        traceback.print_exc()
        sys.exit(1)

    # setup the llm
    if llm_client is None:
        llm_client = _setup_comprehension_llm()

    # setup the knowledge retriever
    try:
        knowledge = Knowledge.from_config(global_vars.config, global_vars.fvt_config)
    except Exception as e:
        logger.critical(f"Failed to setup the knowledge retriever: {e}")
        traceback.print_exc()
        sys.exit(1)

    # # set task flags
    GeneralComprehender.DO_LIBRARY_PURPOSE = do_library_purpose
    GeneralComprehender.DO_LEMMA_USAGE = do_lemma_purpose

    comprehender = GeneralComprehender(
        llm_client,
        knowledge,
        lemma_collection,
        info_repo,
        pool_size=pool_size,
    )
    # load last comprehension if exists
    if (comprehend_path / "comp.pkl").exists():
        logger.info("Loading last comprehension.")
        with open(comprehend_path / "comp.pkl", "rb") as f:
            comp = pickle.load(f)
        comprehender.lib_comprehension = comp

    # do comprehension
    comprehender.comprehend()

    # dump the results
    comprehender.dump(
        (
            (comprehend_path / "comp.pkl")
            if GeneralComprehender.DO_LIBRARY_PURPOSE
            or GeneralComprehender.DO_LEMMA_USAGE
            else None
        )
    )
    comprehender.dump_to_json_csv(
        (
            comprehend_path / "comp.json"
            if GeneralComprehender.DO_LIBRARY_PURPOSE
            or GeneralComprehender.DO_LEMMA_USAGE
            else None
        )
    )
