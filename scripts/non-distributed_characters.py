import json
import os
from typing import Any, Dict, List
from pathlib import Path

DOST_PATH = "/usr/bin/dost/homepage/"
TXTAD_PATH = "/srv/txtad-data/"

PATH_TO_TXTAD_CHARS = Path(TXTAD_PATH, "dost/game_files/Characters/")
PATH_TO_DOST_PLAYERS = Path(DOST_PATH, "data/")
PATH_TO_DOST_CHARS = Path(DOST_PATH, "data/file")

PATH_TO_DISTRIBUTION = Path("resources/character_zuteilung.json")
# PATH_TO_DISTRIBUTION = Path("character_verteilung/output.json")

inactive = 0 

def load_char_ctxs() -> List: 
    chars = []
    for file in PATH_TO_TXTAD_CHARS.glob("*.ctx"):
        with open(file, "r") as f:
            ctx = json.load(f)
            if "test_" not in ctx["id"]: 
                chars.append(ctx)
    return chars

def get_player_name(key) -> str: 
    try:
        with open(PATH_TO_DOST_PLAYERS.joinpath(f"{key}.json"), "r") as f:
            player = json.load(f)
            return player["name"]
    except: 
        return f"no name for: {key}"

def get_creator(key) -> str: 
    creator = ""
    try:
        with open(PATH_TO_DOST_CHARS.joinpath(f"{key}.json"), "r") as f:
            char = json.load(f)
            creator = char["_creator"]
    except: 
        return f"no name for: {key}"

    return get_player_name(creator)

def check_distribution(char, distributed_chars): 
    if char["attributes"]["inactive"] == "True": 
        global inactive 
        inactive += 1
        # print("Skipping inactive characters: ", inactive)
        return

    name = char["name"]
    key = char["attributes"]["key"] 
    block = char["attributes"]["block"] 

    to = [d["player"] for d in distributed_chars if d["character"] == key]
    if len(to) > 0:
        player = get_player_name(to[0])
        creator = get_creator(key)
        # print(f"Character: {key} [creator={creator}, name={name}, block={block}] distributed to: {player}")
        print(f"[creator={creator}, name={name}, block={block}] distributed to: {player}")
    else: 
        print(f"Character: {key} [name={name}, block={block}] not distributed yet")
        return

if __name__ == "__main__": 
    distributed_chars = []
    with open(PATH_TO_DISTRIBUTION, "r") as f:
        distributed_chars = json.load(f)

    for ctx in load_char_ctxs():
         check_distribution(ctx, distributed_chars)
