import re
import ast
import json
import click
import hashlib
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from pathlib import Path
from loguru import logger


VERUSBENCH_PATH = Path(__file__).parent.parent / "Verus-Bench/code/code"


@click.group()
def cli():
    """AutoVerus Script - Verifying with AutoVerus."""
    pass


@cli.command()
@click.argument(
    "crate_path",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, path_type=Path, resolve_path=True
    ),
)
@click.option(
    "--output_path",
    "-o",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path, resolve_path=True),
    default=".",
    help="Path to the output directory for parsed results.",
)
@click.option(
    "--workers",
    "-j",
    type=int,
    default=5,
    help="Number of parallel workers to use.",
)
def run_dir(crate_path: Path, output_path: Path, workers: int):
    """
    Run AutoVerus on the specified crate and output results to the given directory.

    :param crate_path: Path to the Rust crate directory.
    :param output_path: Path to the output directory for results.
    """
    if not output_path.exists():
        output_path.mkdir(parents=True, exist_ok=True)
    cnt = 0
    prove_cnt = 0
    total_prompt = 0
    total_completion = 0
    list_files = sorted(Path(crate_path).glob("*.rs"))

    def _process_file(verus_file: Path):
        if not verus_file.is_file():
            return verus_file, False, 0, 0
        logger.info(f"Processing Verus file: {verus_file}")
        try:
            prove_res, prompt_tokens, completion_tokens = prove(verus_file, output_path)
        except Exception as e:
            logger.exception(f"Exception while processing {verus_file}: {e}")
            return verus_file, False, 0, 0
        return verus_file, prove_res, prompt_tokens or 0, completion_tokens or 0

    if not list_files:
        logger.warning("No .rs files found to process.")
    else:
        logger.info(
            f"Starting parallel processing with {workers} workers for {len(list_files)} files…"
        )
        with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
            future_map = {executor.submit(_process_file, f): f for f in list_files}
            total = len(future_map)
            with tqdm(total=total, desc="Verifying", unit="file") as pbar:
                for future in as_completed(future_map):
                    verus_file, prove_res, prompt_tokens, completion_tokens = (
                        future.result()
                    )
                    cnt += 1
                    if prove_res:
                        prove_cnt += 1
                    total_prompt += prompt_tokens
                    total_completion += completion_tokens
                    pbar.set_postfix(
                        {
                            "proved": prove_cnt,
                            "tokens": f"{total_prompt}/{total_completion}",
                        },
                        refresh=False,
                    )
                    pbar.update(1)
    logger.info(f"Proved {prove_cnt}/{cnt} files successfully.")
    logger.info(f"Total prompt tokens: {total_prompt}")
    logger.info(f"Total completion tokens: {total_completion}")


@cli.command()
@click.argument(
    "target_file",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, path_type=Path, resolve_path=True
    ),
)
@click.option(
    "--output_path",
    "-o",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path, resolve_path=True),
    default=".",
    help="Path to the output directory for parsed results.",
)
def run_file(target_file: Path, output_path: Path):
    """
    Run AutoVerus on a single Verus file in the specified crate and output results to the given directory.

    :param target_file: Path to the Verus file to be proven.
    :param output_path: Path to the output directory for results.
    """
    if not output_path.exists():
        output_path.mkdir(parents=True, exist_ok=True)
    prove(target_file, output_path)


def prove(target_path: Path, output_path: Path):
    """
    Prove a Verus target file and output results to the specified directory.

    :param target_path: Path to the Verus target file.
    :param output_path: Path to the output directory for results.
    :return: A tuple containing:
             - A boolean indicating if the proof was successful.
             - The number of prompt tokens used.
             - The number of completion tokens used.
    """
    cmd = [
        "uv",
        "run",
        "--",
        "python",
        "main.py",
        "--input",
        str(target_path),
        "--output",
        f"{output_path}/{target_path.name}",
        "--config",
        "./config.json",
    ]
    logger.info(f"Running command: {' '.join(cmd)}")
    res = subprocess.run(
        cmd,
        cwd=VERUSBENCH_PATH,
        capture_output=True,
        text=True,
    )
    hash_val = hashlib.md5(str(target_path).encode()).hexdigest()
    stdout_file = output_path / f"{hash_val}.llm"
    stdout_file.write_text(res.stdout, encoding="utf-8")
    stderr_file = output_path / f"{hash_val}.log"
    stderr_file.write_text(res.stderr, encoding="utf-8")
    completion_tokens, prompt_tokens, query_cnt = parse_file(stdout_file)
    sanitized = True if res.stderr.find("Verus succeeded") >= 0 else False
    dict_res = {
        "completion_tokens": completion_tokens,
        "prompt_tokens": prompt_tokens,
        "crate_path": "",
        "verify_cmd": f"database/CortenMM/code/tools/verus/source/target-verus/release/verus {output_path}/{target_path.name} --error-format=json",
        "query_count": query_cnt,
        "remain_san_rounds": 0,
        "sanitized": sanitized,
    }
    res_file = output_path / f"{hash_val}.json"
    res_file.write_text(json.dumps(dict_res, indent=4), encoding="utf-8")
    if res.returncode != 0:
        logger.error(f"Command failed with return code {res.returncode}")
        logger.error(f"Stderr: {res.stderr}")
    else:
        logger.success(f"Command succeeded. Output written to {stdout_file.resolve()}")
        logger.info(f"Sanitized: {sanitized}")
        logger.info(f"result written to {res_file}")
    return sanitized, prompt_tokens, completion_tokens


@cli.command()
@click.option(
    "--verus_dir",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, path_type=Path, resolve_path=True
    ),
)
@click.argument(
    "res_path",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, path_type=Path, resolve_path=True
    ),
)
def parse(verus_dir: Path, res_path: Path):
    """
    Parse the results of Verus verification and output a summary.
    This function now primarily extracts and logs completion and prompt token counts.
    """
    dict_summary = {
        "pass_cnt": 0,
        "fail_cnt": 0,
        "completion_tokens": 0,
        "prompt_tokens": 0,
    }
    for verus_file in verus_dir.glob("*.rs"):
        hash_val = hashlib.md5(str(verus_file).encode()).hexdigest()
        llm_res_file = res_path / f"{hash_val}.llm"
        log_file = res_path / f"{hash_val}.log"
        if not llm_res_file.exists():
            continue
        logger.info(f"Parsing result file: {llm_res_file.name} for {verus_file.name}")
        completion_tokens, prompt_tokens, query_cnt = parse_file(llm_res_file)
        dict_summary["completion_tokens"] += completion_tokens
        dict_summary["prompt_tokens"] += prompt_tokens
        sanitized = True if log_file.read_text().find("Verus succeeded") >= 0 else False
        dict_res = {
            "completion_tokens": completion_tokens,
            "prompt_tokens": prompt_tokens,
            "crate_path": "",
            "verify_cmd": f"database/CortenMM/code/tools/verus/source/target-verus/release/verus {res_path}/{verus_file.name} --error-format=json",
            "query_count": query_cnt,
            "remain_san_rounds": 0,
            "sanitized": sanitized,
        }
        dict_summary[verus_file.name] = dict_res
        dict_summary["pass_cnt"] += 1 if sanitized else 0
        dict_summary["fail_cnt"] += 0 if sanitized else 1
        json_file = res_path / f"{hash_val}.json"
        if not json_file.exists():
            json_file.write_text(json.dumps(dict_res, indent=4), encoding="utf-8")
    summary_file = res_path / "summary.json"
    summary_file.write_text(json.dumps(dict_summary, indent=4), encoding="utf-8")
    logger.success(f"Parsing completed. Summary written to {summary_file}")


def parse_file(file_path: Path):
    completion_tokens = 0
    prompt_tokens = 0
    query_cnt = 0
    content = file_path.read_text(encoding="utf-8")
    for line in content.splitlines():
        if line.startswith("ChatCompletion(id="):
            # Extract the content part after "content:"
            _completion_tokens, _prompt_tokens = extract_tokens(line)
            completion_tokens += _completion_tokens
            prompt_tokens += _prompt_tokens
            query_cnt += 1
    logger.info(f"{prompt_tokens} + {completion_tokens}")
    return completion_tokens, prompt_tokens, query_cnt


def extract_tokens(content: str):
    completion_tokens = None
    prompt_tokens = None

    # Attempt 1: Parse with ast.literal_eval (if content is a string representation of a Python dict/list)
    try:
        parsed_data = ast.literal_eval(content)
        if isinstance(parsed_data, dict):
            usage_info = parsed_data.get("usage")
            if isinstance(usage_info, dict):
                ct = usage_info.get("completion_tokens")
                pt = usage_info.get("prompt_tokens")
                if ct is not None:
                    try:
                        completion_tokens = int(ct)
                    except ValueError:
                        logger.warning(
                            f"Could not convert completion_tokens '{ct}' to int"
                        )
                if pt is not None:
                    try:
                        prompt_tokens = int(pt)
                    except ValueError:
                        logger.warning(f"Could not convert prompt_tokens '{pt}' to int")

    except (
        Exception
    ):  # Catches errors from ast.literal_eval (e.g., malformed string, or not a literal)
        # logger.debug(f"ast.literal_eval failed. Relying on regex.")
        pass  # Errors are expected if content is not a simple literal string, proceed to regex.

    # Attempt 2: Regex extraction (acts as primary if ast.literal_eval fails or doesn't find them)
    if completion_tokens is None:
        match_ct = re.search(r"completion_tokens=(\d+)", content)
        if match_ct:
            try:
                completion_tokens = int(match_ct.group(1))
            except ValueError:
                logger.warning(
                    f"Could not convert regex-captured completion_tokens '{match_ct.group(1)}' to int"
                )

    if prompt_tokens is None:
        match_pt = re.search(r"prompt_tokens=(\d+)", content)
        if match_pt:
            try:
                prompt_tokens = int(match_pt.group(1))
            except ValueError:
                logger.warning(
                    f"Could not convert regex-captured prompt_tokens '{match_pt.group(1)}' to int"
                )

    # Log the required token information
    if completion_tokens is not None and prompt_tokens is not None:
        logger.debug(
            f"Completion Tokens: {completion_tokens}, Prompt Tokens: {prompt_tokens}"
        )
    else:
        missing_parts = []
        if completion_tokens is None:
            missing_parts.append("completion_tokens")
        if prompt_tokens is None:
            missing_parts.append("prompt_tokens")

        if missing_parts:
            logger.warning(f"Could not extract {', '.join(missing_parts)}.")
    # Previous logic for extracting and logging the main "content" of the message has been removed.
    return completion_tokens, prompt_tokens


if __name__ == "__main__":
    cli()
