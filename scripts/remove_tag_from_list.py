import json
import sys
from pathlib import Path
from typing import List

DEFAULT_TAGS_PATH = "data/lists/tags.json"
DEFAULT_ENTRIES_PATH = "data/file/"
SERVER_PREFIX = "/usr/bin/dost/homepage"


def resolve_base_path(path_arg: str | None) -> str:
    if path_arg is None or path_arg == "local":
        return Path(".")
    elif path_arg == "server":
        return Path(SERVER_PREFIX)
    else:
        return Path(path_arg)

def load_json(path: Path): 
    with open(path, "r", encoding="utf-8") as f: 
        return json.load(f)

def write_json(path: Path, data): 
    with open(path, "w", encoding="utf-8") as f: 
        json.dump(data, f, ensure_ascii=False, indent=4)

def delete_or_rename_tag(
    tags_path: List[str], old_tag: str, new_tag: str|None
) -> bool:
    tags = load_json(tags_path)

    if old_tag not in tags:
        return False

    if new_tag is None: 
        del tags[old_tag]
    else: 
        tag_data = tags.pop(old_tag) 
        tag_data["abbr"] = new_tag 
        tags[new_tag] = tag_data

    write_json(tags_path, tags)
    return True

def delete_or_rename_tag_in_entries(
    entries_path: List[str], old_tag:str, new_tag: str|None
) -> int: 
    changed_files = 0 

    for json_path in entries_path.glob("**.json"): 
        data = load_json(json_path)

        if "_tags" not in data or not isinstance(data["_tags"], list):
            print(f"No tags found in {data['key']}")
            continue
        
        old_tags = data["_tags"] 

        if old_tag not in old_tags: 
            continue 

        if new_tag is None: 
            data["_tags"] = [tag for tag in old_tags if tag != old_tag] 
        else: 
            data["_tags"] = [
                new_tag if tag == old_tag else tag 
                for tag in old_tags
            ]
             # remove duplicates, preserving order
            data["_tags"] = list(dict.fromkeys(data["_tags"]))
        
        write_json(json_path, data)
        changed_files += 1

    return changed_files

def main():
    if len(sys.argv) not in (2, 3, 5):
        print(
            f"Usage:\n"
            f"  {sys.argv[0]} <tag> [local|server|custom_base_path]\n"
            f"  {sys.argv[0]} <old_tag> [local|server|custom_base_path] rename <new_tag>"
        )
        sys.exit(1)

    old_tag = sys.argv[1]
    path_arg = sys.argv[2] if len(sys.argv) >= 3 else None
    new_tag = None

    if len(sys.argv) == 5:
        if sys.argv[3] != "rename":
            print("Error: third parameter must be 'rename'")
            sys.exit(1)
        new_tag = sys.argv[4]

    base_path = resolve_base_path(path_arg)
    tags_path = base_path / DEFAULT_TAGS_PATH
    entries_path = base_path / DEFAULT_ENTRIES_PATH

    action = "Deleted" if new_tag is None else "Renamed"

    if delete_or_rename_tag(tags_path, old_tag, new_tag):
        print(f"{action} tag '{old_tag}'")
        changed_entries = delete_or_rename_tag_in_entries(entries_path, old_tag, new_tag)
        print(f"Updated entry files: '{changed_entries}'")
    else:
        print(f"Tag '{tag}' not found")
        sys.exit(1)


if __name__ == "__main__":
    main()
