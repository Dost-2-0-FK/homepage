from pathlib import Path
import json
import os
import random
from jsondiff import diff
from typing import Any, Dict, List

TAG_PRESIDENT = "Präsident"
TAG_SECU = "Security"

TXTAD_PATH = "/srv/txtad-data/"
# TXTAD_PATH = "/home/fux/homepage/test/"
DOST_PATH = "/usr/bin/dost/homepage/"

PATH_TO_TXTAD_CHARS = Path(TXTAD_PATH, "dost/game_files/Characters/")
PATH_TO_DOST_CHARS = Path(DOST_PATH, "data/file/")

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

key_bloc_mapping = {}

def __calc_aitropie(data) -> int: 
    violence = data["violence_potential"] 
    illnesses = len(data["illnesses"])
    cbis = len(data["computer_brain_interfaces"])
    return __calc_entropie(violence, illnesses, cbis)

def __calc_gen_diff(data) -> int: 
    wealth = -1 * (data["violence_potential"]-5)
    illnesses = len(data["illnesses"])
    gms = len(data["genetic_augmentations"])
    return __calc_entropie(wealth, illnesses, gms)

def __calc_entropie(pos_a: int, pos_b: int, neg: int) -> int:
    return min(max(-3, pos_a + pos_b - neg - random.randint(0,2)), 3)

def __tags(data: Dict[str, Any]) -> List[str]: 
    if "_tags" in data: 
        return data["_tags"] 
    return []

def load_char_ctx(key): 
    print("Loading: ", key)
    # Load existing character
    ctx = None
    ctx_path = PATH_TO_TXTAD_CHARS.joinpath(f"{key}.ctx")
    if os.path.exists(ctx_path): 
        print("- found", key)
        with open(ctx_path, "r") as f:
            ctx = json.load(f)
    else: 
        exit(f"Character {key}: does not yet exist, create all chars before updating!!")
    return ctx

def transform(data): 
    key = data["key"]
    # Load existing character
    ctx = load_char_ctx(key)

    print(ctx["name"])
        
    # Exit if name has changed!
    if ctx["name"] != data["sirname"] + ", " + data["name"]: 
        print(f"Character {key}: Has CHANGED NAME!!: \"{ctx['name']}\" != \"{data['sirname']}, {data['name']}\"")
        ok = input("ok? (y/n) ")
        if ok != "y": 
            exit("aborted")


    # Notify if zone has changed
    if ctx["attributes"]["zone"] != data["zone"]: 
        print(f"Character {key}: Updating zone: {ctx['attributes']['zone']} => {data['zone']}")

    # Update flexible attributes
    ctx["attributes"]["entropie"] = str(__calc_aitropie(data))
    ctx["attributes"]["gen_diff"] = str(__calc_gen_diff(data))
    ctx["attributes"]["zone"] = data["zone"]
    ctx["attributes"]["president"] = str(TAG_PRESIDENT in __tags(data))
    ctx["attributes"]["secu"] = str(TAG_SECU in __tags(data))
    ctx["attributes"]["amc_bloc"] = "[]"
    ctx["attributes"]["amc_zone"] = "[]"
    ctx["attributes"]["amc_private"] = "[]"

    # Change old "bloc" to new "block"
    if "bloc" in ctx["attributes"]: 
        cur = ctx["attributes"]["bloc"]
        del ctx["attributes"]["bloc"]
        block = "NEUTRAL"
        if cur == "west" or cur == "blau": 
            block = "WEST" 
        elif cur == "parca" or cur == "rot": 
            block = "PARCA"
        print(f"Character {key}: Updating block: {cur} => {block}")
        ctx["attributes"]["block"] = block

    # Return
    return ctx.copy()

def add_contacts(chars: List[Dict[str, Any]]) -> None: 
    for char in chars: 
        print(
            "add_contacts (zone): ", 
            char["name"], 
            f"[{char['attributes']['president']}, {char['attributes']['secu']}]"
        )
        char["attributes"]["amc_zone"] = str(
            [c["attributes"]["key"] for c in chars 
            if c["attributes"]["zone"] == char["attributes"]["zone"]]
        )

        if char["attributes"]["president"] == "True" or char["attributes"]["secu"] == "True": 
            print("add_contacts (bloc): ", char["name"])
            char["attributes"]["amc_bloc"] = str(
                [c["attributes"]["key"] for c in chars 
                if c["attributes"]["block"] == char["attributes"]["block"]]
            )
        

def safe_all(chars: List[Dict[str, Any]]) -> None: 
    for char in chars: 
        key = char['attributes']['key']
        print("LOADING ORIGINAL: ", key)
        orig = load_char_ctx(key)
        with open(PATH_TO_TXTAD_CHARS.joinpath(f"{key}.ctx"), 'w') as f:
            print("DIFF: ", diff(orig, char))
            ok = input("apply? (y/n) ")
            if ok != "y": 
                exit("aborted")
            json.dump(char, f)

if __name__ == "__main__": 
    chars = []
    for file in PATH_TO_DOST_CHARS.glob("*.json"):
        with open(file, "r") as f:
            data = json.load(f)
            transformed = transform(data.copy())
            chars.append(transformed)

    add_contacts(chars) 
    safe_all(chars)
