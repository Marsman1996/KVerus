from functools import lru_cache

# Data-driven patterns per category (checked in order)
CATEGORY_PATTERNS: dict[str, tuple[str, ...]] = {
    "mm/page_table": ("mm/page_table",),
    "mm/frame": ("mm/frame",),
    "mm/kspace": ("mm/kspace",),
    "mm/vm_space": ("mm/vm_space",),
    "mm/heap": ("mm/heap",),
    "mm/tlb": ("tlb.rs",),
    "mm/dma": ("mm/dma",),
    "mm_other": ("mm/",),
    "sync": ("ostd/src/sync/",),
    "arch": ("ostd/src/arch/",),
    "boot": ("ostd/src/boot/",),
    "bus": ("ostd/src/bus/",),
    "cpu": ("ostd/src/cpu/",),
    "io": ("ostd/src/io/",),
    "task": ("ostd/src/task/",),
    "timer": ("ostd/src/timer/",),
    "trap": ("ostd/src/trap/",),
    "util": ("ostd/src/util/",),
}


@lru_cache(maxsize=4096)
def classify(file_name: str) -> str:
    """Return the coverage category for a given file path string.

    Falls back to "other" when no pattern matches.
    """
    for category, patterns in CATEGORY_PATTERNS.items():
        if any(p in file_name for p in patterns):
            return category
    return "other"
