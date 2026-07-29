"""
Collect the required information for formal verification target generation
"""

import json
from pathlib import Path
from loguru import logger
from abc import ABC, abstractmethod

from src import vars as global_vars
from src.preprocessor.information import InfoRepository, RustFunctionInfo, RustTraitInfo
from src.llm.prompter import VerusAnalyzeAdmitPrompter, VerusAnalyzeProvePrompter
from src.utils import parse_location
from .fvt import FVT


class GenRequirements(ABC):
    """
    Class to store the required information for FVT generation
    """

    ...


class VerusGenRequirements(GenRequirements):
    """
    Class to store the required information for Verus FVT generation
    """

    def __init__(self, api_info: str):
        self.api_info = api_info


class VerusInfoCollector:
    """
    To assist in collecting extra knowledge for Verus FVT generation
    We need to use the same LLM as verification here
    This is to ensure the knowledge is consistent with the verification process
    """

    def __init__(self):
        pass

    def collect_admit_knowledge(self, fvt: FVT, verus_code: str) -> str:
        """
        Collect extra knowledge for prove admit()
        TODO: Currently focus on lemma related
        """
        prompter = VerusAnalyzeAdmitPrompter(fvt.llm_chat)
        requires = prompter.prompt(verus_code)
        fvt.llm_chat.remove_last_query()
        return self._collect_knowledge(fvt, requires)

    def collect_prove_knowledge(self, fvt: FVT, verus_code: str, err_msg: str) -> str:
        """
        Collect extra knowledge to finish the proof
        TODO: Currently focus on lemma related
        """
        prompter = VerusAnalyzeProvePrompter(fvt.llm_chat)
        requires = prompter.prompt(verus_code, err_msg)
        fvt.llm_chat.remove_last_query()
        return self._collect_knowledge(fvt, requires)

    def _collect_knowledge(self, fvt: FVT, requires: str) -> str:
        try:
            requires: list[dict[str, str]] = json.loads(requires)
        except json.JSONDecodeError:
            logger.error("Expected JSON format, but got: \n" + requires)
            return ""
        extra_knowledge = ""
        for require in requires:
            if "lemma" in require:
                extra_knowledge += self._select_lemma(fvt, require["lemma"])
        return extra_knowledge

    def _select_lemma(self, fvt: FVT, desc: str):
        """
        Select lemma for Verus FVT generation
        """
        lemma_excerpts = fvt.query_knowledge(desc)
        if lemma_excerpts is None:
            return ""
        logger.info(f"For query {desc}\nRetrieved {len(lemma_excerpts)} excerpts.")
        lemma_content = ""
        for lemma in lemma_excerpts:
            lemma_content += f"{lemma.content}\n"
        return lemma_content
        # # load lemma tree
        # tree_path = (
        #     Path(global_vars.fvt_config["output_path"])
        #     / "preprocessor"
        #     / "model.tree.json"
        # )
        # if not tree_path.exists():
        #     logger.warning(f"{tree_path} not exist, run preprocess first!")
        #     return
        # dict_tree: dict = json.loads(tree_path.read_text())
        # list_tree = []
        # for root, lines in dict_tree.items():
        #     # FIXME: current we only select lemma from vstd
        #     if root.find("vstd") < 0:
        #         continue
        #     list_tree.append(f"{root}\n{'\n'.join(lines)}")
        # if len(list_tree) == 0:
        #     logger.warning("No lemma tree found")
        #     return

        # prompter = VerusSelectLemmaAdmit(fvt.llm_chat)
        # verus_code = ""

    def collect_meta_knowledge(self, info: InfoRepository, func_loc: str) -> str:
        """
        Collect meta information for Verus FVT generation
        """
        if info is None:
            logger.error(
                "Info repository is not initialized, cannot collect meta knowledge."
            )
            return ""
        code_knowledge = f"#### Related Code Knowledge\n"
        func_info = info.get_info(func_loc, RustFunctionInfo)
        # get all related function infos
        set_func_info: set[RustFunctionInfo] = set()

        def get_used_func_info(func_info, depth=0):
            if depth > 5:
                return
            for used_func_info in func_info.used_functions:
                if used_func_info not in set_func_info:
                    set_func_info.add(used_func_info)
                    get_used_func_info(used_func_info, depth + 1)

        get_used_func_info(func_info)
        set_composite_info = set()
        set_typedef_info = set()

        for used_func_info in set_func_info:
            code_knowledge += f"\n```rust\n{used_func_info.get_impl_code()}\n```\n"
            # Add composite types
            for composite_info in used_func_info.used_composites:
                set_composite_info.add(composite_info)
            # Add typedefs
            for typedef_info in used_func_info.used_typedefs:
                set_typedef_info.add(typedef_info)
        for composite_info in set_composite_info:
            code_knowledge += f"\n```rust\n{composite_info.definition}\n```\n"
        for typedef_info in set_typedef_info:
            code_knowledge += f"\n```rust\n{typedef_info.definition}\n```\n"

        lemma_knowledge = f"#### Related Lemma Knowledge\n"
        set_lemma = set()

        # Collect all related traits
        def get_traits(trait_obj: RustTraitInfo, depth=0):
            if depth > 5:
                return
            for trait in trait_obj.trait_bounds:
                if trait not in set_traits:
                    set_traits.add(trait)
                    get_traits(trait, depth + 1)

        set_traits = set()
        heldby_trait = func_info.heldby_trait
        if heldby_trait:
            set_traits.add(heldby_trait)
            get_traits(heldby_trait)

        file, _, _ = parse_location(func_info.location)
        for info_iter in info.function_infos.values():
            if info_iter.name.find("lemma_") < 0:
                continue
            # Collect all lemmas from the same file
            iter_file, _, _ = parse_location(info_iter.location)
            if iter_file == file:
                set_lemma.add(info_iter.signature)
                # set_lemma.add(info_iter.get_impl_code())
            # Collect all lemmas from the used trait
            if info_iter.heldby_trait and info_iter.heldby_trait in set_traits:
                set_lemma.add(info_iter.signature)
                # set_lemma.add(info_iter.get_impl_code())

        lemma_knowledge += "\n\n".join(f"```rust\n{lemma}\n```" for lemma in set_lemma)
        meta_knowledge = f"{code_knowledge}\n\n{lemma_knowledge}"
        logger.trace(
            f"Collected meta knowledge for {func_info.name} ({func_loc}):\n{meta_knowledge}"
        )
        return meta_knowledge

    def collect(self, model_info_path: Path):
        dict_func_info = json.loads(model_info_path.read_text())["function_infos"]
        api_info = dict()
        for func_loc in dict_func_info:
            api_info[func_loc[func_loc]] = {
                "name": dict_func_info[func_loc]["name"],
                "signature": dict_func_info[func_loc]["signature"],
            }

        gen_requirements = VerusGenRequirements(json.dumps(api_info))

        return gen_requirements
