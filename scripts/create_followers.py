from pathlib import Path
import json
import os
import random
import re
import unicodedata
from typing import Any, Dict, List

TXTAD_PATH = "/srv/txtad-data/"
DOST_PATH = "/usr/bin/dost/homepage/"

PATH_TO_TXTAD_CHARS = Path(TXTAD_PATH, "dost/game_files/Characters/")
PATH_TO_DOST_CHARS = Path(DOST_PATH, "data/file/")

PATH_TO_FOLLOWER_JSONS = "pleroma/followers.json"

def __tags(data: Dict[str, Any]) -> List[str]: 
    if "_tags" in data: 
        return data["_tags"] 
    return []

def create_followers(char, ctx): 
    followers = [] 
    if ctx["attributes"]["block"] == "NEUTRAL": 
        followers.append("IKAC")
        followers.append("FSB")
        if ctx["username"] not in ["kim_sokolow", "anja_markova", "mara_kessler", "mika_sorin"]:
            followers.append("metabolic_infrastructure")

    if ctx["attributes"]["block"] == "WEST": 
        followers.append("transatlantic_genetic_meritocratic_society_tgms")
        followers.append("stiftung_wissenschaft_politik_swp")
        followers.append("ODeM")

    return {
        "username": ctx["attributes"]["username"],
        "followers": followers 
    }

if __name__ == "__main__": 
    chars = []
    for file in PATH_TO_DOST_CHARS.glob("*.json"):
        char = None 
        with open(file, "r") as f:
            char = json.load(f)
        with open(PATH_TO_TXTAD_CHARS.joinpath(f"{char['key']}.ctx"), 'r') as f:
            ctx = json.load(f)
        chars.append(create_followers(char, ctx))
    
    with open(PATH_TO_FOLLOWER_JSONS, 'w') as f:
        json.dump(chars, f)
