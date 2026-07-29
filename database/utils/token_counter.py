import os
import tiktoken


def count_tokens_in_file(file_path, encoding):
    """Count the number of tokens in a file."""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
            tokens = encoding.encode(content)
            return len(tokens)
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return 0


def count_tokens_in_directory(directory):
    """Count the tokens in all files within a directory."""
    total_tokens = 0
    encoding = tiktoken.get_encoding("cl100k_base")  # Replace with the desired encoding

    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            tokens = count_tokens_in_file(file_path, encoding)
            print(f"{file_path}: {tokens} tokens")
            total_tokens += tokens

    print(f"Total tokens in directory {directory}: {total_tokens}")
    return total_tokens


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Count tokens in files within a directory."
    )
    parser.add_argument("directory", type=str, help="Path to the directory to analyze.")
    args = parser.parse_args()

    count_tokens_in_directory(args.directory)
