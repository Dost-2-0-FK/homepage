from pathlib import Path
import json
import os
from typing import Any, Dict, List

TXTAD_PATH = "/srv/txtad-data/"
# TXTAD_PATH = "/home/fux/homepage/test/"
DOST_PATH = "/usr/bin/dost/homepage/"

PATH_TO_TXTAD_CHARS = Path(TXTAD_PATH, "dost/game_files/Characters/")
PATH_TO_TXTAD_PLAYERS = Path(TXTAD_PATH, "dost/game_files/Players/")
PATH_TO_TXTAD_DIARIES = Path(TXTAD_PATH, "dost/game_files/Diaries/")
PATH_TO_DOST_PLAYERS = Path(DOST_PATH, "data/")

JSON_CTX_TEMPLATE = {
    "attributes": {
    },
    "description": {
        "logic": "",
        "one_time_events": "",
        "permanent_events": "",
        "shared": False,
        "txt": "."
    },
    "id": "",
    "listeners": [],
    "name": "",
    "permeable": True,
    "priority": 0,
    "re_entrycondition": "",
    "shared": True
}

def get_character(player_key, distribution) -> str: 
    chars = [c["character"] for c in distribution if c["player"] == player_key]
    if len(chars) > 1: 
        exit(f"too many or no chars for player: {player_key} => {chars}")
    if len(chars) == 0:
        print("Skipping player without distributed character: ", player_key)
        return None

    with open(PATH_TO_TXTAD_CHARS.joinpath(f"{chars[0]}.ctx"), 'r') as f:
        return json.load(f)

def transform(player, distribution): 
    player_key = player["key"]
    char = get_character(player_key, distribution)
    if char is None:
        return
    char_key = char["attributes"]["key"]
    char_username = char["attributes"]["username"]

    # Create Player
    player_ctx = JSON_CTX_TEMPLATE.copy()
    player_ctx["id"] = f"Players/{player_key}"
    player_ctx["name"] = player['name']
    player_ctx["attributes"] = {}
    player_ctx["attributes"]["key"] = player_key
    player_ctx["attributes"]["cur_char"] = char_key
    player_ctx["attributes"]["cur_username"] = char_username

    # Create Diary
    diary_ctx = JSON_CTX_TEMPLATE.copy()
    diary_ctx["id"] = f"Diaries/{player_key}"
    diary_ctx["name"] = f"{player['name']}'s Diary"
    diary_ctx["attributes"] = {}
    diary_ctx["attributes"]["key"] = player_key
    diary_ctx["attributes"]["player"] = player_key
    diary_ctx["attributes"]["cur_char"] = char_key
    diary_ctx["attributes"]["cur_username"] = char_username

    # Also update char: 
    char["attributes"]["player"] = player_key

    print("PLAYER: ", json.dumps(player_ctx, indent=4))
    print("DIARY: ", json.dumps(diary_ctx, indent=4))
    print("CHAR: ", json.dumps(char, indent=4))
    inp = input("Safe? (y/n): ")
    if inp != "y":
        exit("aborted.")

    # Safe Player
    with open(PATH_TO_TXTAD_PLAYERS.joinpath(f"{player_key}.ctx"), 'w') as f:
        json.dump(player_ctx, f)

    # Safe Diary
    with open(PATH_TO_TXTAD_DIARIES.joinpath(f"{player_key}.ctx"), 'w') as f:
        json.dump(diary_ctx, f)
   
    # Also store char: 
    with open(PATH_TO_TXTAD_CHARS.joinpath(f"{char_key}.ctx"), 'w') as f:
        json.dump(char, f)

if __name__ == "__main__": 
    with open("resources/character_zuteilung.json", 'r') as f:
        distribution = json.load(f)
    for file in PATH_TO_DOST_PLAYERS.glob("*.json"):
        with open(file, "r") as f:
            transform(json.load(f), distribution)
