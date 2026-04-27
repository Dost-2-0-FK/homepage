from pathlib import Path
import json
import os
import random
from typing import Any, Dict, List

from src.communicator import Comm
from src.seafiler import Seafile
from src.user_manager import UManager

PATH_TO_TXTAD_CHARS = Path(
    "/home/fux/Documents/programming/txtad/data/games/dost/game_files/Characters/"
)
PATH_TO_DOST_CHARS = Path("data/file/")

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

CONFIG = {
    "presidents": ["Bronec, Anna"],
    "secus": [],
}

comm = Comm()
seafiler = Seafile(os.getenv("USE_SEAFILE", "False") == "True")
umanger = UManager(seafiler)

key_bloc_mapping = {}



def create_public_key(key: str) -> str: 
    return "pub_" + reorder_key(key)

def create_priv_key(key: str) -> str: 
    return "priv_" + reorder_key(key)

def reorder_key(key: str) -> str: 
    blocks = key.split("-")
    shuffled_blocks = [
        ''.join(random.sample(block, len(block)))
        for block in blocks
    ]
    return "-".join(shuffled_blocks)

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

def __bloc_from_creator_key(key: str) -> str: 
    if key in key_bloc_mapping: 
        return key_bloc_mapping[key]
    user = umanger.get_user(key) 
    if user: 
        comm_user = comm.get_user(user.email)
        if comm_user: 
            collective = comm_user.collective 
            block = collective.split("-")[1] if "-" in collective else collective
            block = "schweiz" if block == "orga" else block
            key_bloc_mapping[key] = block
            return block
    exit(f"Can't get bloc from given creator key: {key}")

def transform(data): 
    ctx = JSON_CTX_TEMPLATE 
    key = data["key"]
    ctx["id"] = key
    ctx["name"] = data["sirname"] + ", " + data["name"]
    print("transform: ", ctx["name"])
    ctx["attributes"] = {
        "name": ctx["name"],
        "key": key,
        "key_pub": create_public_key(key),
        "key_priv": create_priv_key(key),
        "entropie": str(__calc_aitropie(data)),
        "gen_diff": str(__calc_gen_diff(data)),
        "zone": data["zone"],
        "bloc": __bloc_from_creator_key(data["_creator"]),
        "president": str(ctx["name"] in CONFIG["presidents"]),
        "secu": str(ctx["name"] in CONFIG["secus"]),
        "amc_online": "0",
        "amc_bloc": "[]",
        "amc_private": "[]",
        "amc_zone": "[]",
    }
    return ctx.copy()

def add_contacts(chars: List[Dict[str, Any]]) -> None: 
    for char in chars: 
        print(
            "add_contacts (zone): ", 
            char["name"], 
            f"[{char["attributes"]["president"]}, {char["attributes"]["secu"]}]"
        )
        char["attributes"]["amc_zone"] = str(
            [c["attributes"]["key_priv"] for c in chars 
            if c["attributes"]["zone"] == char["attributes"]["zone"]]
        )

        if char["attributes"]["president"] == "True" or char["attributes"]["secu"] == "True": 
            print("add_contacts (bloc): ", char["name"])
            char["attributes"]["amc_bloc"] = str(
                [c["attributes"]["key_priv"] for c in chars 
                if c["attributes"]["bloc"] == char["attributes"]["bloc"]]
            )
        

def safe_all(chars: List[Dict[str, Any]]) -> None: 
    for char in chars: 
        with open(PATH_TO_TXTAD_CHARS.joinpath(f"{char['id']}.ctx"), 'w') as f:
            json.dump(char, f)

if __name__ == "__main__": 
    chars = []
    for file in PATH_TO_DOST_CHARS.glob("*.json"):
        with open(file, "r") as f:
            chars.append(transform(json.load(f)))
    add_contacts(chars) 
    safe_all(chars)
