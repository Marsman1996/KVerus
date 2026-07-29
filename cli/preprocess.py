"""
Preprocessor command line interface.
"""

from pathlib import Path
import click
from loguru import logger
from multiprocessing import cpu_count
import sys
import json

from src import vars as global_vars
from src.utils import setup_default_config
from src.preprocessor.ast import (
    RustASTPreprocessor,
    VerusASTPreprocessor,
    ASTPreprocessor,
)
from src.preprocessor.incidental import RustLibraryCallGraphBuilder
from src.preprocessor.information import InfoRepository
from src.preprocessor.lemma import LemmaExtractor, LemmaCollection


@click.command(help="Preprocess the library to get necessary information.")
@click.option(
    "-F",
    "--fvt",
    "library_name",
    default=None,
    help="The name of the library for preprocess. You should have it configured in the libraries.toml. \
If the libraries.toml contains only one library, you can omit this option.",
)
@click.option(
    "--pool-size",
    "pool_size",
    help="The number of the process running.",
    default=cpu_count(),
)
@click.option(
    "--call-graph",
    is_flag=True,
    default=False,
    help="Construct and dump the library call graph.",
)
def preprocess(
    library_name: str,
    pool_size: int,
    call_graph: bool,
):
    """
    KVerus Preprocessor CLI
    """
    # setup the default configuration
    setup_default_config(library_name)

    ASTPreprocessor.POOL_SIZE = pool_size

    if (
        global_vars.fvt_language == global_vars.SupportedLanguages.RUST
        and global_vars.fvt_tool == global_vars.SupportedTools.VERUS
    ):
        verus_preprocess(library_name, call_graph)
    else:
        logger.critical(
            f"Unsupported language {global_vars.fvt_language}, only Verus are supported."
        )
        sys.exit(1)


def verus_preprocess(library_name: str, call_graph: bool):
    """
    Preprocess the Rust library.
    """
    # set some configurations
    if (
        global_vars.fvt_language == global_vars.SupportedLanguages.RUST
        and global_vars.fvt_tool == global_vars.SupportedTools.VERUS
        and (
            verus_process_bin := Path(global_vars.config["paths"]["verus_processor"])
        ).is_file()
    ):
        RustASTPreprocessor.PROCESSOR_BIN = verus_process_bin
        VerusASTPreprocessor.PROCESSOR_BIN = verus_process_bin
        RustLibraryCallGraphBuilder.PROCESSOR_BIN = verus_process_bin
    else:
        logger.critical(
            "The processor binary is not found, please run `setup.sh` first."
        )
        sys.exit(1)

    # create the output and tmp path
    out_path = Path(global_vars.fvt_config["output_path"]) / "preprocessor"
    out_path.mkdir(parents=True, exist_ok=True)
    tmp_path = Path(global_vars.fvt_config["output_path"]) / "tmp"
    tmp_path.mkdir(parents=True, exist_ok=True)

    # For Rust and Verus, we directly generate the info.json and api.json
    rust_preprocessor = RustASTPreprocessor.from_library_config(global_vars.fvt_config)
    info_dict = rust_preprocessor.run()
    # FIXME: Shall we separate the model code from the library code?
    # verus_preprocessor = VerusASTPreprocessor.from_library_config(
    #     global_vars.fvt_config
    # )
    # verus_preprocessor.run(out_path)

    # DO info repository generation
    logger.info("Initializing the information repository.")
    info = InfoRepository.load_from_dict(info_dict)
    info.dump(out_path / "info.pkl")
    info.dump_json(out_path / "info.json")
    (out_path / "info-ori.json").write_text(json.dumps(info_dict))

    # DO lemma function extraction
    lemma_extractor = LemmaExtractor(info)
    lemma = lemma_extractor.extract()
    lemma.dump(out_path / "lemma.pkl")
    lemma.dump_to_json(out_path / "lemma.json")

    # Dump source files into json
    # They are used to determine whether a file in the backtrace is from the library
    # or not in later analysis process
    source_paths = rust_preprocessor.source_files
    with open(out_path / "sources.json", "w") as f:
        json.dump([str(_) for _ in source_paths], f, indent=4)
    logger.success(f"Source files dumped to {out_path / 'sources.json'}")

    if not call_graph:
        logger.info(
            "Skipping library call graph extraction; pass --call-graph to enable it."
        )
        return

    # DO library call graph extraction
    call_graph_builder = RustLibraryCallGraphBuilder.from_ast_preprocessor(
        rust_preprocessor
    )
    library_call_graph = call_graph_builder.build_graph()
    library_call_graph.dump(out_path / "call_graph.pkl")
    library_call_graph.dump_json(out_path / "call_graph.json")
    logger.success(f"Call graph dumped to {out_path / 'call_graph.json'}")
