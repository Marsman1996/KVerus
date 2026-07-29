from loguru import logger

from src.comprehender.knowledge import ModelKnowledge
from src import vars as global_vars
from src.utils import setup_rag


def run():
    # set configs
    comprehender_config = global_vars.config["comprehender"]
    ModelKnowledge.RETRIEVE_TOP_K = comprehender_config["retrieve_top_k"]

    rag = setup_rag(
        "embedding_llm",
        global_vars.kverus_path / "database/CortenMM/out/vstd/comprehender/documents",
    )

    model_knowledge = ModelKnowledge(
        global_vars.kverus_path / "database/CortenMM/out/vstd/preprocessor/info.json",
        rag,
    )
    query = "For any non-negative integers `x` and any positive integer `d`, if you define `q = x / d` (integer division, i.e. floor division), then `q * d <= x`. In other words, dividing and then multiplying back never overshoots the original dividend."
    lemma_excerpts = model_knowledge.retrieve(query)
    logger.info(f"For query {query}\nRetrieved {len(lemma_excerpts)} excerpts.")
    for lemma in lemma_excerpts:
        logger.info(f"Excerpt: {lemma.content}")
        logger.info(f"Source: {lemma.location}")
