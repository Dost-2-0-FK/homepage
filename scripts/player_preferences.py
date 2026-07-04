from pathlib import Path
import json
import os
import random
import re
import unicodedata
from typing import Any, Dict, List

DOST_PATH = "/usr/bin/dost/homepage/"

PATH_TO_DOST_PLAYERS = Path(DOST_PATH, "data/")
PATH_TO_CHAR_DIST = Path("character_verteilung/players.json")

PATH_TO_DISTRIBUTION = Path("resources/character_zuteilung.json")

def get(field: str, data) -> List[str]: 
    if field in data: 
        return data[field] 
    return []

def transform(data):
    player = {} 
    player["key"] = data["key"] 
    player["positive_tags"] = get("positive_tags", data)
    player["negative_tags"] = get("negative_tags", data)
    player["nogo_tags"] = get("nogo_tags", data)
    player["positive_contacts"] = get("positive_contacts", data)
    player["nogo_contacts"] = get("nogo_contacts", data)
    player["arrival"] = get("arrival", data)
    return player

if __name__ == "__main__": 
    distributed = []
    with open(PATH_TO_DISTRIBUTION, "r") as f:
        distributed = json.load(f)

    def is_distributed(key: str) -> bool: 
        return len([d for d in distributed if d["player"] == key])

    names = []
    players = []
    for file in PATH_TO_DOST_PLAYERS.glob("*.json"):
        with open(file, "r") as f:
            data = json.load(f)
            if "name" not in data: 
                continue
            if is_distributed(data["key"]): 
                print(f"Already distributed: {data['key']}")
                continue
            if "Jenni" in data["name"]: 
                print("Skipped: ", data["name"])
                continue

            if "status" not in data or data["status"] != "Anwesend": 
                continue

            else: 
                players.append(transform(data))
                names.append(data["name"])

    print(f"Writing {len(players)} players: {names}")

    with open(PATH_TO_CHAR_DIST, "w") as f:
        json.dump(players, f)
