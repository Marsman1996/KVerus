import json
from loguru import logger

from src.prover.fvt import FVT
from src.llm.prompter import ValidatePrompter


class Validator:
    """
    Class to validate the generated formal verification target (FVT) code
    """

    VALIDATE = False

    def __init__(self):
        pass

    def validate(self, fvt, ori_code: str, gen_code: str) -> bool:
        """
        Validate the FVT code.

        :param fvt: The formal verification target (FVT) instance.
        :param ori_code: The original code before generation.
        :param gen_code: The generated code after refinement.
        :return: True if the code is valid, False otherwise.
        """
        if not self.VALIDATE:
            return True

        prompter = ValidatePrompter(fvt.llm_chat)
        json_response: list = json.loads(prompter.prompt(ori_code, gen_code))
        logger.debug(f"Validation response: {json_response}")
        is_modified = json_response["modified"]
        return not is_modified
