"""
Evaluator command line interface.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
from loguru import logger

from src import vars as global_vars
from src.llm.proof_difficulty import ProofDifficultyEvaluator
from src.preprocessor.information import InfoRepository, RustFunctionInfo
from src.utils import parse_location, setup_default_config


@click.group()
def eval():
    """
    KVerus Evaluator CLI
    """


@eval.command(help="LLM-based difficulty score for a proof function.")
@click.option(
    "-F",
    "--fvt",
    "fvt_name",
    default=None,
    help="Name of the formal verification target to load from fvts.toml. "
    "If only one entry exists you may omit this option.",
)
@click.option(
    "--file",
    "file_path",
    required=True,
    type=click.Path(
        exists=True, dir_okay=False, file_okay=True, readable=True, path_type=Path
    ),
    help="Path to the source file that defines the target function.",
)
@click.option(
    "--function",
    "function_name",
    required=True,
    help="Name of the function or lemma to evaluate.",
)
@click.option(
    "--output",
    "output_path",
    required=False,
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    help="Optional JSON destination. Defaults to logs/eval/proof-difficulty-*.json.",
)
@click.option(
    "--llm",
    "llm_name",
    required=False,
    help="Override the LLM config entry used for scoring "
    "(defaults to [eval].difficulty_llm or the global default).",
)
def difficulty(
    fvt_name: Optional[str],
    file_path: Path,
    function_name: str,
    output_path: Optional[Path],
    llm_name: Optional[str],
):
    """
    Evaluate the difficulty of a function using the configured LLM rubric.
    """

    setup_default_config(fvt_name)

    info_path = (
        Path(global_vars.fvt_config["output_path"]) / "preprocessor" / "info.pkl"
    )
    if not info_path.exists():
        raise click.ClickException(
            f"Preprocessor output not found at {info_path}. Please run preprocess first."
        )

    logger.info(f"Loading preprocessor information from {info_path}")
    info_repo = InfoRepository.load(info_path)

    target_file = file_path.resolve()
    candidate_functions = _find_function_candidates(
        info_repo, function_name, target_file
    )
    if not candidate_functions:
        raise click.ClickException(
            f"Function '{function_name}' was not found inside '{target_file}'. "
            "Run preprocess or double-check the --file path."
        )
    if len(candidate_functions) > 1:
        logger.warning(
            f"Multiple definitions named '{function_name}' detected in {target_file}. "
            "Using the first match."
        )
    func_info = candidate_functions[0]

    function_code = func_info.get_impl_code()
    if not function_code.strip():
        raise click.ClickException(
            f"Unable to extract implementation body for '{func_info.name}'. "
            "Re-run preprocess to refresh metadata."
        )

    metadata = _build_metadata(func_info, function_code)
    evaluator = ProofDifficultyEvaluator(llm_name=llm_name)
    try:
        evaluation = evaluator.evaluate(
            fvt_name=global_vars.fvt_name,
            function_name=func_info.name,
            signature=func_info.signature,
            file_path=str(target_file),
            impl_span=metadata["impl_span"],
            metadata={k: v for k, v in metadata.items() if k != "impl_span"},
            function_code=function_code,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(f"Failed to evaluate difficulty: {exc}") from exc

    report_payload = _build_report_payload(
        func_info=func_info,
        evaluation=evaluation,
        metadata=metadata,
        target_file=target_file,
    )
    output_file = _write_report(report_payload, output_path, function_name)

    logger.success(
        f"Proof difficulty for '{func_info.name}': score {evaluation['score']} "
        f"(saved to {output_file})"
    )
    logger.info(f"Rationale: {evaluation['rationale']}")


def _find_function_candidates(
    repo: InfoRepository, function_name: str, file_path: Path
) -> List[RustFunctionInfo]:
    """
    Narrow down candidate functions to the provided file path.
    """

    candidates = repo.get_info_by_name(function_name, RustFunctionInfo)
    matches: List[RustFunctionInfo] = []
    for func_info in candidates:
        loc_file, _, _ = parse_location(func_info.location)
        if not loc_file:
            continue
        resolved = Path(loc_file)
        if not resolved.is_absolute():
            resolved = (global_vars.kverus_path / resolved).resolve()
        else:
            resolved = resolved.resolve()
        if resolved == file_path:
            matches.append(func_info)
    return matches


def _build_metadata(func_info: RustFunctionInfo, function_code: str) -> Dict[str, Any]:
    """
    Collect signal for the prompt + report.
    """

    line_count = len(function_code.splitlines())
    used_fn_count = len(func_info.used_functions)
    used_comp_count = len(func_info.used_composites)
    used_typedef_count = len(func_info.used_typedefs)
    attr = list(func_info.attributes)
    impl_range = func_info.impl_range
    if impl_range[0] and impl_range[1]:
        impl_span = (
            f"{impl_range[0].line}:{impl_range[0].col}"
            f"-{impl_range[1].line}:{impl_range[1].col}"
        )
    else:
        impl_span = "unknown"

    heldby_impl = ""
    if isinstance(func_info.heldby_impl, str):
        heldby_impl = func_info.heldby_impl
    elif func_info.heldby_impl:
        heldby_impl = getattr(func_info.heldby_impl, "name", "")

    trait_bounds = [tb.name for tb in getattr(func_info, "trait_bounds", []) if tb]

    return {
        "impl_span": impl_span,
        "lines_of_code": line_count,
        "used_function_count": used_fn_count,
        "used_composite_count": used_comp_count,
        "used_typedef_count": used_typedef_count,
        "attributes": attr,
        "heldby_impl": heldby_impl,
        "trait_bounds": trait_bounds,
    }


def _build_report_payload(
    *,
    func_info: RustFunctionInfo,
    evaluation: Dict[str, Any],
    metadata: Dict[str, Any],
    target_file: Path,
) -> Dict[str, Any]:
    """
    Assemble the persisted JSON report.
    """

    payload: Dict[str, Any] = {
        "fvt": global_vars.fvt_name,
        "function": func_info.name,
        "signature": func_info.signature,
        "file": str(target_file),
        "impl_span": metadata["impl_span"],
        "metadata": {k: v for k, v in metadata.items() if k != "impl_span"},
        "score": evaluation["score"],
        "rationale": evaluation["rationale"],
        "model": evaluation["model"],
        "evaluated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "raw_response": evaluation["raw_response"],
    }
    if evaluation.get("risk_factors"):
        payload["risk_factors"] = evaluation["risk_factors"]
    if evaluation.get("reasoning"):
        payload["reasoning"] = evaluation["reasoning"]
    return payload


def _write_report(
    payload: Dict[str, Any],
    explicit_path: Optional[Path],
    function_name: str,
) -> Path:
    """
    Persist report JSON to disk and return the resolved path.
    """

    if explicit_path:
        output_file = explicit_path
    else:
        logs_root = global_vars.kverus_path / "logs" / "eval"
        logs_root.mkdir(parents=True, exist_ok=True)
        safe_name = (
            function_name.replace("::", "_")
            .replace("<", "_")
            .replace(">", "_")
            .replace("/", "_")
        )
        output_file = (
            logs_root
            / f"proof-difficulty-{safe_name}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.json"
        )

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    return output_file.resolve()
