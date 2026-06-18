from pathlib import Path
import json
import os
import random
import re
import unicodedata
from typing import Any, Dict, List

from src.communicator import Comm
from src.seafiler import Seafile
from src.user_manager import UManager

TAG_HIDDEN = "hidden: "
TAG_PRESIDENT = "Präsident"

DOST_PATH = "/usr/bin/dost/homepage/"
PATH_TO_DOST_CHARS = Path(DOST_PATH, "data/file")
PATH_TO_CHAR_DIST = Path("/home/fux/homepage/character_verteilung/characters.json")

comm = Comm()
seafiler = Seafile(os.getenv("USE_SEAFILE", "False") == "True")
umanger = UManager(seafiler)

key_bloc_mapping = {}

def __bloc_from_tags_or_creator(tags: List[str], key: str) -> str: 
    if "west" in tags: 
        return "west" 
    if "parca" in tags: 
        return "parca" 
    if "ikac" in tags: 
        return "ikac" 
    if key in key_bloc_mapping: 
        return key_bloc_mapping[key]
    print(f"{key}: missing block tag!")
    user = umanger.get_user(key) 
    if user: 
        comm_user = comm.get_user(user.email)
        if comm_user: 
            collective = comm_user.collective 
            block = collective.split("-")[1] if "-" in collective else collective
            block = "schweiz" if block == "orga" else block
            key_bloc_mapping[key] = block
            return block
        else: 
            exit(f"GET BLOC: no comm-user found for key: {key}, user: {user.email}")
    else: 
        exit(f"GET BLOC: no user found for key: {key}")

def get(field: str, data) -> List[str]: 
    if field in data: 
        return data[field] 
    return []

def transform(data): 
    print(f"{data['key']}")
    char = {
        "key": data["key"],
        "name": f"{data['sirname']}, {data['name']}",
        "zone": data["zone"],
        "tags": get("_tags", data),
        "private_contacts": data["connections"],
        "block": __bloc_from_tags_or_creator(get("_tags", data), data["_creator"]),
    }
    for tag in get("_tags", data): 
        if TAG_HIDDEN in tag: 
            char["connected"] = tag[len(TAG_HIDDEN):]

    return char

def refine(chars, hidden): 
    for char in chars: 
        char["zone_contacts"] = [c["key"] for c in chars if c["zone"] == char["zone"]]
        char["block_contacts"] = [c["key"] for c in chars if c["block"] == char["block"]]
        if char["name"] in hidden: 
            print("found hidden") 
            char["tags"].extend(hidden[char["name"]]["tags"])
            char["private_contacts"].extend(hidden[char["name"]]["private_contacts"])
            print(f"Added {len(hidden[char['name']]['tags'])} tags from hidden")
            print(f"Added {len(hidden[char['name']]['private_contacts'])} conntacts from hidden")

    for char in chars:
        del char["name"]
        del char["block"]
    return chars

if __name__ == "__main__": 
    chars = []
    hidden = {}
    for file in PATH_TO_DOST_CHARS.glob("*.json"):
        with open(file, "r") as f:
            char = transform(json.load(f))
            if "Chernobylmann" in char["name"]: 
                continue
            if "connected" in char: 
                hidden[char["connected"]] = char
            else: 
                chars.append(char)

    print(f"Adding contacts and handling hidden for {len(chars)} characters. Hidden: {hidden.keys()}")
    chars = refine(chars, hidden)

    print(f"Writing {len(chars)} chars")

    with open(PATH_TO_CHAR_DIST, "w") as f:
        json.dump(chars, f)
