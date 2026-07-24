from pathlib import Path


def count_files(root: Path) -> int:
    return sum(1 for item in root.iterdir() if item.is_file())


if __name__ == "__main__":
    print(count_files(Path(".")))
