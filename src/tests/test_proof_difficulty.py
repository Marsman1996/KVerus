import pytest

from src.llm.proof_difficulty import ProofDifficultyEvaluator


def test_parse_response_text_accepts_json_block():
    response = """Here is the assessment:
```json
{
  "score": 9,
  "rationale": "Long proof with several helper lemmas and ownership invariants.",
  "risk_factors": ["deep trait bounds"]
}
```"""
    result = ProofDifficultyEvaluator.parse_response_text(response)
    assert result.score == 9
    assert "helper lemmas" in result.rationale
    assert result.risk_factors == ["deep trait bounds"]


def test_parse_response_text_rejects_out_of_range_score():
    bad_response = '{"score": 42, "rationale": "too big"}'
    with pytest.raises(ValueError):
        ProofDifficultyEvaluator.parse_response_text(bad_response)


def test_parse_response_text_requires_score():
    bad_response = '{"rationale": "missing score"}'
    with pytest.raises(ValueError):
        ProofDifficultyEvaluator.parse_response_text(bad_response)
