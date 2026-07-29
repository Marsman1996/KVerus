"""
Extract information repository from the Meta, which is a dependency graph of language objects.

Design:
The idea here is to retrieve all needed information at preprocess stage, while still offering some flexibilities at generation stage.
Hence, the `info` module is designed as a directed graph which stores all used objects and their reference relationships.
These objects include functions, composite types, classes, typedefs, etc.
At preprocess stage, we create all the objects and build the graph.
Later at generation stage, we can traverse the graph to collect all the needed information.
"""

from abc import ABC
from loguru import logger
import pickle
import json
from pathlib import Path
from functools import cache, lru_cache
from random import choice
from typing import Optional, Union, List, Tuple, Dict, Any, Iterator

import src.vars as global_vars
from src.utils import filter_typename, deduplicate_list, FilePos, parse_location
from .meta import Meta


@lru_cache(maxsize=1000)
def parse_name_location(name_loc_str: str) -> Tuple[str, str]:
    """
    Parse a string in format "name (location)" into name and location.

    :param name_loc_str: String in format "name (location)"
    :return: Tuple of (name, location)
    """
    if not name_loc_str or "(" not in name_loc_str:
        return "", ""

    name, location = name_loc_str.rstrip(")").split(" (", 1)
    return name, location


def create_composite_info(composite_str: str) -> Optional["RustCompositeInfo"]:
    """
    Create a RustCompositeInfo object from a composite string.

    :param composite_str: String in format "name (location)"
    :return: RustCompositeInfo object or None if not found
    """
    if not composite_str:
        return None

    name, location = parse_name_location(composite_str)
    if not location:
        return None

    composite_dict = Info.dict_info["composite_infos"].get(location)
    if composite_dict is None:
        logger.warning(
            f"Composite {name} at location {location} is not found in the meta data."
        )
        return None

    # Import here to avoid circular imports
    return RustCompositeInfo.from_dict(composite_dict)


def create_typedef_info(typedef_str: str) -> Optional["RustTypedefInfo"]:
    """
    Create a RustTypedefInfo object from a typedef string.

    :param typedef_str: String in format "name (location)"
    :return: RustTypedefInfo object or None if not found
    """
    if not typedef_str:
        return None

    name, location = parse_name_location(typedef_str)
    if not location:
        return None

    typedef_dict = Info.dict_info["typedef_infos"].get(location)
    if typedef_dict is None:
        logger.warning(
            f"Typedef {name} at location {location} is not found in the meta data."
        )
        return None

    # Import here to avoid circular imports
    return RustTypedefInfo.from_dict(typedef_dict)


def create_trait_info(trait_str: str) -> Optional["RustTraitInfo"]:
    """
    Create a RustTraitInfo object from a trait string.

    :param trait_str: String in format "name (location)"
    :return: RustTraitInfo object or None if not found
    """
    if not trait_str:
        return None

    name, location = parse_name_location(trait_str)
    if not location:
        return None

    trait_dict = Info.dict_info["trait_infos"].get(location)
    if trait_dict is None:
        logger.warning(
            f"Trait {name} at location {location} is not found in the meta data."
        )
        return None

    # Import here to avoid circular imports
    return RustTraitInfo.from_dict(trait_dict)


def create_impl_info(impl_str: str) -> Optional["RustImplInfo"]:
    """
    Create a RustImplInfo object from an impl string.

    :param impl_str: String in format "name (location)"
    :return: RustImplInfo object or None if not found
    """
    if not impl_str:
        return None

    name, location = parse_name_location(impl_str)
    if not location:
        return None

    impl_dict = Info.dict_info["impl_infos"].get(location)
    if impl_dict is None:
        logger.warning(
            f"Impl {name} at location {location} is not found in the meta data."
        )
        return None

    # Import here to avoid circular imports
    return RustImplInfo.from_dict(impl_dict)


class Info(ABC):
    """
    Abstract class to store the information.
    """

    def __init__(self):
        self.name: str = ""
        self.location: str = ""

    meta: "Meta" = None
    repository: "InfoRepository" = None
    dict_info: dict = None
    """ Currently only for Rust objects """

    @classmethod
    def from_name_and_location_as_empty(cls, name: str, location: str):
        """
        Create an empty information object with name and location.

        :param name: The name string.
        :param location: The location string.
        :return: The information object.
        """
        info = cls()
        info.name = name
        info.location = location
        # To avoid infinite recursion, we need to create an empty object and add it to the repository first
        # Afterwards we'll modify the object
        cls.repository.add_info(info)
        return info

    @property
    def ref_info_iter(self):
        """
        Iterate the referred information objects in this information object.
        """
        for prop in self.__dict__.values():
            if isinstance(prop, Info):
                yield prop
            elif isinstance(prop, list):
                for item in prop:
                    if isinstance(item, Info):
                        yield item

    @property
    def ref_info_iter_name_unique(self):
        """
        Iterate the referred information objects in this information object.
        Objects with the same name will be randomly selected once.
        """
        for prop in self.__dict__.values():
            if isinstance(prop, Info):
                yield prop
            elif isinstance(prop, list):
                # organize the items by name
                items_by_name = {}
                for item in prop:
                    if isinstance(item, Info):
                        items_by_name.setdefault(item.name, []).append(item)
                # randomly select one item for each name
                for items in items_by_name.values():
                    yield choice(items)

    def __eq__(self, value) -> bool:
        return type(self) == type(value) and self.location == value.location

    def __hash__(self):
        return hash(type(self)) + hash(self.location)


class FunctionInfo(Info):
    def __init__(self):
        super().__init__()
        self.signature: str = ""
        self.used_composites: List["CompositeInfo"] = []
        self.used_typedefs: List["TypedefInfo"] = []
        self.used_functions: List["FunctionInfo"] = []
        self.impl_range: Tuple[Optional[FilePos], Optional[FilePos]] = (None, None)


class RustFunctionInfo(FunctionInfo):
    """
    Class to store the information of a Rust function.
    """

    # A Rust function may need below information:
    # 1. Name of the function
    # 2. Location of the function, as a identifier
    # 3. Function signature
    # 4. Used composite (struct/enum) info
    # 5. Used typedef info
    # 6. Held-by struct
    # 7. Related struct info
    # 8. Position range of the implementation

    def __init__(self):
        super().__init__()
        self.short_name = ""
        self.signature: str = ""
        self.used_composites: List["RustCompositeInfo"] = []
        self.used_typedefs: List["RustTypedefInfo"] = []
        self.used_functions: List["RustFunctionInfo"] = []
        # self.heldby_namespace: str = ""
        self.heldby_impl: Union[str, "RustImplInfo"] = ""
        self.heldby_trait: Optional["RustTraitInfo"] = None
        self.trait_bounds: List["RustTraitInfo"] = []
        self.impl_range: Tuple[Optional[FilePos], Optional[FilePos]] = (None, None)
        self.attributes: List[str] = []
        self.isPub: bool = False
        self.is_empty: bool = False

    @classmethod
    def from_dict(cls, dict_func_info: Dict[str, Any]) -> "RustFunctionInfo":
        """
        Create a RustFunctionInfo object from a function dict.

        :param dict_func_info: The function dict.
        :return: A RustFunctionInfo object.
        """
        info = cls()
        info.name = dict_func_info["name"]
        info.short_name = dict_func_info["short_name"]
        info.location = dict_func_info["location"]
        info.signature = dict_func_info["signature"]

        # Create composite and typedef objects using utility functions
        info.used_composites = [
            composite_info
            for composite_str in dict_func_info["used_composites"]
            if (composite_info := create_composite_info(composite_str)) is not None
        ]

        info.used_typedefs = [
            typedef_info
            for typedef_str in dict_func_info["used_typedefs"]
            if (typedef_info := create_typedef_info(typedef_str)) is not None
        ]

        # impl range
        range_start = dict_func_info["impl_range"][0]
        range_end = dict_func_info["impl_range"][1]
        info.impl_range = (
            FilePos.from_location_line(range_start),
            FilePos.from_location_line(range_end),
        )

        # heldby impl
        heldby_impl_str = dict_func_info["heldby_impl"]
        info.heldby_impl = create_impl_info(heldby_impl_str) if heldby_impl_str else ""

        # Add trait related info
        heldby_trait_str = dict_func_info["heldby_trait"]
        info.heldby_trait = (
            create_trait_info(heldby_trait_str) if heldby_trait_str else None
        )

        info.trait_bounds = [
            trait_bound_info
            for trait_bound_str in dict_func_info["trait_bounds"]
            if (trait_bound_info := create_trait_info(trait_bound_str)) is not None
        ]

        # Add attributes
        info.attributes = dict_func_info.get("attributes", [])

        info.isPub = dict_func_info["isPub"]
        info.is_empty = dict_func_info["is_empty"]

        return info

    def add_used_functions(self, dict_used: List[str]) -> None:
        """
        Add used functions to the RustFunctionInfo object.
        We use a separate function to add used functions
        to prevent circular dependency

        :param dict_used: The used functions list.
        """
        for func_str in dict_used:
            if " (" in func_str:
                # find func info by location
                func_name, func_loc = parse_name_location(func_str)
                func_info = self.repository.get_info(func_loc, RustFunctionInfo)

                if func_info is None:
                    logger.warning(
                        f"Cannot find function {func_name} in location {func_loc}"
                    )
                    # Create an empty function info as fallback
                    func_info = RustFunctionInfo.from_name_and_location_as_empty(
                        func_name, func_loc
                    )
                    pos_start = FilePos.from_location_line(func_loc)
                    # FIXME: Could it exceed the file end?
                    func_loc_end = (
                        f"{pos_start.file}:{pos_start.line + 20}:{pos_start.col}"
                    )
                    pos_end = FilePos.from_location_line(func_loc_end)
                    func_info.impl_range = (pos_start, pos_end)

                if func_info not in self.used_functions:
                    self.used_functions.append(func_info)
            else:
                # For functions that cannot be navigated, find them by name
                func_name = func_str
                func_infos = self.repository.get_info_by_name(
                    func_name, RustFunctionInfo
                )

                if not func_infos:
                    logger.warning(
                        f"Cannot find callee function {func_name} in caller {self.location}"
                    )
                    continue

                if len(func_infos) > 1:
                    logger.warning(
                        f"Function {func_name} has multiple definitions found."
                    )

                # Prefer functions in the same file
                self_file, _, _ = parse_location(self.location)
                for func_info in func_infos:
                    func_file, _, _ = parse_location(func_info.location)
                    if self_file == func_file:
                        if func_info not in self.used_functions:
                            self.used_functions.append(func_info)
                        break
                else:
                    # If no function in same file, use the first one
                    if func_infos[0] not in self.used_functions:
                        self.used_functions.append(func_infos[0])

    def get_impl_code(self) -> str:
        """
        Get the implementation code of the function.

        :return: The implementation code string.
        """
        if self.impl_range[0] is None or self.impl_range[1] is None:
            logger.error(
                f"Cannot find implementation range for function {self.name}, {self.location}"
            )
            return ""
        pos_start = self.impl_range[0]
        pos_end = self.impl_range[1]
        impl_code = pos_start.get_content_till_pos(pos_end)
        return impl_code


class CompositeInfo(Info): ...


class RustCompositeInfo(CompositeInfo):
    """
    Class to store the information of a Rust composite type.
    """

    # A Rust composite type may need below information:
    # 1. Name of the composite type
    # 2. Location of the composite type, as a identifier
    # 3. Composite definition
    # 4. Used composite info
    # 5. Used typedef info
    # 6. Held-by struct
    # 7. Related struct info
    # 8. Composite kind (struct, union, enum, unknown)

    def __init__(self):
        super().__init__()
        self.definition: str = ""
        self.used_composites: List["RustCompositeInfo"] = []
        self.used_typedefs: List["RustTypedefInfo"] = []
        self.heldby_namespace: str = ""
        self.heldby_class: str = ""
        self.related_class: List["RustCompositeInfo"] = []
        self.kind: str = ""
        self.trait_bounds: List["RustTraitInfo"] = []
        self.impl_range: Tuple[Optional[FilePos], Optional[FilePos]] = (None, None)

    @classmethod
    def from_dict(cls, dict_comp: Dict[str, Any]) -> "RustCompositeInfo":
        """
        Create a RustCompositeInfo object from a composite dict.

        :param dict_comp: The composite dict.
        :return: A RustCompositeInfo object.
        """
        name = dict_comp["name"]
        location = dict_comp["location"]

        # Return existing info if already created
        if (info := cls.repository.get_info(location, cls)) is not None:
            return info

        info = cls.from_name_and_location_as_empty(name, location)
        info.definition = dict_comp["definition"]
        info.kind = dict_comp["kind"]

        # Create composite and typedef objects using utility functions
        info.used_composites = [
            composite_info
            for composite_str in dict_comp["used_composites"]
            if (composite_info := create_composite_info(composite_str)) is not None
        ]

        info.used_typedefs = [
            typedef_info
            for typedef_str in dict_comp["used_typedefs"]
            if (typedef_info := create_typedef_info(typedef_str)) is not None
        ]

        info.trait_bounds = [
            trait_bound_info
            for trait_bound_str in dict_comp["trait_bounds"]
            if (trait_bound_info := create_trait_info(trait_bound_str)) is not None
        ]

        info.impl_range = (
            FilePos.from_location_line(dict_comp["impl_range"][0]),
            FilePos.from_location_line(dict_comp["impl_range"][1]),
        )

        return info


class RustImplInfo(Info):
    """
    Class to store the information of a Rust impl code block
    """

    def __init__(self):
        super().__init__()
        self.signature: str = ""
        self.impl_range: Tuple[Optional[FilePos], Optional[FilePos]] = (None, None)
        self.trait_info: Optional["RustTraitInfo"] = None
        self.composite_info: Optional["RustCompositeInfo"] = None
        self.trait_bounds: List["RustTraitInfo"] = []

    @classmethod
    def from_dict(cls, dict_impl: Dict[str, Any]) -> "RustImplInfo":
        name = dict_impl["name"]
        location = dict_impl["location"]

        # Return existing info if already created
        if (info := cls.repository.get_info(location, cls)) is not None:
            return info

        info = cls.from_name_and_location_as_empty(name, location)
        info.signature = dict_impl["signature"]

        # impl range
        info.impl_range = (
            FilePos.from_location_line(dict_impl["impl_range"][0]),
            FilePos.from_location_line(dict_impl["impl_range"][1]),
        )

        # Use utility functions for creating related objects
        info.trait_info = create_trait_info(dict_impl.get("trait_info", ""))
        info.composite_info = create_composite_info(dict_impl.get("composite_info", ""))

        info.trait_bounds = [
            trait_bound_info
            for trait_bound_str in dict_impl["trait_bounds"]
            if (trait_bound_info := create_trait_info(trait_bound_str)) is not None
        ]

        return info


class RustTraitInfo(Info):
    """
    Class to store the information of a Rust trait.
    """

    def __init__(self):
        super().__init__()
        self.signature: str = ""
        self.used_composites: List["RustCompositeInfo"] = []
        self.used_typedefs: List["RustTypedefInfo"] = []
        self.trait_bounds: List["RustTraitInfo"] = []
        self.impl_range: Tuple[FilePos, FilePos] = (None, None)

    @classmethod
    def from_dict(cls, dict_trait: Dict[str, Any]) -> "RustTraitInfo":
        """
        Create a RustTraitInfo object from a trait dict.

        :param dict_trait: The trait dict.
        :return: A RustTraitInfo object.
        """
        name = dict_trait["name"]
        location = dict_trait["location"]

        # Return existing info if already created
        if (info := cls.repository.get_info(location, cls)) is not None:
            return info

        info = cls.from_name_and_location_as_empty(name, location)
        info.signature = dict_trait["signature"]

        # impl range
        info.impl_range = (
            FilePos.from_location_line(dict_trait["impl_range"][0]),
            FilePos.from_location_line(dict_trait["impl_range"][1]),
        )

        # Create objects using utility functions for better performance
        info.used_composites = [
            composite_info
            for composite_str in dict_trait["used_composites"]
            if (composite_info := create_composite_info(composite_str)) is not None
        ]

        info.used_typedefs = [
            typedef_info
            for typedef_str in dict_trait["used_typedefs"]
            if (typedef_info := create_typedef_info(typedef_str)) is not None
        ]

        info.trait_bounds = [
            trait_bound_info
            for trait_bound_str in dict_trait["trait_bounds"]
            if (trait_bound_info := create_trait_info(trait_bound_str)) is not None
        ]

        return info


class TypedefInfo(Info): ...


class RustTypedefInfo(TypedefInfo):
    """
    Class to store the information of a Rust typedef.
    """

    # A Rust typedef may need below information:
    # 1. Name of the typedef
    # 2. Location of the typedef, as a identifier
    # 3. Typedef definition
    # 4. Used composite info
    # 5. Used typedef info
    # 6. Held-by struct
    # 7. Related struct info

    def __init__(self):
        super().__init__()
        self.definition: str = ""
        self.used_composites: List["RustCompositeInfo"] = []
        self.used_typedefs: List["RustTypedefInfo"] = []
        self.heldby_namespace: str = ""
        self.heldby_class: str = ""
        self.related_class: List["RustCompositeInfo"] = []
        self.impl_range: Tuple[FilePos, FilePos] = (None, None)

    @classmethod
    def from_dict(cls, typedef_obj: Dict[str, Any]) -> "RustTypedefInfo":
        """
        Create a RustTypedefInfo object from a typedef dict.

        :param typedef_obj: The typedef dict.
        :return: A RustTypedefInfo object.
        """
        name = typedef_obj["name"]
        location = typedef_obj["location"]

        # Return existing info if already created
        if (info := cls.repository.get_info(location, cls)) is not None:
            return info

        info = cls.from_name_and_location_as_empty(name, location)
        info.definition = typedef_obj["definition"]

        # Create objects using utility functions for better performance
        info.used_composites = [
            composite_info
            for composite_str in typedef_obj["used_composites"]
            if (composite_info := create_composite_info(composite_str)) is not None
        ]

        info.used_typedefs = [
            typedef_info
            for typedef_str in typedef_obj["used_typedefs"]
            if (typedef_info := create_typedef_info(typedef_str)) is not None
        ]

        info.impl_range = (
            FilePos.from_location_line(typedef_obj["impl_range"][0]),
            FilePos.from_location_line(typedef_obj["impl_range"][1]),
        )

        return info


class InfoRepository:
    """
    Repository to store all the information.
    """

    def __init__(self, meta: Meta):
        """
        Initialize the repository.

        :param meta: The meta data.
        """
        self.meta = meta
        Info.meta = meta
        Info.repository = self

        # reorganize the base to derived classes, in order to parse ABC constructor
        if global_vars.fvt_language == global_vars.SupportedLanguages.CPP:
            self.meta.reorganize_base_to_derived()

        # all the information objects are stored as location:object
        self.function_infos: Dict[str, FunctionInfo] = {}
        self.composite_infos: Dict[str, CompositeInfo] = {}
        self.typedef_infos: Dict[str, TypedefInfo] = {}
        self.trait_infos: Dict[str, RustTraitInfo] = {}
        self.impl_infos: Dict[str, RustImplInfo] = {}

    def iter(
        self, start: List[Info], name_unique: bool = False, traverse_depth: int = -1
    ) -> Iterator[Tuple[Info, List[Info]]]:
        """
        Iterate all the information objects from the start info objects.

        :param start: The start info objects.
        :param name_unique: Whether to use name-unique iterator,
                            which will randomly choose one unique info object from all the same name info objects.
        :param traverse_depth: The depth to traverse. -1 means infinite.
        :return: The generator of a tuple of (info, visited path).
        """
        # traverse the info objects
        # the info objects that have been visited
        visited_infos = set()
        # the traversing stack, each element is a tuple of (info, visited path)
        traversing_stack = [(info, []) for info in start]

        # do BFS traversal
        while traversing_stack:
            # pop the top info object in the stack
            cur_info, cur_visited_path = traversing_stack.pop()
            # check if it has been visited
            if cur_info in visited_infos:
                continue
            # check if the traverse depth is reached
            if len(cur_visited_path) > traverse_depth and traverse_depth != -1:
                continue
            # mark the info object as visited
            visited_infos.add(cur_info)

            # yield the info object
            yield cur_info, cur_visited_path

            # get the reference info objects
            ref_infos = (
                cur_info.ref_info_iter_name_unique
                if name_unique
                else cur_info.ref_info_iter
            )
            # push the reference info objects into the stack
            for ref_info in ref_infos:
                traversing_stack.append((ref_info, cur_visited_path + [cur_info]))

    def dump(self, path: Path):
        """
        Dump the repository to a file using pickle.

        :param path: The save path.
        """
        with open(path, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, path: Path) -> "InfoRepository":
        """
        Load the repository from a file using pickle.

        :param path: The load path.
        :return: The repository object.
        """
        if not path.is_file():
            raise ValueError(f"The repository file is not found at {path}.")
        with open(path, "rb") as f:
            return pickle.load(f)

    @classmethod
    def load_from_dict(cls, dict_info: dict) -> "InfoRepository":
        """
        Load the repository from a json file.

        :param json_path: The json load path.
        :return: The repository object.
        """
        repo = cls(Meta({}))
        Info.dict_info = dict_info
        for func_loc, func_info in dict_info["function_infos"].items():
            repo.function_infos[func_loc] = RustFunctionInfo.from_dict(func_info)
        # after all functions are initialized, we load used functions
        func_infos = list(repo.function_infos.values())
        for func_info in func_infos:
            func_info.add_used_functions(
                dict_info["function_infos"][func_info.location]["used_functions"]
            )
        return repo

    def dump_json(self, json_path: Path):
        """
        Dump the repository to a json file.
        This is just for human readable, not for loading back.

        :param json_path: The json save path.
        """

        class InfoEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, Info):
                    json_obj = {}
                    for p_name, p_value in obj.__dict__.items():
                        if isinstance(p_value, list):
                            if p_value:
                                for item in p_value:
                                    if isinstance(item, Info):
                                        # for Info list
                                        json_obj.setdefault(p_name, []).append(
                                            f"{item.name} ({item.location})"
                                        )
                                    else:
                                        json_obj.setdefault(p_name, []).append(item)
                            else:
                                json_obj[p_name] = p_value
                        elif isinstance(p_value, tuple) and all(
                            isinstance(item, FilePos) for item in p_value
                        ):
                            # for FilePos tuple
                            json_obj[p_name] = [str(pos) for pos in p_value]
                        elif p_name in [
                            "heldby_trait",
                            "heldby_impl",
                            "composite_info",
                            "trait_info",
                        ]:
                            json_obj[p_name] = (
                                f"{p_value.name} ({p_value.location})"
                                if p_value
                                else None
                            )
                        else:
                            json_obj[p_name] = p_value
                    return json_obj
                else:
                    return super().default(obj)

        with open(json_path, "w") as f:
            json.dump(
                {
                    "function_infos": self.function_infos,
                    "composite_infos": self.composite_infos,
                    "typedef_infos": self.typedef_infos,
                    "trait_infos": self.trait_infos,
                    "impl_infos": self.impl_infos,
                },
                f,
                indent=4,
                cls=InfoEncoder,
            )

    def get_info(self, loc: str, cls) -> Optional[Info]:
        """
        Get the information object by location and class.

        :param loc: The location.
        :param cls: The class which the information object belongs to.
        :return: The information object, None if not found.
        """
        if issubclass(cls, FunctionInfo):
            return self.function_infos.get(loc)
        elif issubclass(cls, CompositeInfo):
            return self.composite_infos.get(loc)
        elif issubclass(cls, RustTraitInfo):
            return self.trait_infos.get(loc)
        elif issubclass(cls, RustImplInfo):
            return self.impl_infos.get(loc)
        elif issubclass(cls, TypedefInfo):
            return self.typedef_infos.get(loc)
        else:
            logger.error(f"Invalid class: {cls}")
            return None

    def get_info_by_name(self, name: str, cls) -> List[Info]:
        """
        Get the information object by name and class.

        :param name: The name.
        :param cls: The class which the information object belongs to.
        :return: The information objects list.
        """
        if issubclass(cls, FunctionInfo):
            infos_dict = self.function_infos
        elif issubclass(cls, CompositeInfo):
            infos_dict = self.composite_infos
        elif issubclass(cls, TypedefInfo):
            infos_dict = self.typedef_infos
        else:
            logger.error(f"Invalid class: {cls}")
            return []

        return [
            info
            for info in infos_dict.values()
            if info.name == name and isinstance(info, cls)
        ]

    def add_info(self, info):
        """
        Add information object to the repository.

        :param info: The information object.
        """
        if isinstance(info, FunctionInfo):
            self.function_infos[info.location] = info
        elif isinstance(info, CompositeInfo):
            self.composite_infos[info.location] = info
        elif isinstance(info, RustTraitInfo):
            self.trait_infos[info.location] = info
        elif isinstance(info, RustImplInfo):
            self.impl_infos[info.location] = info
        elif isinstance(info, TypedefInfo):
            self.typedef_infos[info.location] = info
        else:
            logger.error(f"Invalid info object: {info}")
