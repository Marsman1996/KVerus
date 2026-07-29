"""
Comprehend the library

INPUT: document retriever, api function names and signatures
OUTPUT: library purpose, function usage, function relevance
1. Retrieve to obtain the library purpose.
2. For each API function, retrieve its usage. Provide the retrieved document excerpts to the LLM,
and ask it whether these describe the usage of a certain function.
If they do, ask the LLM to describe the function's usage based on documents and source code.
3. For API functions without documentation, use the LLM to infer the usage based on source code.
4. Provide the LLM with the signature and usage of each function, and let it select relevant functions.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from tqdm import tqdm
from loguru import logger
from functools import cached_property
from dataclasses import dataclass, asdict
import pickle
import json
from concurrent.futures import ThreadPoolExecutor
import threading
import time
from typing import Any, ClassVar

from src.utils import concat_excerpts, with_progress_update
from src import vars as global_vars
from src.llm.llm import LLMClient, LLMChat
from src.llm.prompter import LibPurposePrompter, LemmaSummaryFromSrcPrompter
from src.preprocessor.information import InfoRepository, RustFunctionInfo
from src.preprocessor.lemma import LemmaCollection
from .knowledge import Knowledge, RAGExcerpt


class Comprehender(ABC):
    """
    Base class for comprehenders
    """

    # pool size for parallel processing
    pool_size: int = 1

    @cached_property
    def comprehension(self) -> Any:
        return self.comprehend()

    @abstractmethod
    def comprehend(self): ...


@dataclass
class LibraryComprehension:
    """
    Dataclass to store the library comprehension
    """

    purpose: str
    """
    Library purpose
    """

    functions: dict[str, str]
    """
    Function comprehensions about their usage
    as function name: function usage
    """

    def dump(self, path: Path):
        """
        Dump the library comprehension to a file

        :param path: Path to dump the library comprehension
        """
        with open(path, "wb") as f:
            pickle.dump(self, f)

    def dump_json(self, path: Path):
        """
        Dump the library comprehension to a JSON file, only for human-readable purpose

        :param path: Path to dump the library comprehension
        """

        class CompJSONEncoder(json.JSONEncoder):
            def default(self, o):
                if isinstance(o, LibraryComprehension):
                    return asdict(o)
                else:
                    return super().default(o)

        with open(path, "w") as f:
            json.dump(self, f, cls=CompJSONEncoder, indent=4)

    @classmethod
    def load(cls, path: Path) -> "LibraryComprehension":
        """
        Load the library comprehension from a file

        :param path: Path to load the library comprehension
        :return: The library comprehension
        """
        with open(path, "rb") as f:
            return pickle.load(f)


class GeneralComprehender(Comprehender):
    """
    Comprehend all the information about the library, used to invoke all the comprehenders
    """

    # flags to control the comprehender
    DO_LIBRARY_PURPOSE: ClassVar[bool] = True
    DO_LEMMA_USAGE: ClassVar[bool] = True

    def __init__(
        self,
        llm_client: LLMClient,
        knowledge: Knowledge,
        lemma_collection: LemmaCollection,
        info_repo: InfoRepository,
        pool_size: int = 1,
    ):
        """
        Initialize the general comprehender

        :param llm_client: LLM client
        :param knowledge: Document knowledge
        :param info_repo: Information repository from preprocess
        :param pool_size: Number of processes to use for comprehension
        """
        self.llm_client = llm_client
        self.knowledge = knowledge
        self.lemma_collection = lemma_collection
        self.info_repo = info_repo

        Comprehender.pool_size = pool_size

        self.lib_comprehension = LibraryComprehension("", {})

    def comprehend(self) -> LibraryComprehension:
        """
        Comprehend the library

        :return: Library comprehension and function relevance
        """
        # comprehend the library purpose
        if self.DO_LIBRARY_PURPOSE:
            logger.info("Comprehending library purpose...")
            lib_purpose_comprehender = LibPurposeComprehender(
                self.llm_client, self.knowledge
            )
            self.lib_comprehension.purpose = lib_purpose_comprehender.comprehend()
            logger.success(
                f"Library purpose comprehended: {self.lib_comprehension.purpose}"
            )

        # comprehend the lemma summary
        if self.DO_LEMMA_USAGE:
            logger.info("Comprehending lemma summary...")
            lemma_summary_comprehender = LemmaSummaryComprehender(
                self.llm_client,
                self.knowledge,
                self.lemma_collection,
                self.info_repo,
            )
            self.lib_comprehension.functions = lemma_summary_comprehender.comprehend()
            logger.success("Lemma summary comprehended")

        return self.lib_comprehension

    def dump(self, comprehension_path: Path | None):
        """
        Dump the library comprehension and function relevance to files

        :param comprehension_path: Path to dump the library comprehension, set to None to skip
        """
        if comprehension_path is not None:
            if (
                not self.lib_comprehension.purpose
                and not self.lib_comprehension.functions
            ):
                raise ValueError("Comprehension not done yet")
            self.lib_comprehension.dump(comprehension_path)

    def dump_to_json_csv(self, comprehension_path: Path | None):
        """
        Dump the library comprehension to JSON and function relevance to CSV.
        Only for human-readable purpose, not for loading back.

        :param comprehension_path: Path to dump the library comprehension, set to None to skip
        :param relevance_path: Path to dump the function relevance, set to None to skip
        """
        if comprehension_path is not None:
            if (
                not self.lib_comprehension.purpose
                and not self.lib_comprehension.functions
            ):
                raise ValueError("Comprehension not done yet")
            self.lib_comprehension.dump_json(comprehension_path)


class LibPurposeComprehender(Comprehender):
    """
    Comprehend the purpose of the library

    IN: document knowledge
    OUT: library purpose
    """

    RETRIEVE_TEMPLATE = "introduction of the {} library"

    def __init__(self, llm_client: LLMClient, knowledge: Knowledge):
        """
        Initialize the library purpose comprehender

        :param llm_client: LLM client
        :param knowledge: Document knowledge
        """
        self.llm_client = llm_client
        self.library_name = global_vars.fvt_name
        self.knowledge = knowledge

    def comprehend(self) -> str:
        """
        Comprehend the purpose of the library

        :return: concise description of the library
        """
        # retrieve the document
        document_excerpts = self.knowledge.retrieve(
            self.RETRIEVE_TEMPLATE.format(self.library_name)
        )

        # prompt for library purpose
        prompter = LibPurposePrompter(LLMChat(self.llm_client))
        library_purpose = prompter.prompt(self.library_name, document_excerpts)

        if not library_purpose:
            raise ValueError("No response from the LLM")
        logger.debug(f"Library purpose: \n{library_purpose}")

        return library_purpose


class LemmaSummaryComprehender(Comprehender):
    """
    Comprehend the lemma functions

    IN: library purpose, lemma names, lemma signatures
    OUT: lemma summaries
    """

    def __init__(
        self,
        llm_client: LLMClient,
        knowledge: Knowledge,
        lemma_collection: LemmaCollection,
        info_repo: InfoRepository,
    ):
        """
        Initialize the lemma summary comprehender

        :param llm_client: LLM client
        :param knowledge: Document knowledge
        :param info_repo: Information repository from preprocess
        """
        self.library_name = global_vars.fvt_name
        self.llm_client = llm_client
        self.knowledge = knowledge
        self.lemma_collection = lemma_collection
        self.info_repo = info_repo

    @staticmethod
    def _get_function_signatures(
        lemma_loc: str, lemma_collection: LemmaCollection, info_repo: InfoRepository
    ) -> str:
        """
        Get the function signature by function name

        :param function_name: Function name
        :param api_collection: API functions
        :param info_repo: Information repository from preprocess
        :return: Function signature
        """

        func_info = info_repo.get_info(lemma_loc, RustFunctionInfo)
        if not isinstance(func_info, RustFunctionInfo):
            raise ValueError(f"Function info not found for {lemma_loc}")
        lemma_sig = func_info.signature

        return lemma_sig

    @with_progress_update
    def _comprehend_one_function(
        self,
        lemma_loc: str,
        progress: tqdm | None = None,
    ) -> tuple[str, str]:
        """
        Comprehend the usage of one function

        :param lemma_loc: Lemma location
        :param progress: Progress bar object
        :return: Function usage, as a tuple of (function name, function usage)
        """
        # get the function signatures and source code
        func_info = self.info_repo.get_info(lemma_loc, RustFunctionInfo)
        if not isinstance(func_info, RustFunctionInfo):
            raise ValueError(f"Function info not found for {lemma_loc}")
        lemma_sig = func_info.signature
        lemma_name = func_info.name

        # prompt for function usage
        prompter = LemmaSummaryFromSrcPrompter(LLMChat(self.llm_client))
        summary = prompter.prompt(self.library_name, lemma_name, lemma_sig)

        logger.debug(f"{lemma_name} comprehended: \n{summary}")
        return (lemma_name, summary)

    def comprehend(self) -> dict[str, str]:
        """
        Comprehend the usage of the function

        :return: Function comprehensions, as function name: function usage
        """
        # Algorithm:
        # 1. Get all lemma functions as targets
        # 2. Prompt the LLM with source code to infer the usage

        # get all function names, deduplicated
        lemma_locs = self.lemma_collection.function_locations

        # comprehend the function usage
        progress_bar = tqdm(
            total=len(lemma_locs),
            desc="Comprehending lemma summary",
            unit="lemma function",
            colour="BLUE",
            leave=False,
        )
        if self.pool_size > 1:
            with ThreadPoolExecutor(max_workers=self.pool_size) as executor:
                results = list(
                    executor.map(
                        lambda lemma_loc: self._comprehend_one_function(
                            lemma_loc, progress=progress_bar
                        ),
                        lemma_locs,
                    )
                )
        else:
            results = [
                self._comprehend_one_function(lemma_loc, progress=progress_bar)
                for lemma_loc in lemma_locs
            ]

        progress_bar.close()
        return {result[0]: result[1] for result in results}
