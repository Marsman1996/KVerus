"""
Extract lemma functions from the library.
"""

from pathlib import Path
from loguru import logger
from multiprocessing import cpu_count
from dataclasses import dataclass
import json
import pickle

from .information import InfoRepository, RustFunctionInfo


@dataclass
class LemmaFunction:
    """
    Class to represent a lemma function.
    """

    name: str
    """
    The name of the API function.
    """

    loc: str
    """
    The location of the API function, as an identifier.
    """

    def __eq__(self, other):
        if not isinstance(other, LemmaFunction):
            return False
        return self.loc == other.loc

    def __hash__(self):
        return hash(self.loc)

    def __str__(self):
        return f"{self.name} at {self.loc}"

    def __repr__(self):
        return self.__str__()


class LemmaCollection:
    """
    Class to store the lemma functions.
    """

    def __init__(self, lemma_functions: list[LemmaFunction]):
        """
        Initialize the lemma functions.

        :param lemma_functions: The lemma functions list
        """
        self.funcs = lemma_functions

    @property
    def count(self):
        """
        Get the count of the lemma functions.
        """
        return len(self.funcs)

    @property
    def function_names(self):
        """
        Get all function names in the lemma functions

        :return: A list of function names
        """
        return list(set(func.name for func in self.funcs))

    @property
    def function_locations(self):
        """
        Get all function locations in the lemma functions

        :return: A list of function locations
        """
        return list(func.loc for func in self.funcs)

    def dump(self, path: Path):
        """
        Dump the lemma functions to a file.

        :param path: The save path
        """
        with open(path, "wb") as f:
            pickle.dump(self.funcs, f)

    def dump_to_json(self, path: Path):
        """
        Dump the lemma functions to a JSON file. Only for readability, not for loading back.

        :param path: The save path
        """
        lemma_functions = dict()
        for lemma_func in self.funcs:
            lemma_functions.setdefault(lemma_func.name, []).append(
                {
                    "loc": lemma_func.loc,
                }
            )
        with open(path, "w") as f:
            json.dump(lemma_functions, f, indent=4)

    @classmethod
    def load(cls, path: Path):
        """
        Load the lemma functions from a file.

        :param path: The load path
        :return: The lemma functions
        """
        if not path.is_file():
            raise ValueError(f"The lemma functions file is not found at {path}.")
        with open(path, "rb") as f:
            lemma_functions = pickle.load(f)
        return cls(lemma_functions)

    @classmethod
    def load_from_json(cls, path: Path):
        """
        Load the lemma functions from a JSON file.

        :param path: The load path
        :return: The lemma functions
        """
        if not path.is_file():
            raise ValueError(f"The lemma functions file is not found at {path}.")
        with open(path, "r") as f:
            lemma_functions = json.load(f)
        lemma_funcs = []
        for func_name, func_loc_list in lemma_functions.items():
            for func_loc in func_loc_list:
                lemma_funcs.append(
                    LemmaFunction(
                        name=func_name,
                        loc=func_loc["loc"],
                    )
                )
        return cls(lemma_funcs)

    @property
    def safe_iter(self):
        """
        Iterate the lemma functions. During the iteration, the lemma functions can be safely modified.

        :return: The lemma function generator
        """
        snapshot = self.funcs.copy()
        for lemma_func in snapshot:
            yield lemma_func

    def get_by_location(self, loc: str) -> LemmaFunction | None:
        """
        Get the lemma function by location.

        :param loc: The location
        :return: The lemma function, or None if not found
        """
        # cache lookup table
        if not hasattr(self, "loc_lookup_dict"):
            self.loc_lookup_dict = dict()
            for func in self.funcs:
                self.loc_lookup_dict[func.loc] = func
        return self.loc_lookup_dict.get(loc, None)

    def get_by_name(self, func_name: str) -> list[LemmaFunction]:
        """
        Get the lemma functions by name.

        :param func_name: The function name
        :return: The list of lemma functions
        """
        # cache lookup table
        if not hasattr(self, "name_lookup_dict"):
            self.name_lookup_dict = dict()
            for func in self.funcs:
                self.name_lookup_dict.setdefault(func.name, []).append(func)
        return self.name_lookup_dict.get(func_name, [])

    def get_locations_by_name(self, func_name: str):
        """
        Get the locations of the lemma functions with the same name.

        :param func_name: The function name
        :return: The list of locations
        """
        return [func.loc for func in self.get_by_name(func_name)]

    def remove(self, lemma_function: LemmaFunction):
        """
        Remove a lemma function.

        :param lemma_function: The lemma function to remove
        """
        self.funcs.remove(lemma_function)
        if hasattr(self, "loc_lookup_dict"):
            self.loc_lookup_dict.pop(lemma_function.loc, None)
        if hasattr(self, "name_lookup_dict"):
            self.name_lookup_dict.pop(lemma_function.name, None)

    def append(self, lemma_function: LemmaFunction):
        """
        Append a lemma function.

        :param lemma_function: The lemma function to append
        """
        self.funcs.append(lemma_function)
        if hasattr(self, "loc_lookup_dict"):
            self.loc_lookup_dict[lemma_function.loc] = lemma_function
        if hasattr(self, "name_lookup_dict"):
            self.name_lookup_dict.setdefault(lemma_function.name, []).append(
                lemma_function
            )

    def has(self, lemma_function: LemmaFunction):
        """
        Check if the lemma function exists.

        :param lemma_function: The lemma function to check
        :return: True if exists, False otherwise
        """
        return lemma_function in self.funcs

    def __len__(self):
        return len(self.funcs)

    def __str__(self):
        return "\n".join(
            f"{func.name} at {func.loc.split("/")[-1]}" for func in self.funcs
        )


class LemmaExtractor:
    """
    Lemma extractor class
    """

    def __init__(self, info: InfoRepository):
        self.info = info

    def extract(self, pool_size: int = cpu_count()) -> LemmaCollection:
        """
        Extract the lemma functions from the library.

        :param pool_size: The parallel pool size for extraction.
        :return: The lemma functions collection.
        """
        lemma_funcs = []
        for func in self.info.function_infos.values():
            if not isinstance(func, RustFunctionInfo):
                continue
            if func.short_name.startswith("lemma_"):
                lemma_funcs.append(
                    LemmaFunction(
                        name=func.name,
                        loc=func.location,
                    )
                )
        logger.info(f"Extracted {len(lemma_funcs)} lemma functions.")
        return LemmaCollection(lemma_funcs)
