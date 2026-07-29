"""
Prover command line interface
"""

import traceback
import click
from enum import StrEnum, auto
from loguru import logger
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import hashlib
import sys

from src import vars as global_vars
from src.utils import (
    setup_default_config,
    setup_llm,
    find_verus_binary,
)
from src.llm.llm import LLMClient, LLMChat
from src.comprehender.knowledge import ModelKnowledge
from src.prover.fvt import FVT, FVTStage
from src.prover.collector import VerusInfoCollector
from src.refiner.refiner import Refiner
from src.refiner.validate import Validator
from src.analyzer.report import Reporter


# disable options for ablation study
class DisableOptions(StrEnum):
    CODE = auto()
    LEMMA = auto()
    VERUS = auto()
    ALL = auto()
    NONE = auto()


def _setup_configurations(disable_option: str = DisableOptions.NONE.value):
    """Setup common configurations for all prove commands."""
    comprehender_config = global_vars.config["comprehender"]
    refiner_config = global_vars.config["refiner"]

    ModelKnowledge.RETRIEVE_TOP_K = comprehender_config["retrieve_top_k"]
    FVT.PROCESSOR_BIN = global_vars.config["paths"]["verus_processor"]
    FVT.VERUS_BIN = find_verus_binary(global_vars.config["paths"]["verus_dir"])
    FVT.MAX_REFINE_ROUNDS = refiner_config["refinement_rounds"]
    Refiner.LEVEL = global_vars.fvt_config["level"]
    Validator.VALIDATE = refiner_config.get("validate_code", False)
    Reporter.ENABLED = refiner_config.get("enable_report", False)

    if disable_option == DisableOptions.CODE.value:
        FVT.DISABLE_CODE = True
    elif disable_option == DisableOptions.LEMMA.value:
        FVT.DISABLE_LEMMA = True
    elif disable_option == DisableOptions.VERUS.value:
        FVT.DISABLE_VERUS = True
    elif disable_option == DisableOptions.ALL.value:
        FVT.DISABLE_CODE = True
        FVT.DISABLE_LEMMA = True
        FVT.DISABLE_VERUS = True


def _setup_llm_client():
    """Setup LLM client with error handling."""
    try:
        refiner_config = global_vars.config["refiner"]
        fixer_llm_client = setup_llm(refiner_config["refine_llm"])
        return LLMChat(fixer_llm_client)
    except Exception as e:
        logger.critical(f"Failed to setup the LLM client: {e}")
        sys.exit(1)


def _setup_model_knowledge():
    """Setup model knowledge if database exists."""
    lemma_database_path = (
        Path(global_vars.fvt_config["database_path"]) / "comprehender" / "lemmas"
    )
    if lemma_database_path.exists():
        try:
            return ModelKnowledge.load(global_vars.config, lemma_database_path)
        except Exception as e:
            logger.critical(f"Failed to setup the knowledge retriever: {e}")
            traceback.print_exc()
            sys.exit(1)
    return None


def _create_fvt(new_chat, out_path, verify_cmd=None, model_knowledge=None):
    """Create and configure FVT instance. This for single and all commands."""
    fvt_crate_path = Path(global_vars.fvt_config["output_path"])
    verify_base_path = Path(global_vars.fvt_config["verify_base_path"])
    fvt = FVT(fvt_crate_path, out_path, verify_base_path, new_chat)
    fvt.set_stage(FVTStage.PROVE)
    fvt.SINGLE_FILE_PROVE = True

    if verify_cmd:
        fvt.set_verify_cmd(verify_cmd)
    if model_knowledge:
        fvt.set_knowledge(model_knowledge)

    return fvt


def _setup_output_path(subdir="prover"):
    """Setup and create output path."""
    out_path = Path(global_vars.fvt_config["output_path"]) / subdir
    out_path.mkdir(parents=True, exist_ok=True)
    return out_path


def _load_patch_context(patch_file: Path | None) -> str:
    """
    Load the optional patch/diff file to supply as extra context.
    """
    if patch_file is None:
        return ""

    try:
        patch_text = Path(patch_file).read_text(encoding="utf-8")
    except OSError as exc:
        raise click.ClickException(f"Failed to read patch file {patch_file}: {exc}")

    return f"## Verus Update Patch\n```\n{patch_text}\n```"


@click.group()
@click.option(
    "-F",
    "--fvt",
    "fvt_name",
    default=None,
    help="The name of the formal verify target for proof. You should have it configured in the fvts.toml. \
If the fvts.toml contains only one fvt, you can omit this option.",
)
@click.option(
    "--disable",
    "disable_option",
    type=click.Choice([_.value for _ in DisableOptions]),
    default=DisableOptions.NONE.value,
    help="""The module to disable during the proving process, used for ablation studies.
Select from the following options:

- "code": Do not provide the code metadata knowledge.

- "lemma": Do not provide lemma knowledge.

- "verus": Do not provide Verus knowledge.

- "all": Disable all knowledge.

- "none": Do not disable any knowledge.""",
    show_default=True,
)
@click.pass_context
def prove(ctx, fvt_name, disable_option):
    """
    Run prover commands.
    """
    # Store the disable option in the context for subcommands to access
    ctx.ensure_object(dict)
    ctx.obj["disable_option"] = disable_option
    ctx.obj["fvt_name"] = fvt_name


@prove.command(help="Prove a single Verus file.")
@click.option(
    "-o",
    "--output",
    "output_path",
    required=False,
    type=click.Path(path_type=Path, resolve_path=True, file_okay=False, dir_okay=True),
    help="The output path to store the proving results. If not provided, use the output path in the fvt configuration.",
)
@click.option(
    "--file",
    "file_path",
    required=True,
    type=click.Path(path_type=Path, resolve_path=True, file_okay=True, dir_okay=False),
    help="The path to the file to prove.",
)
@click.pass_context
def single(ctx, output_path: Path, file_path: Path):
    """
    Prove a single Verus file in the given directory.
    """
    disable_option = ctx.obj.get("disable_option", DisableOptions.NONE.value)
    fvt_name = ctx.obj.get("fvt_name")
    logger.info(f"Disable option: {disable_option}")

    setup_default_config(fvt_name)
    _setup_configurations(disable_option)

    # Override the output path if provided
    if output_path:
        global_vars.fvt_config["output_path"] = str(output_path)

    out_path = _setup_output_path()
    new_chat = _setup_llm_client()
    model_knowledge = _setup_model_knowledge()

    verify_cmd = global_vars.fvt_config["verify_cmd"].replace(
        "{INPUT_PATH}", f"{file_path}"
    )
    fvt = _create_fvt(new_chat, out_path, verify_cmd, model_knowledge)

    _prove_single_file(fvt, file_path)


def _prove_single_file(fvt: FVT, file_path: Path):
    fvt.meta_knowledge = ""
    refiner = Refiner()
    refiner.refine_until_success(fvt, file_path)


@prove.command(help="Prove all Verus files in the given directory.")
@click.option(
    "-o",
    "--output",
    "output_path",
    required=False,
    type=click.Path(path_type=Path, resolve_path=True, file_okay=False, dir_okay=True),
    help="The output path to store the proving results. If not provided, use the output path in the fvt configuration.",
)
@click.option(
    "--pool-size",
    "pool_size",
    type=int,
    default=5,
    help="The pool size for the parallel generation.",
)
@click.pass_context
def all(ctx, output_path: Path, pool_size: int):
    """
    Prove all single Verus file in the given directory.
    """
    disable_option = ctx.obj.get("disable_option", DisableOptions.NONE.value)
    fvt_name = ctx.obj.get("fvt_name")
    logger.info(f"Disable option: {disable_option}")

    setup_default_config(fvt_name)
    _setup_configurations(disable_option)

    # Borrow the crate path from the FVT configuration
    dir_path = Path(global_vars.fvt_config["crate_path"])
    if dir_path.is_file():
        logger.critical(f"The crate path {dir_path} is a file, expected a directory.")
        sys.exit(1)
    if not dir_path.exists():
        logger.critical(f"The crate path {dir_path} does not exist.")
        sys.exit(1)
    dir_path = dir_path.resolve(strict=True)
    # Override the output path if provided
    if output_path:
        global_vars.fvt_config["output_path"] = str(output_path)

    out_path = _setup_output_path()
    new_chat = _setup_llm_client()
    model_knowledge = _setup_model_knowledge()

    # Find all verus files
    verus_files = list(dir_path.rglob("*.rs"))
    if len(verus_files) == 0:
        logger.warning(f"No verus files in {dir_path}, skip")
        return
    logger.info(f"Found {len(verus_files)} verus files in {dir_path}")

    process_bar = tqdm(
        total=len(verus_files),
        desc="KVerus is proving",
        unit="source files",
        colour="YELLOW",
        leave=False,
    )

    def process_file(verus_file):
        try:
            logger.info(f"Proving {verus_file}")
            verify_cmd = global_vars.fvt_config["verify_cmd"].replace(
                "{INPUT_PATH}", f"{verus_file}"
            )
            fvt = _create_fvt(new_chat, out_path, verify_cmd, model_knowledge)
            _prove_single_file(fvt, verus_file)
            logger.success(f"{verus_file} Finished")
        except Exception as e:
            logger.error(f"Error processing {verus_file}: {e}")
            logger.debug(traceback.format_exc())
        finally:
            process_bar.update(1)

    with ThreadPoolExecutor(max_workers=pool_size) as executor:
        futures = [executor.submit(process_file, file) for file in verus_files]
        # Wait for all futures to complete
        for future in futures:
            future.result()


@prove.command(help="Prove the Verus verify codes in the given directory.")
@click.option(
    "--file",
    "file_path",
    required=True,
    help="The path to the file to prove admit.",
)
@click.option(
    "--caller",
    "caller_name",
    required=False,
    default=None,
    help="Specify the function name that calls admit() to focus proving. If omitted and multiple callers exist, the first one will be used; pass this to disambiguate.",
)
@click.option(
    "--pool-size",
    "pool_size",
    type=int,
    default=1,
    help="The pool size for the parallel proof.",
)
@click.pass_context
def admit(ctx, file_path, caller_name, pool_size):
    """
    Prove `admit()` in the Verus verify codes in the given directory.
    """
    disable_option = ctx.obj.get("disable_option", DisableOptions.NONE.value)
    fvt_name = ctx.obj.get("fvt_name")
    logger.info(f"Disable option: {disable_option}")

    setup_default_config(fvt_name)
    _setup_configurations(disable_option)

    file_path = Path(file_path).resolve(strict=True)
    out_path = _setup_output_path()
    new_chat = _setup_llm_client()
    model_knowledge = _setup_model_knowledge()

    # Create FVT with different crate path for admit command
    fvt_crate_path = Path(global_vars.fvt_config["crate_path"])
    verify_base_path = Path(global_vars.fvt_config["verify_base_path"])
    fvt = FVT(fvt_crate_path, out_path, verify_base_path, new_chat)
    fvt.set_stage(FVTStage.PROVE)
    fvt.set_verify_cmd(global_vars.fvt_config["verify_cmd"])
    if model_knowledge:
        fvt.set_knowledge(model_knowledge)

    # Find admit caller
    cg_path = out_path / f"cg-{hashlib.md5(str(file_path).encode()).hexdigest()}.json"
    fvt.call_graph(cg_path, file_path)
    admit_callers = []  # list of tuples (callerDeclLoc, callerName)
    for _, call_pair in fvt.cg_infos.items():
        if (
            call_pair["calleeName"] == "admit"
            and call_pair["calleeDeclLoc"] == "/PATH/TO/VERUS"
        ):
            admit_callers.append((call_pair["callerDeclLoc"], call_pair["callerName"]))

    if len(admit_callers) == 0:
        logger.success(f"No admit() in {file_path}, skip")
        return

    # Choose target caller by --caller-name or fallback
    target_caller_loc = None
    target_caller_name = None
    if caller_name:
        matched = [loc for (loc, name) in admit_callers if name == caller_name]
        if not matched:
            available = sorted(set(name for (_, name) in admit_callers))
            logger.critical(
                "No caller named '{}' found that calls admit() in {}. Available callers: {}".format(
                    caller_name, file_path, ", ".join(available)
                )
            )
            sys.exit(1)
        target_caller_loc = matched[0]
        target_caller_name = caller_name
    else:
        target_caller_loc, target_caller_name = admit_callers[0]
        unique_names = sorted(set(name for (_, name) in admit_callers))
        if len(unique_names) > 1:
            logger.warning(
                "Multiple admit() callers detected: {}. Using '{}' by default. Use --caller-name to choose explicitly.".format(
                    ", ".join(unique_names), target_caller_name
                )
            )

    # Run preprocessor for FVT
    fvt.preprocess(out_path)
    if target_caller_loc not in fvt.info.function_infos:
        logger.critical(
            f"Cannot find the function {target_caller_loc} in the preprocess info"
            ", please check the preprocess result."
        )
        sys.exit(1)
    fvt_func_code = fvt.info.function_infos[target_caller_loc].get_impl_code()
    ori_code = fvt_func_code
    fvt_func_code = fvt_func_code.replace("admit();", "// admit();", 1)
    code_in_file = file_path.read_text()
    file_path.write_text(code_in_file.replace(ori_code, fvt_func_code))

    # Rerun the preprocess to update the database
    fvt.preprocess(out_path)

    # Load knowledge here
    info_collector = VerusInfoCollector()
    if fvt.DISABLE_CODE == True:
        meta_knowledge = ""
    else:
        meta_knowledge = info_collector.collect_meta_knowledge(
            fvt.info, target_caller_loc
        )
    fvt.meta_knowledge = meta_knowledge
    extra_knowledge = meta_knowledge
    extra_knowledge += "\n\n"
    extra_knowledge += info_collector.collect_admit_knowledge(fvt, fvt_func_code)
    logger.debug(f"Extra knowledge: {extra_knowledge}")

    # Prove the admit() and refine until success
    refiner = Refiner()
    refiner.refine_until_success(fvt)


@prove.command(help="Fixes the Verus verify codes in the given directory.")
@click.option(
    "--pool-size",
    "pool_size",
    type=int,
    default=1,
    help="The pool size for the parallel generation.",
)
@click.option(
    "-P",
    "--patch-file",
    "patch_file",
    required=False,
    type=click.Path(
        path_type=Path,
        exists=True,
        dir_okay=False,
        file_okay=True,
        readable=True,
        resolve_path=True,
    ),
    help="Optional patch/diff file of Verus to use as additional context.",
)
@click.pass_context
def fix(ctx, pool_size, patch_file):
    """
    Fixes the Verus verify codes in the given directory.
    """
    disable_option = ctx.obj.get("disable_option", DisableOptions.NONE.value)
    fvt_name = ctx.obj.get("fvt_name")
    logger.info(f"Disable option: {disable_option}")

    # Setup default config
    setup_default_config(fvt_name)
    _setup_configurations(disable_option)

    # setup the llm
    new_chat = _setup_llm_client()

    # load knowledge here

    fvt_crate_path = Path(global_vars.fvt_config["crate_path"])
    verify_base_path = Path(global_vars.fvt_config["verify_base_path"])
    out_path = _setup_output_path("fixer")
    fvt = FVT(fvt_crate_path, out_path, verify_base_path, new_chat)
    fvt.set_stage(FVTStage.FIX)
    fvt.meta_knowledge = _load_patch_context(patch_file)
    fvt.set_verify_cmd(global_vars.fvt_config["verify_cmd"])
    refiner = Refiner()
    while fvt.refined == False and fvt.remain_refine_rounds > 0:
        refiner.refine_until_success(fvt)
