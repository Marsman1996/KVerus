"""
Shared constants for configuration management.
"""

from typing import Dict, List, Tuple

# Module mappings for configuration
MODULE_MAPPINGS = {
    "embedding": ("comprehender", "embedding_llm"),
    "comprehension": ("comprehender", "comprehension_llm"),
    "prover": ("prover", "prove_llm"),
    "refiner": ("refiner", "refine_llm"),
}

# Module descriptions for setup wizard
MODULE_DESCRIPTIONS = [
    ("embedding", "Text embedding for RAG"),
    ("comprehension", "Code comprehension"),
    ("prover", "Formal verification proving"),
    ("refiner", "Proof fixing and refinement"),
]

# Module display names for options/listing
MODULE_DISPLAY_NAMES = {
    "embedding": "Embedding",
    "comprehension": "Comprehension",
    "prover": "Prover",
    "refiner": "Fixer",
}

# Validation structure for checking assignments
VALIDATION_MODULES = {
    "comprehender": ["embedding_llm", "comprehension_llm"],
    "prover": ["prove_llm"],
    "refiner": ["refine_llm"],
}

# Path mappings
BINARY_MAPPINGS = [
    ("verus_dir", "Verus project directory"),
    ("verus_processor", "Verus processor"),
]

# Path validation - expected file names
REQUIRED_BINARIES = {
    "verus_dir": ["verus", "verus.exe"],  # Directory should contain verus binary
    "verus_processor": [
        "PromeX-Verus",
        "PromeX-Verus.exe",
    ],
}


def get_display_mapping() -> List[Tuple[str, str]]:
    """Get module mappings in display format (config_key, display_name)."""
    return [
        (f"{section}.{param}", MODULE_DISPLAY_NAMES[module])
        for module, (section, param) in MODULE_MAPPINGS.items()
    ]


def get_assignment_options() -> List[str]:
    """Get formatted assignment options for CLI help text."""
    options = ["  default       - Default LLM for all modules"]

    for module, description in MODULE_DESCRIPTIONS:
        section, param = MODULE_MAPPINGS[module]
        option_line = f"  {module:<12} - {description} ({section}.{param})"
        options.append(option_line)

    return options
