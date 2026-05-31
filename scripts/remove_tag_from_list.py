import json
import sys

DEFAULT_PATH = "data/lists/tags.json"
SERVER_PREFIX = "/usr/bin/dost/homepage"


def get_path(path_arg: str | None) -> str:
    if path_arg is None or path_arg == "local":
        return DEFAULT_PATH
    elif path_arg == "server":
        return f"{SERVER_PREFIX}/{DEFAULT_PATH}"
    else:
        return path_arg

def remove_tag(tag: str, path: str) -> bool:
    """
    Remove a tag from tags.json and overwrite the file.

    Returns:
        True if the tag was found and removed,
        False if the tag did not exist.
    """
    with open(path, "r", encoding="utf-8") as f:
        tags = json.load(f)

    if tag not in tags:
        return False

    del tags[tag]

    with open(path, "w", encoding="utf-8") as f:
        json.dump(tags, f, ensure_ascii=False, indent=4)

    return True


def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print(
            f"Usage: {sys.argv[0]} <tag> [local|server|custom_path]"
        )
        sys.exit(1)

    tag = sys.argv[1]
    path = get_path(sys.argv[2] if len(sys.argv) == 3 else None)

    if remove_tag(tag, path):
        print(f"Removed tag '{tag}'")
    else:
        print(f"Tag '{tag}' not found")
        sys.exit(1)


if __name__ == "__main__":
    main()
