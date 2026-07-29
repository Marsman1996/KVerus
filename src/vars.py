"""
Global variables
"""

from enum import Enum
from pathlib import Path


# ==================== Basic Info ====================
class SupportedLanguages(Enum):
    """
    Supported languages
    """

    NONE = "none"
    C = "c"
    CPP = "c++"
    RUST = "rust"


class SupportedTools(Enum):
    """
    Supported tools
    """

    NONE = "none"
    VERUS = "verus"


kverus_path: Path = None

# ==================== Configuration ====================

# template configuration, as default value
config_template = dict()
fvts_template = dict()

# KVerus configuration
config = dict()

# libraries configuration
fvts = dict()

# ==================== Current Library ====================

# target library name
fvt_name = ""

# target library language
fvt_language = SupportedLanguages.NONE

# fvt tool
fvt_tool = SupportedTools.NONE

# target library configuration
fvt_config = dict()
