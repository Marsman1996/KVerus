import argparse
from functools import lru_cache
import re


def extract_verus_error_message(input_text):
    """
    Extracts the Verus error message from the given input text.

    Args:
        input_text (str): The input text containing Verus error messages.

    Returns:
        list: A list of extracted error messages.
    """
    error_messages = []

    # Regular expression to match error messages
    error_block_pattern = re.compile(r"## Verus Error Message\n```(.*?)```", re.DOTALL)

    # Find all matches for the error block
    matches = error_block_pattern.findall(input_text)

    for match in matches:
        error_messages.append(match.strip())

    if error_messages == []:
        error_messages.append(input_text)

    return error_messages


def extract_errors_from_file(file_path):
    """
    Reads a log file and extracts Verus error messages.

    Args:
        file_path (str): The path to the log file.

    Returns:
        list: A list of extracted error messages.
    """
    try:
        with open(file_path, "r") as file:
            content = file.read()
        return extract_verus_error_message(content)
    except FileNotFoundError:
        print(f"Error: The file {file_path} does not exist.")
        return []
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        return []


def merge_dicts(dict1: dict[str, float], dict2: dict[str, float]) -> dict[str, float]:
    """Merge two dictionaries by summing values of matching keys."""
    merged = dict1.copy()
    for key, value in dict2.items():
        if key in merged:
            merged[key] += value
        else:
            merged[key] = value
    return merged


ERROR_PATTERNS = {
    "Decreases Missing": (
        "loop must have a decreases clause",
        "recursive function must have a decreases clause",
    ),
    "Type Mismatched": ("mismatched types", "type annotations needed"),
    "Wrong Variable Mode": (
        "with mode exec",
        "The Verus types ",
        "cannot use while in proof or spec mode",
    ),
    "Wrong Token": (
        "expected `,`",
        "but its trait bounds were not satisfied",
        "cannot find",
        "expected an expression",
        "no method named",
        "unexpected token",
    ),
    "Trigger": (
        "Could not automatically infer triggers",
        "trigger must be a function call",
        "in trigger cannot appear in both",
        "let variables in triggers not supported",
    ),
    "Arithmetic Overflow": ("possible arithmetic",),
    "Unsatisfied Condition": (
        "postcondition not satisfied",
        "precondition not satisfied",
        "requires not satisfied",
    ),
    "Loop Invariant": (
        "invariant not satisfied",
        "decreases not satisfied at end of loop",
        "while loop: Resource limit",
    ),
    "Assert Failure": ("assertion failed",),
}


@lru_cache(maxsize=4096)
def classify(err_msg: str) -> str:
    """Return the coverage category for a given file path string.

    Falls back to "other" when no pattern matches.
    """
    for category, patterns in ERROR_PATTERNS.items():
        if any(p in err_msg for p in patterns):
            return category
    print(err_msg)
    return "other"


def analyze_error_messages(list_messages: list[str]) -> dict[str, int]:
    from collections import defaultdict

    dict_err: dict[str, int] = defaultdict(int)
    cnt = 0
    for err_msg in list_messages:
        for line in err_msg.splitlines():
            if not line.startswith("error"):
                continue
            if line.find("aborting due to") >= 0 and line.find("previous error") >= 0:
                continue
            cnt += 1
            dict_err[classify(line)] += 1

    print(f"Total error lines: {cnt}")

    return dict_err


# Example usage
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract Verus error messages from a log file."
    )
    parser.add_argument(
        "log_file_path",
        type=str,
        help="Path to the log file containing Verus error messages.",
    )
    args = parser.parse_args()

    errors = extract_errors_from_file(args.log_file_path)

    if errors:
        dict_err = analyze_error_messages(errors)
        print("\n---Error Summary:")
        for err_key in ERROR_PATTERNS.keys():
            if err_key in dict_err:
                print(f"{err_key}: {dict_err[err_key]}")
            else:
                print(f"{err_key}: 0")
    else:
        print("No error messages found.")
