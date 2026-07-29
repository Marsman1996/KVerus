"""
Formal Verification Target
"""

from pathlib import Path
from loguru import logger
import subprocess
import json
import shutil
from enum import StrEnum
from typing import ClassVar, Optional

from src import vars as global_vars
from src.llm.llm import LLMChat
from src.preprocessor.ast import RustASTPreprocessor
from src.preprocessor.information import InfoRepository
from src.comprehender.knowledge import ModelKnowledge
from src.utils import FilePos, expand_config_path
from .utils import VerifyStatus, is_verify_error


class FVTStage(StrEnum):
    PREPROCESS = "preprocess"
    PROVE = "prove"
    FIX = "fix"


class FVT:
    """
    Formal Verification Target
    """

    # config constants
    MAX_REFINE_ROUNDS: ClassVar[int] = 10
    PROCESSOR_BIN: ClassVar[Optional[Path]] = None
    VERUS_BIN: ClassVar[Optional[Path]] = None
    USE_POSTPROCESSOR: ClassVar[bool] = True
    CLEANUP_POST: ClassVar[bool] = False
    ## For ablation study
    DISABLE_CODE: ClassVar[bool] = False
    DISABLE_LEMMA: ClassVar[bool] = False
    DISABLE_VERUS: ClassVar[bool] = False

    def __init__(
        self,
        crate_path: Path,
        out_path: Path,
        verify_base_path: Path,
        llm_chat: Optional[LLMChat],
    ):
        self.crate_path = crate_path
        self.verify_base_path = verify_base_path
        self.llm_chat = llm_chat
        self.verify_cmd = None
        self.knowledge: Optional[ModelKnowledge] = None
        self.current_stage = FVTStage.PROVE
        self.SINGLE_FILE_PROVE: bool = False

        self.out_path = out_path
        if not self.out_path.exists():
            self.out_path.mkdir(parents=True, exist_ok=True)
        self.remain_refine_rounds = self.MAX_REFINE_ROUNDS
        """remaining refinement rounds"""
        self.refined = False
        """whether the fvt has been refined"""
        self.query_count = 0
        """the number of queries sent to generate and the fvt"""
        self.id = 0
        self.info: Optional[InfoRepository] = None
        self.cg_infos: dict[str, dict] = dict()
        """self.cg_infos[loc] = {calleeDeclLoc, calleeName, callerDeclLoc, callerName}"""
        self.has_rag_lemma = False
        self.stage_artifacts: dict[str, str] = {}
        self.proof_code: Optional[str] = None
        self.meta_knowledge: Optional[str] = None
        self.ori_code: Optional[str] = None
        self.last_gen_code: Optional[str] = None
        self.last_err_msg: Optional[str] = None
        self.verification_status: Optional[VerifyStatus] = None
        self.verification_error: Optional[str] = None
        self.tokens: tuple[int, int] = (0, 0)

    @staticmethod
    def _normalize_stage(stage: "FVTStage | str") -> FVTStage:
        if isinstance(stage, FVTStage):
            return stage
        return FVTStage(stage)

    def set_stage(self, stage: "FVTStage | str"):
        self.current_stage = self._normalize_stage(stage)

    def record_stage_artifact(
        self, content: str, stage: "FVTStage | str | None" = None
    ):
        normalized_stage = (
            self.current_stage if stage is None else self._normalize_stage(stage)
        )
        self.stage_artifacts[normalized_stage.value] = content
        if normalized_stage in (FVTStage.PROVE, FVTStage.FIX):
            self.proof_code = content
        self.last_gen_code = content

    def get_stage_artifact(self, stage: "FVTStage | str") -> Optional[str]:
        normalized_stage = self._normalize_stage(stage)
        return self.stage_artifacts.get(normalized_stage.value)

    def record_verification_result(self, status: VerifyStatus, err_msg: str):
        self.verification_status = status
        self.verification_error = err_msg or None
        return status, err_msg

    def set_verify_cmd(self, build_cmd: str):
        # If an instance-specific VERUS_BIN is set, prefer it
        if build_cmd.find("{VERUS_BIN}") >= 0 and self.VERUS_BIN:
            build_cmd = build_cmd.replace("{VERUS_BIN}", str(self.VERUS_BIN))
        build_cmd = expand_config_path(build_cmd)
        self.verify_cmd = build_cmd

    def set_knowledge(self, knowledge: ModelKnowledge):
        self.knowledge = knowledge

    def query_knowledge(self, query: str):
        if self.knowledge is None:
            return None
        try:
            result = self.knowledge.retrieve(query)
            return result
        except Exception as e:
            logger.error(f"Failed to query knowledge: {e}")
            return None

    def preprocess(self, out_path: Path):
        self.set_stage(FVTStage.PREPROCESS)
        if self.SINGLE_FILE_PROVE:
            return

        RustASTPreprocessor.PROCESSOR_BIN = self.PROCESSOR_BIN
        rust_preprocessor = RustASTPreprocessor(self.crate_path)
        info_dict = rust_preprocessor.run()
        self.info = InfoRepository.load_from_dict(info_dict)

    def load_info_pkl(self, path_pkl: Path):
        self.info = InfoRepository.load(path_pkl)

    def call_graph(self, json_path: Path, input_path: Path):
        cmd = f"{self.PROCESSOR_BIN} call -c {self.crate_path} -o {json_path} -i {input_path}"
        logger.debug(f"Running Verus call graph for {input_path}: \n{cmd}")
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            errors="replace",
        )
        output = result.stderr
        if output:
            logger.warning(
                f"AST preprocessor warning/error for {self.crate_path}: \n{output}"
            )

        if result.returncode != 0:
            logger.error(
                f"Failed to run Rust AST preprocessor for {self.crate_path}: \n{cmd}\nerror: \n{result.stderr}"
            )
            return

        self.cg_infos = json.loads(json_path.read_text(encoding="utf-8"))

    def find_enclosing_function(self, pos: FilePos):
        if self.info == None:
            return None, None
        for func_info in self.info.function_infos.values():
            func_info = func_info
            (pos_impl_start, pos_impl_end) = func_info.impl_range
            if pos_impl_start is None or pos_impl_end is None:
                continue
            if pos_impl_start.file != pos.file:
                continue
            if pos_impl_start <= pos <= pos_impl_end:
                return func_info.location, func_info.impl_range
        return None, None

    def run(self) -> tuple[VerifyStatus, str]:
        """
        Run verify for FVT

        :return (VerifyStatus, stderr)
        """
        if self.verify_cmd is None:
            raise ValueError("Verification command not set.")
        logger.info(f"Verifying {self.crate_path} with command: {self.verify_cmd}")
        try:
            result = subprocess.run(
                self.verify_cmd,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.verify_base_path,
            )
            logger.debug(
                f"returncode={result.returncode}\n"
                f"Verification result: {result.stdout}"
            )
        except subprocess.TimeoutExpired as e:
            logger.error(f"Verification command timed out: {e}")
            return self.record_verification_result(VerifyStatus.TIMEOUT, str(e))
        except subprocess.CalledProcessError as e:
            logger.error(f"Verification command failed: {e}")
            return self.record_verification_result(VerifyStatus.FAIL, str(e))
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise e

        if result.stderr.find("error: aborting due to") >= 0:
            if is_verify_error(result.stdout):
                return self.record_verification_result(
                    VerifyStatus.VERIFY_ERROR, result.stderr
                )
            else:
                return self.record_verification_result(
                    VerifyStatus.BUILD_ERROR, result.stderr
                )
        elif result.returncode != 0:
            logger.critical(
                "Failed with Uncatchable error, most likely a Rust context error."
            )
            return self.record_verification_result(
                VerifyStatus.RUST_ERROR, result.stderr
            )
        else:
            return self.record_verification_result(VerifyStatus.SUCCESS, "")

    def query_write(
        self,
        prompter_class,
        path: Path,
        ori_code: str,
        knowledge: str,
        err_msg: Optional[str] = None,
    ):
        """
        Query the LLM with the given prompter class and write the result to the file.

        :param prompter_class: The prompter class to use for querying.
        :param path: The path to the file to write to.
        :param ori_code: The original code to be fixed.
        :param knowledge: The knowledge to be used in the query.
        :param err_msg: (Optional) The error message to be used in the query.
        """
        if self.llm_chat is None:
            logger.error(
                f"Cannot query prompter {prompter_class.__name__} without an LLM chat"
            )
            return
        prompter = prompter_class(self.llm_chat)
        if err_msg is not None:
            fixed_code = prompter.prompt(ori_code, err_msg, knowledge)
        else:
            fixed_code = prompter.prompt(ori_code, knowledge)
        self.llm_chat.remove_last_query()
        self.query_count += 1
        if fixed_code == "":
            logger.error(f"No fixed code generated for FVT {path}")
            return
        else:
            logger.debug(f"Fixed code for FVT {path}:\n{fixed_code}")
            fvt_file_code = path.read_text(encoding="utf-8")
            fvt_file_code = fvt_file_code.replace(ori_code, fixed_code)
            self.write_to_file(path, fvt_file_code)
            self.record_stage_artifact(path.read_text(encoding="utf-8"))

    def write_to_file(self, file_path: Path, content: str):
        file_path.write_text(content, encoding="utf-8")

    def record_current_token(self):
        """
        Record current token consumption
        """
        if self.llm_chat is None:
            self.tokens = (0, 0)
            return
        self.tokens = self.llm_chat.token

    def log_status(self, log_path: Optional[Path] = None):
        """
        Log the status of the FVT.
        """
        status = {
            "crate_path": str(self.crate_path),
            "current_stage": self.current_stage.value,
            "verify_cmd": self.verify_cmd,
            "query_count": self.query_count,
            "remain_san_rounds": self.remain_refine_rounds,
            "sanitized": self.refined,
            "verification_status": (
                self.verification_status.value
                if self.verification_status is not None
                else None
            ),
            "prompt_tokens": (
                self.llm_chat.token[0] - self.tokens[0]
                if self.llm_chat is not None
                else 0
            ),
            "completion_tokens": (
                self.llm_chat.token[1] - self.tokens[1]
                if self.llm_chat is not None
                else 0
            ),
        }
        logger.info(json.dumps(status, indent=4))
        if log_path is not None and log_path.parent.exists():
            log_path.write_text(json.dumps(status, indent=4), encoding="utf-8")
            logger.info(f"log in status to {log_path}")

    def backup(self, file_path: Path, backup_dir: Path):
        """
        Backup the FVT file.
        """
        if not backup_dir.exists():
            backup_dir.mkdir(parents=True, exist_ok=True)
        backup_file_path = (
            backup_dir / f"{file_path.stem}-{self.query_count}{file_path.suffix}"
        )
        shutil.copy(file_path, backup_file_path)
