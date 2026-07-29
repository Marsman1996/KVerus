import sys
import json
import subprocess
import argparse
import re
from pathlib import Path

KVERUS_PATH = Path(__file__).parent.parent.parent
GRAPH_BENCH_PATH = Path(__file__).parent.parent / "mathspec/code"


def parse_location(location_line: str) -> tuple[str | None, int, int]:
    """
    Parse the location line in the meta file

    :param location_line: The location line
    :return: The parsed location tuple, like: (file, line, col), file set to None if not found
    """
    from parse import parse

    # a location line is like:
    # "file:line:col"
    result = parse("{file}:{line:d}:{col:d}", location_line)
    if result is None:
        return (None, -1, -1)
    return (result["file"], result["line"], result["col"])


def replace_content(file: Path, start_line: int, end_line: int, new_content: str):
    lines = file.read_text().splitlines()
    new_lines = lines[: start_line - 1] + new_content.splitlines() + lines[end_line:]
    file.write_text("\n".join(new_lines))


def parse_logs():
    """Parse log files and extract token statistics"""
    log_dir = KVERUS_PATH / "logs"
    # log_dir = GRAPH_BENCH_PATH.parent / "out/logs"

    list_logs = list(log_dir.glob("*.log"))
    list_logs.sort(key=lambda x: x.name, reverse=True)

    cnt_pre = 0
    total_query_times = 0
    total_input_tokens = 0
    total_output_tokens = 0

    for log_path in list_logs:
        if log_path.name.find("_preprocess.log") >= 0:
            cnt_pre += 1
            if cnt_pre >= 2:
                break
        else:
            cnt_pre = 0

        if log_path.name.find("prove_--disable_all_admit") < 0:
            continue
        lines = log_path.read_text().splitlines()
        match = re.search(
            r"Total query times:\s*(\d+),\s*total tokens:\s*(\d+)\s*->\s*(\d+)",
            lines[-1],
        )
        if match:
            query_times = int(match.group(1))
            input_tokens = int(match.group(2))
            output_tokens = int(match.group(3))

            total_query_times += query_times
            total_input_tokens += input_tokens
            total_output_tokens += output_tokens

            print(f"File: {log_path.name}")
            print(f"  Query times: {query_times}")
            print(f"  Input tokens: {input_tokens}")
            print(f"  Output tokens: {output_tokens}")

        # new_path = KVERUS_PATH / "database/mathspec/out/logs" / log_path.name
        # if new_path.parent.exists() == False:
        #     new_path.parent.mkdir(parents=True)
        # log_path.rename(new_path)

    print(f"\nSummary:")
    print(f"Total query times: {total_query_times}")
    print(f"Total input tokens: {total_input_tokens}")
    print(f"Total output tokens: {total_output_tokens}")


def run_mathspec(disable: str):
    """Run the main mathspec functionality with optional disable flags"""
    info_path = Path(__file__).parent.parent / "mathspec/out/preprocessor-ori/info.json"

    func_info = json.loads(info_path.read_text())["function_infos"]
    dict_file_loc: dict[str, list[str]] = dict()

    lemma_cnt = 0
    for func_dict in func_info.values():
        if func_dict["name"].find("lemma_") >= 0:
            _, start_line, start_col = parse_location(func_dict["impl_range"][0])
            file, end_line, end_col = parse_location(func_dict["impl_range"][1])
            path_file = Path(file)
            function_context = path_file.read_text().splitlines()[
                start_line - 1 : end_line
            ]
            if function_context[-1].find("}") >= 0:
                dict_file_loc.setdefault(file, []).append(func_dict["location"])
                lemma_cnt += 1

    def prove(lemma_loc: str) -> bool:
        print(lemma_loc)
        func_dict = func_info[lemma_loc]

        # replace the original proof with admit
        lemma_signature = func_dict["signature"]
        _, start_line, start_col = parse_location(func_dict["impl_range"][0])
        file, end_line, end_col = parse_location(func_dict["impl_range"][1])
        replace_content(
            Path(file),
            start_line,
            end_line,
            f"{lemma_signature} {{ admit(); }}",
        )

        # run preprocess again
        subprocess.run(
            [
                "uv",
                "run",
                "--",
                "python",
                "./KVerus.py",
                "-D",
                "-F",
                "./database/mathspec/fvts.toml",
                "preprocess",
            ],
            cwd=KVERUS_PATH,
        )

        # run prove for admit lemma
        subprocess.run(
            [
                "uv",
                "run",
                "--",
                "python",
                "./KVerus.py",
                "-D",
                "-F",
                "./database/mathspec/fvts.toml",
                "prove",
                "--disable",
                disable,
                "admit",
                "--fvt",
                "graph",
                "--file",
                str(Path(file).resolve()),
            ],
            cwd=KVERUS_PATH,
        )

        # run verification to check whether success
        result = subprocess.run(["cargo", "xtask", "verify"], cwd=GRAPH_BENCH_PATH)
        is_success = result.returncode == 0

        # Run git restore
        subprocess.run(["git", "restore", "."], cwd=GRAPH_BENCH_PATH)
        return is_success

    print(f"Total lemma functions: {lemma_cnt}")
    list_success = []
    cnt_success = 0
    for file in dict_file_loc:
        # print(f"File: {file}")
        # print(f"Lemma functions: {dict_file_loc[file]}")
        for lemma_loc in dict_file_loc[file]:
            is_success = prove(lemma_loc)
            if is_success:
                list_success.append(lemma_loc)
                cnt_success += 1
            # print(Path(__file__).parent)
            # Now I will run git checkout

    print(json.dumps(list_success, indent=2))
    print(f"Total success: {cnt_success} out of {lemma_cnt}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="MathSpec tool for running and parsing"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Add run command
    run_parser = subparsers.add_parser("run", help="Run the mathspec functionality")
    # Add disable option to the run command
    run_parser.add_argument(
        "--disable",
        choices=["code", "lemma", "verus", "all"],
        help="Disable specific parts of the run functionality",
    )

    # Add parse command
    parse_parser = subparsers.add_parser(
        "parse", help="Parse log files and extract token statistics"
    )

    args = parser.parse_args()

    if args.command == "run":
        run_mathspec(disable=args.disable)
    elif args.command == "parse":
        parse_logs()
    else:
        parser.print_help()
