"""
Prompter for LLM
"""

from loguru import logger
from abc import ABC, abstractmethod
import re
import json
from functools import cache

from src.utils import concat_excerpts
from src import vars as global_vars
from . import llm
from .rag import RAGExcerpt


class Prompter(ABC):
    """
    Prompt LLM for information
    """

    def __init__(self, llm_chat: llm.LLMChat):
        """
        Initialize prompter

        :param llm_chat: LLM chat
        """
        self.chat = llm_chat
        self.language_tag = (
            "c"
            if global_vars.fvt_language == global_vars.SupportedLanguages.C
            else "cpp"
        )
        self._load_prompt()

    @abstractmethod
    def _load_prompt(self): ...

    @abstractmethod
    def prompt(self): ...

    def set_system_prompt(self, system_prompt: str):
        """
        Set system prompt

        :param system_prompt: System prompt
        """
        self.chat.system_prompt = system_prompt

    @staticmethod
    @cache
    def _read_prompt(prompt_file_name: str) -> str:
        """
        Read prompt from file, cached

        :param prompt_file_name: Prompt file name
        :return: Prompt content
        """
        PROMPT_PATH = global_vars.kverus_path / "src" / "prompt"
        return (PROMPT_PATH / prompt_file_name).read_text(encoding="utf-8")

    @staticmethod
    def parse_code_from_llm_output(response: str, warning: bool = True) -> str:
        """
        Parse ```LANGUAGE\nCODE\n``` from LLM output

        :param response: LLM output
        :return: Code
        """
        from parse import search

        code = search("```{lang}\n{code}\n```", response)
        code = (
            code if code else search("```\n{code}\n```", response)
        )  # try without language

        if code is None:
            if warning:
                logger.warning("No code found in LLM output")
                return ""
            else:
                return response
        return code["code"]

    @staticmethod
    def parse_indexes_from_llm_output(response: str, candidate_num: int) -> list[int]:
        """
        Parse indexes from LLM output, discard invalid indexes

        :param response: LLM output, indexes start from 1
        :param candidate_num: Number of candidates
        :return: Indexes, start from 0
        """
        indexes = re.findall(r"\d+", response)
        filtered_indexes = set()
        for index_str in indexes:
            index = int(index_str) - 1
            if index < 0:
                # 0 for none of the above
                continue
            if index >= candidate_num:
                logger.warning(
                    f"Index {index} from LLM output is out of range, discarding"
                )
                continue
            filtered_indexes.add(index)
        return list(filtered_indexes)

    @staticmethod
    def economize_prompt(prompt: str) -> str:
        """
        Remove unnecessary spaces and newlines from prompt to save token usage

        :param prompt: Prompt
        :return: Economized prompt
        """
        import re

        # replace all tabs with spaces
        prompt = prompt.replace("\t", " ")

        # remove trailing spaces at each line
        prompt = "\n".join([line.rstrip() for line in prompt.split("\n")])

        # consolidate more than 2 newlines to 2 newlines
        prompt = re.sub(r"\n{3,}", "\n\n", prompt)

        # consolidate more than 1 spaces to 1 spaces
        prompt = re.sub(r" {2,}", " ", prompt)

        return prompt

    @staticmethod
    def format_code(
        code: str,
        style: str = r"{BasedOnStyle: Google, ColumnLimit: 0, IndentWidth: 2, UseTab: Never}",
    ) -> str:
        """
        Format C/C++ code

        :param code: Code
        :return: Formatted code
        """
        import subprocess

        if not hasattr(Prompter, "clang_installed"):
            # detect clang-format
            try:
                subprocess.run(
                    ["clang-format", "--version"],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                Prompter.clang_installed = True
            except:
                logger.debug(f"clang-format not installed, will not format code")
                Prompter.clang_installed = False
        if not Prompter.clang_installed:
            return code

        # format code
        try:
            formatted_code = subprocess.run(
                ["clang-format", f"-style={style}"],
                input=code.encode(),
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ).stdout.decode()
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to format code: {e.stderr.decode()}")
            return code

        return formatted_code


class LibPurposePrompter(Prompter):
    """
    Prompter to deduce the purpose of a library
    """

    def _load_prompt(self):
        """
        Load deduce library purpose prompt
        """
        self.system_prompt = self._read_prompt("deduce_library_purpose.sys")
        self.user_prompt = self._read_prompt("deduce_library_purpose.usr")

    def prompt(self, library_name: str, document_excerpts: list[RAGExcerpt]) -> str:
        """
        Prompt LLM for deducing library purpose

        :param library_name: Name of the library
        :param document_excerpts: Excerpts from the library document
        :return: Deduced library purpose
        """
        # concatenate all excerpts
        excerpts_str = concat_excerpts(document_excerpts)

        # set system prompt
        system_prompt = self.system_prompt.format(
            LIBRARY_NAME=library_name,
        )
        self.set_system_prompt(system_prompt)

        # set user prompt
        user_prompt = self.user_prompt.format(
            LIBRARY_NAME=library_name,
            DOC_EXCERPTS=excerpts_str,
        )

        # query LLM
        summary = self.chat.query(user_prompt)

        return summary


class LemmaSummaryFromSrcPrompter(Prompter):
    """
    Prompter to deduce the lemma summary from source code
    """

    def _load_prompt(self):
        """
        Load deduce lemma summary prompt
        """
        self.system_prompt = self._read_prompt("deduce_lemma_summary.sys")
        self.user_prompt = self._read_prompt("deduce_lemma_summary.usr")

    def prompt(
        self,
        library_name: str,
        lemma_name: str,
        lemma_signature: str,
        # function_source_code: str,
    ) -> str:
        """
        Prompt LLM for deducing lemma summary

        :param library_name: Name of the library
        :param function_name: Name of the function
        :param function_signatures: Signatures of the function
        :param function_source_code: Source code of the function
        :return: Deduced function usage
        """
        # set system prompt
        system_prompt = self.system_prompt.format(
            LIBRARY_NAME=library_name,
        )
        self.set_system_prompt(system_prompt)

        # set user prompt
        user_prompt = self.user_prompt.format(
            LEMMA_NAME=lemma_name,
            LEMMA_SIGNATURE=lemma_signature,
            # FUNCTION_SOURCE_CODE=self.format_code(function_source_code),
        )

        # query LLM
        response = self.chat.query(user_prompt)

        return response


class FixPrompter(Prompter):
    """
    Prompt LLM for fixing
    """

    # to be implemented by subclasses
    def _load_prompt(self): ...

    def prompt(self, error_message: str) -> str:
        """
        Prompt LLM for fixing

        :param error_message: Error message
        :return: Fixed code
        """
        user_prompt = self.fix_prompt.format(ERROR_MESSAGE=error_message)
        fixed_code = self.chat.query(user_prompt)
        return Prompter.parse_code_from_llm_output(fixed_code)


class FixFVTPrompter(Prompter):
    """
    Prompt LLM for fixing Formal Verification Target error
    """

    def _load_prompt(self):
        self.sys_prompt = self._read_prompt("fix_fvt_error.sys")
        self.usr_prompt = self._read_prompt("fix_fvt_error.usr")

    def prompt(self, verus_code: str, error_message: str, knowledge: str = "") -> str:
        """
        Prompt LLM for fixing Formal Verification Target error

        :param verus_code: Verus code
        :param error_message: Error message
        :return: Fixed code
        """
        self.set_system_prompt(self.sys_prompt)
        user_prompt = self.usr_prompt.format(
            VERUS_CODE=verus_code, ERROR_MESSAGE=error_message, KNOWLEDGE=knowledge
        )
        fixed_code = self.chat.query(user_prompt)
        return Prompter.parse_code_from_llm_output(fixed_code)


class FixFVTSimplePrompter(FixFVTPrompter):
    """
    Prompter to fix Formal Verification Target error with a simpler prompt
    """

    def _load_prompt(self):
        """
        Load fix Formal Verification Target error prompt
        """
        self.sys_prompt = self._read_prompt("fix_fvt_error.sys.simple")
        self.usr_prompt = self._read_prompt("fix_fvt_error.usr")


class VerusErrorAnalysisPrompter(Prompter):
    """
    Prompter to analyze Verus errors
    """

    def _load_prompt(self):
        """
        Load analyze Verus error prompt
        """
        self.system_prompt = self._read_prompt("analyze_verus_error.sys")
        self.user_prompt = self._read_prompt("analyze_verus_error.usr")

    def prompt(self, error_message: str) -> str:
        self.set_system_prompt(self.system_prompt)
        # query LLM
        # first query for explanation
        output = self.chat.query(self.user_prompt.format(ERROR_MESSAGE=error_message))
        return output


class VerusAnalyzeAdmitPrompter(Prompter):
    """
    Prompter to select lemma to prove Verus
    """

    def _load_prompt(self):
        """
        Load analyze Verus error prompt
        """
        # self.system_prompt = self._read_prompt("analyze_admit.sys")
        user_prompt = self._read_prompt("analyze_admit.usr")
        common_txt = self._read_prompt("analyze.common")
        self.user_prompt = user_prompt.format(COMMON_CODE=common_txt)

    def prompt(self, verus_code: str) -> str:
        # self.set_system_prompt(self.sys_prompt)
        # knowledge = self._read_prompt("fix_fvt_error.know")
        user_prompt = self.user_prompt.format(VERUS_CODE=verus_code)
        output = self.chat.query(user_prompt)
        return self.parse_code_from_llm_output(output)


class VerusAnalyzeProvePrompter(Prompter):
    """
    Prompter to select lemma to prove Verus
    """

    def _load_prompt(self):
        """
        Load analyze Verus error prompt
        """
        user_prompt = self._read_prompt("analyze_prove.usr")
        common_txt = self._read_prompt("analyze.common")
        self.user_prompt = user_prompt.format(
            COMMON_CODE=common_txt, ERROR_MESSAGE="{ERROR_MESSAGE}"
        )

    def prompt(self, verus_code: str, error_msg: str) -> str:
        output = self.chat.query(
            self.user_prompt.format(VERUS_CODE=verus_code, ERROR_MESSAGE=error_msg)
        )
        return self.parse_code_from_llm_output(output)


class VerusProveAdmitPrompter(Prompter):
    """
    Prompter to prove Verus admit
    """

    def _load_prompt(self):
        """
        Load analyze Verus error prompt
        """
        # self.system_prompt = self._read_prompt("analyze_verus_error.sys")
        self.user_prompt = self._read_prompt("prove_admit.usr")

    def prompt(self, verus_code: str, knowledge: str) -> str:
        output = self.chat.query(
            self.user_prompt.format(VERUS_CODE=verus_code, KNOWLEDGE=knowledge)
        )
        return self.parse_code_from_llm_output(output)


class VerusProvePrompter(Prompter):
    """
    Prompter to prove Verus admit
    """

    def _load_prompt(self):
        """
        Load analyze Verus error prompt
        """
        self.sys_prompt = self._read_prompt("prove.sys")
        self.user_prompt = self._read_prompt("prove.usr")

    def prompt(self, verus_code: str, err_msg: str, knowledge: str) -> str:
        self.set_system_prompt(self.sys_prompt)
        output = self.chat.query(
            self.user_prompt.format(
                VERUS_CODE=verus_code, ERROR_MESSAGE=err_msg, KNOWLEDGE=knowledge
            )
        )
        return self.parse_code_from_llm_output(output)


class VerusProveSimplePrompter(VerusProvePrompter):
    """
    Prompter to prove Verus admit with a simpler prompt
    """

    def _load_prompt(self):
        """
        Load analyze Verus error prompt
        """
        self.sys_prompt = self._read_prompt("prove.sys.simple")
        self.user_prompt = self._read_prompt("prove.usr")


class ReportFailPrompter(Prompter):
    """
    Prompter to generate report for failing reason
    """

    def _load_prompt(self):
        """
        Load generate report prompt
        """
        self.user_prompt = self._read_prompt("report_fail.usr")

    def prompt(
        self,
        max_refine_rounds: int,
        ori_code: str,
        gen_code: str,
        err_msg: str,
        knowledge: str,
    ) -> str:
        self.set_system_prompt("")
        output = self.chat.query(
            self.user_prompt.format(
                MAX_REFINE_ROUNDS=max_refine_rounds,
                ORI_CODE=ori_code,
                GEN_CODE=gen_code,
                ERROR_MESSAGE=err_msg,
                KNOWLEDGE=knowledge,
            )
        )
        return output


class ValidatePrompter(Prompter):
    """
    Prompter to validate the generated formal verification target (FVT) code
    """

    def _load_prompt(self):
        """
        Load validate FVT code prompt
        """
        self.user_prompt = self._read_prompt("validate_code.usr")

    def prompt(self, ori_code: str, gen_code: str) -> str:
        """
        Prompt LLM to validate the FVT code.

        :param ori_code: The original source code.
        :param gen_code: The generated FVT code.
        :return: True if the code is valid, False otherwise.
        """
        self.set_system_prompt("")
        output = self.chat.query(
            self.user_prompt.format(
                ORI_CODE=ori_code,
                GEN_CODE=gen_code,
            )
        )

        return self.parse_code_from_llm_output(output)
