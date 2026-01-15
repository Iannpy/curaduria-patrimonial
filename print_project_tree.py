from pathlib import Path

EXCLUDE_DIRS = {
    "venv",
    ".git",
    "__pycache__",
    ".streamlit",
    ".idea",
    ".vscode",
}

EXCLUDE_FILES = {
    ".DS_Store",
}

def print_tree(path: Path, prefix: str = ""):
    entries = sorted(
        [e for e in path.iterdir() if e.name not in EXCLUDE_DIRS and e.name not in EXCLUDE_FILES],
        key=lambda x: (x.is_file(), x.name.lower())
    )

    for index, entry in enumerate(entries):
        connector = "└── " if index == len(entries) - 1 else "├── "
        print(prefix + connector + entry.name)

        if entry.is_dir():
            extension = "    " if index == len(entries) - 1 else "│   "
            print_tree(entry, prefix + extension)

def main():
    root = Path(".").resolve()
    print(root.name)
    print_tree(root)

if __name__ == "__main__":
    main()
