"""
Parse Verus error
"""

import json
from loguru import logger
from pathlib import Path
from functools import cached_property

from src.utils import FilePos
from src.prover.fvt import FVT


class VerusTrace:
    """
    Class to represent a Verus trace
    """

    def __init__(self, file: Path, line: int, col: int, message: str, summary: str):
        """
        Initialize the VerusTrace object
        """
        self.file = file
        self.line = line
        self.col = col
        self.message = message
        self.summary = summary

    @cached_property
    def file_pos(self) -> FilePos:
        """
        Get the file position of the trace
        """
        return FilePos(self.file, self.line, self.col)

    def __str__(self):
        return f"{self.message}"


class VerusFileError:
    """
    class to store Verus error clustered by files
    """

    def __init__(self, file_path: Path):
        self.path = file_path
        self.func_errs: dict[str, VerusFuncError] = dict()
        """errors[func_loc] = VerusFuncError"""

        self.errs: list[VerusTrace] = []
        self.last_err: VerusFuncError = None

    def add_error2file(self, func_loc, func_impl_range, verus_trace: VerusTrace):
        if func_loc not in self.func_errs:
            self.func_errs[func_loc] = VerusFuncError(
                self.path, func_loc, func_impl_range
            )
        self.func_errs[func_loc].add_error2func(verus_trace)
        self.errs.append(verus_trace)
        self.last_err = self.func_errs[func_loc]

    def add_note2file(self, verus_trace: VerusTrace):
        if self.last_err == None:
            logger.error(f"Cannot attach note to an error")
        self.last_err.add_error2func(verus_trace)
        self.errs.append(verus_trace)

    def get_func_error_msg(self, func_loc) -> str:
        if func_loc not in self.func_errs:
            logger.error(f"{func_loc} doesn't contain any error")
        return self.func_errs[func_loc].get_func_error_msg()

    def get_file_error_msg(self):
        error_msg = ""
        for verus_trace in self.errs:
            error_msg += f"{verus_trace.message}\n"
        return error_msg


class VerusFuncError:
    """
    class to store Verus error clustered by functions
    """

    def __init__(
        self, file_path: Path, func_loc: str, func_impl_range: tuple[FilePos, FilePos]
    ):
        self.path = file_path
        self.func_loc = func_loc
        self.func_impl = func_impl_range
        self.errors: list[VerusTrace] = []

    def add_error2func(self, verus_trace: VerusTrace):
        self.errors.append(verus_trace)

    def get_func_error_msg(self):
        error_msg = ""
        for verus_trace in self.errors:
            error_msg += f"{verus_trace.message}\n"
        return error_msg


class VerusError:
    """
    Class to parse Verus error logs, extracting errors and their corresponding notes.
    """

    def __init__(self, log_content: str, fvt: FVT):
        """
        Initialize the VerusError instance with the log content.

        :param log_content: The raw Verus error log content, which should be a json str
        :param crate_path: the path of the crate
        """
        self.log_content = log_content
        self.crate_path = fvt.crate_path
        self.parsed_errors = self._parse_log(fvt)

    def _parse_log(self, fvt: FVT) -> dict[Path, VerusFileError]:
        """
        Parse the log content to extract errors and their corresponding notes.

        :return: A list of dictionaries, each containing an error and its notes.
        """
        errors: dict[Path, VerusFileError] = {}
        current_error_file = None
        for line in self.log_content.strip().splitlines():
            try:
                dict_msg = json.loads(line)
            except Exception as e:
                logger.debug(
                    f"Fail to convert verus error log to json due to {e}:\n {line}"
                )
                continue

            dict_spans = dict_msg["spans"]
            if len(dict_spans) == 0:
                continue
            elif len(dict_spans) > 1:
                logger.trace("multiple files found in span" f"{dict_spans}")

            dict_span = dict_spans[-1]
            file_path = Path(dict_span["file_name"])
            if not file_path.is_absolute():
                file_path = fvt.verify_base_path / file_path
            if not file_path.exists():
                logger.critical(f"{file_path} not exists!")

            # ignore all warning
            if dict_msg["level"] == "warning":
                current_error_file = None
                continue
            # keep note following a error
            elif dict_msg["level"] == "note":
                if current_error_file == None:
                    continue
            elif dict_msg["level"] == "error":
                current_error_file = file_path
            else:
                current_error_file = None

            if current_error_file not in errors:
                errors[current_error_file] = VerusFileError(current_error_file)
            verus_trace = VerusTrace(
                file_path,
                dict_span["line_start"],
                dict_span["column_start"],
                dict_msg["rendered"],
                dict_msg["message"],
            )

            if dict_msg["level"] == "error":
                error_line_col = (
                    f'{file_path}:{dict_span["line_start"]}:{dict_span["column_start"]}'
                )
                func_loc, func_impl_range = fvt.find_enclosing_function(
                    FilePos.from_location_line(error_line_col, reload_file=True)
                )
                errors[current_error_file].add_error2file(
                    func_loc, func_impl_range, verus_trace
                )
            elif dict_msg["level"] == "note":
                errors[current_error_file].add_note2file(verus_trace)

        return errors

    @property
    def file_errors(self) -> list[VerusFileError]:
        return list(self.parsed_errors.values())

    @property
    def error_files(self) -> list[Path]:
        """
        The files where the error occurs
        """
        return list(self.parsed_errors.keys())

    @property
    def func_errors(self) -> list[VerusFuncError]:
        """
        The loc of function where the error occurs
        """
        list_verus_func_err = []
        for _, verus_file_error in self.parsed_errors.items():
            for _, verus_func_error in verus_file_error.func_errs.items():
                list_verus_func_err.append(verus_func_error)
        return list_verus_func_err

    def get_error_msg_by_file(self, file: Path) -> str:
        """
        Get the parsed errors and their notes in the file.

        :return: the error message.
        """
        if file not in self.error_files:
            logger.critical(f"{file} not in {self.error_files}")
            return ""
        return self.parsed_errors[file].get_file_error_msg()

    def format_errors(self):
        """
        Format the parsed errors and notes into a readable string.

        :return: A formatted string representation of the errors and notes.
        """
        formatted_output = ""
        for verus_file_err in self.file_errors:
            formatted_output += verus_file_err.get_file_error_msg() + "\n"
        return formatted_output
