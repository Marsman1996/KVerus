"""
Configuration file templates.

This module provides template generation functions for creating
clean configuration files without comments.
"""

import os


def create_minimal_config() -> str:
    """Create empty configuration file with basic structure."""
    # Use appropriate binary extension for the current platform
    exe_ext = ".exe" if os.name == "nt" else ""

    return f"""[preprocessor]
dump_call_graph = false

[comprehender]
embedding_llm = ""
comprehension_llm = ""
retrieve_top_k = 10
function_batch_size = 24

[prover]
prove_llm = ""

[refiner]
refine_llm = ""
refinement_rounds = 10
validate_code = false

[llm]
default_llm = ""
validate_llm = true
enable_log = true

[paths]
verus_processor = "{{KVERUS_PATH}}/build/bin/PromeX-Verus{exe_ext}"
verus_dir = ""
"""
