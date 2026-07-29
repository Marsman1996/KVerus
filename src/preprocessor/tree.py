import json
from pathlib import Path


def dump_tree(root: Path, output_file: Path):
    tree_lines = generate_tree(root)
    tree_lines.insert(0, str(root))
    tree_output = "\n".join(tree_lines)

    # Save to file
    output_file.write_text(tree_output, encoding="utf-8")


def generate_tree(path: Path, prefix: str = "") -> list[str]:
    lines = []
    entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name))
    pointers = ["├── "] * (len(entries) - 1) + ["└── "]

    for pointer, entry in zip(pointers, entries):
        lines.append(f"{prefix}{pointer}{entry.name}")
        if entry.is_dir():
            extension = "│   " if pointer == "├── " else "    "
            lines.extend(generate_tree(entry, prefix + extension))
    return lines


if __name__ == "__main__":
    import sys

    # Replace with your target path
    root = Path(sys.argv[1])
    output_file = Path(sys.argv[2])

    dump_tree(root, output_file)

    print(f"Directory tree written to {output_file.resolve()}")
