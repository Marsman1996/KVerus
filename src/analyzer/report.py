from pathlib import Path
from loguru import logger

from src.prover.fvt import FVT
from src.llm.prompter import ReportFailPrompter


class Reporter:
    ENABLED = False

    def __init__(self):
        pass

    def generate_failure_report(self, fvt: FVT, report_path: Path):
        """
        Generate a failure report based on the FVT, which contains the verus code, error message and knowledge.

        :param fvt: The formal verification target (FVT) instance.
        :param report_path: The output report path.
        """
        if self.ENABLED == False or fvt.refined:
            # logger.debug("FVT already refined, no failure report needed")
            return

        logger.debug("Generating failure report")
        prompter = ReportFailPrompter(fvt.llm_chat)
        generated_code = (
            fvt.last_gen_code or fvt.proof_code
        )
        report = prompter.prompt(
            fvt.MAX_REFINE_ROUNDS,
            fvt.ori_code,
            generated_code,
            fvt.last_err_msg,
            fvt.meta_knowledge or "",
        )
        report_path.write_text(report)
        logger.info(f"Generated failure report:\n{report} \nin {report_path}")
