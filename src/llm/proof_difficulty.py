"""
Proof difficulty evaluation via LLM.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional
import json
import re

from loguru import logger

from src import vars as global_vars
from src.llm.llm import LLMChat
from src.llm.prompter import Prompter
from src.utils import setup_llm


FEW_SHOT_PLACEHOLDER = "{{FEW_SHOT_EXAMPLES}}"


@dataclass
class ProofDifficultyResult:
    """
    Parsed LLM response for proof difficulty.
    """

    score: int
    rationale: str
    risk_factors: Optional[list[str]]

    def to_dict(self) -> Dict[str, Any]:
        """
        JSON-friendly output.
        """
        payload: Dict[str, Any] = {
            "score": self.score,
            "rationale": self.rationale,
        }
        if self.risk_factors:
            payload["risk_factors"] = self.risk_factors
        return payload


class ProofDifficultyPromptTemplate:
    """
    Builds the prompt for the proof difficulty evaluation.
    """

    SYSTEM_PROMPT = "proof_difficulty/proof_difficulty.sys"
    USER_PROMPT = "proof_difficulty/proof_difficulty.usr"

    def __init__(self):
        self.system_prompt = Prompter._read_prompt(self.SYSTEM_PROMPT)
        self.user_prompt = Prompter._read_prompt(self.USER_PROMPT)

    def build(
        self,
        *,
        fvt_name: str,
        function_name: str,
        signature: str,
        file_path: str,
        impl_span: str,
        metadata_block: str,
        function_code: str,
        few_shot_examples: str = "",
    ) -> str:
        """
        Inject runtime values into the prompt template.
        """
        prompt = self.user_prompt
        replacements = {
            FEW_SHOT_PLACEHOLDER: few_shot_examples.strip()
            or "[[ADD_FEW_SHOT_EXAMPLES_HERE]]",
            "{{FVT_NAME}}": fvt_name,
            "{{FUNCTION_NAME}}": function_name,
            "{{FUNCTION_SIGNATURE}}": signature,
            "{{FILE_PATH}}": file_path,
            "{{IMPL_SPAN}}": impl_span,
            "{{FUNCTION_METADATA}}": metadata_block,
            "{{FUNCTION_CODE}}": function_code,
        }
        for token, value in replacements.items():
            prompt = prompt.replace(token, value)
        return Prompter.economize_prompt(prompt)


class ProofDifficultyEvaluator:
    """
    Helper that queries an LLM with the proof difficulty prompt and parses the response.
    """

    MIN_SCORE = 1
    MAX_SCORE = 15

    def __init__(self, llm_name: Optional[str] = None):
        eval_config = global_vars.config.get("eval", {})
        if llm_name is None:
            llm_name = eval_config.get("difficulty_llm")
        examples = eval_config.get("difficulty_examples", "")

        self.prompt_template = ProofDifficultyPromptTemplate()
        self.few_shot_examples = examples

        client = setup_llm(llm_name or "")
        self.chat = LLMChat(client, system_prompt=self.prompt_template.system_prompt)
        self.model_name = getattr(client, "model", client.__class__.__name__)

    def evaluate(
        self,
        *,
        fvt_name: str,
        function_name: str,
        signature: str,
        file_path: str,
        impl_span: str,
        metadata: Dict[str, Any],
        function_code: str,
    ) -> Dict[str, Any]:
        """
        Run the evaluation and return structured data.
        """
        metadata_block = json.dumps(metadata, indent=2, ensure_ascii=False)
        prompt = self.prompt_template.build(
            fvt_name=fvt_name,
            function_name=function_name,
            signature=signature,
            file_path=file_path,
            impl_span=impl_span,
            metadata_block=metadata_block,
            function_code=function_code,
            few_shot_examples=self.few_shot_examples,
        )
        response, reasoning = self.chat.query_reasoning(prompt)
        parsed = self.parse_response_text(response)
        return {
            "score": parsed.score,
            "rationale": parsed.rationale,
            "risk_factors": parsed.risk_factors,
            "raw_response": response,
            "reasoning": reasoning,
            "model": self.model_name,
        }

    @staticmethod
    def parse_response_text(response: str) -> ProofDifficultyResult:
        """
        Parse JSON payload from the LLM response and enforce the scoring contract.
        """
        if not response or not response.strip():
            raise ValueError("Empty LLM response for proof difficulty evaluation.")

        json_text = ProofDifficultyEvaluator._extract_json_block(response)
        try:
            payload = json.loads(json_text)
        except json.JSONDecodeError as exc:
            logger.error(f"Failed to parse proof difficulty response as JSON: {exc}")
            raise

        score = payload.get("score") or payload.get("difficulty")
        if score is None:
            raise ValueError("LLM response did not include a 'score' field.")
        try:
            score_value = int(float(score))
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Score is not numeric: {score}") from exc
        if not (
            ProofDifficultyEvaluator.MIN_SCORE
            <= score_value
            <= ProofDifficultyEvaluator.MAX_SCORE
        ):
            raise ValueError(
                f"Score {score_value} is outside the allowed range "
                f"[{ProofDifficultyEvaluator.MIN_SCORE}, {ProofDifficultyEvaluator.MAX_SCORE}]"
            )

        rationale = str(payload.get("rationale", "")).strip()
        if not rationale:
            raise ValueError("LLM response is missing a rationale for the score.")
        risk_factors_raw = payload.get("risk_factors")
        risk_factors: Optional[list[str]] = None
        if isinstance(risk_factors_raw, list):
            risk_factors = [
                str(item).strip() for item in risk_factors_raw if str(item).strip()
            ]
        return ProofDifficultyResult(
            score=score_value, rationale=rationale, risk_factors=risk_factors
        )

    @staticmethod
    def _extract_json_block(response: str) -> str:
        """
        Extract a JSON object from the response, tolerating code fences or prose.
        """
        fenced_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
        if fenced_match:
            return fenced_match.group(1)
        start = response.find("{")
        end = response.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("Unable to locate JSON payload in LLM response.")
        return response[start : end + 1]
