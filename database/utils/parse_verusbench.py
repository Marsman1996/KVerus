import sys
import json
import argparse
import re
from pathlib import Path
from loguru import logger
from collections import OrderedDict

if __name__ == "__main__":
    logger.info("Parsing VerusBench results...")
    parser = argparse.ArgumentParser(description="Parse VerusBench results.")
    parser.add_argument(
        "input_path", type=Path, help="Path to the VerusBench results directory."
    )
    args = parser.parse_args()
    input_path = args.input_path
    output_path = input_path
    res_summary = {"pass_cnt": 0, "fail_cnt": 0, "details": {}}
    for res_file in input_path.rglob("*.json"):
        if not res_file.is_file():
            continue
        if res_file.name in ["verusbench_summary.json", "summary.json"]:
            continue
        res = json.loads(res_file.read_text(encoding="utf-8"))
        res_summary["details"][Path(res["verify_cmd"].split(" ")[1]).name] = {
            "sanitized": res["sanitized"],
            "query_count": res["query_count"],
        }
        if res["sanitized"] == True:
            res_summary["pass_cnt"] += 1
        else:
            res_summary["fail_cnt"] += 1

    def extract_task_id(filename):
        # extract ID from filename using regex
        match = re.search(r"task_id_(\d+)\.rs", filename)
        if match:
            return int(match.group(1))
        return filename

    sorted_details = OrderedDict(
        sorted(res_summary["details"].items(), key=lambda x: extract_task_id(x[0]))
    )
    res_summary["details"] = sorted_details

    logger.success(f"Passed: {res_summary['pass_cnt']}")
    logger.error(f"Failed: {res_summary['fail_cnt']}")
    out_file = output_path / "verusbench_summary.json"
    out_file.write_text(
        json.dumps(
            res_summary,
            indent=4,
        ),
        encoding="utf-8",
    )

    # Output all failed tasks
    failed_tasks = [
        task
        for task, details in res_summary["details"].items()
        if not details["sanitized"]
    ]
    if len(failed_tasks) > 0:
        logger.error("Failed tasks:")
        for task in failed_tasks:
            task_path = Path(
                f"database/Verus-Bench/code/benchmarks/MBPP/unverified/{task}"
            ).resolve()
            logger.error(f"- {task_path}")
    else:
        logger.success("All tasks passed.")
    logger.info(f"Results written to {out_file.resolve()}")

    for task_name, detail in res_summary["details"].items():
        print(
            f"{task_name.rstrip(".rs")} {detail['query_count']} {detail['sanitized']}"
        )
