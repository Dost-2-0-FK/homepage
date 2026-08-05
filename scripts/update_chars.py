from pathlib import Path
import json
import os
import random
from jsondiff import diff
from typing import Any, Dict, List

TAG_PRESIDENT = "Präsident"
TAG_SECU = "Security"
TAG_HIDDEN = "hidden:"
PALADIN_KEY = "test_paladin_1789"

PROLOG_TRACKS = [
    f"gruppe-{number}{suffix}"
    for number in range(1, 5)
    for suffix in ("a", "b")
]
MAIN_TRACKS = {
    "a": (
        "PART_A_Gruppe_A1",
        "PART_A_Gruppe_A2",
        "PART_A_Gruppe_B1",
        "PART_A_Gruppe_B2",
    ),
    "b": ("Part_B_Gruppe_A", "Part_B_Gruppe_B"),
    "c": (
        "PART_C_Gruppe_A1",
        "PART_C_Gruppe_A2",
        "PART_C_Gruppe_B",
    ),
}
PART_C_USERNAMES = {"gregor_anders", "li_profdrwen"}

TXTAD_PATH = "/srv/txtad-data/"
# TXTAD_PATH = "/home/fux/homepage/test/"
DOST_PATH = "/usr/bin/dost/homepage/"

PATH_TO_TXTAD_CHARS = Path(TXTAD_PATH, "dost/game_files/Characters/")
PATH_TO_TXTAD_ZONES = Path(TXTAD_PATH, "dost/game_files/Zones/")
PATH_TO_DOST_CHARS = Path(DOST_PATH, "data/file/")

zones = {}
for file in PATH_TO_TXTAD_ZONES.glob("*.ctx"):
    with open(file, "r") as f:
        data = json.load(f)
        zones[data["attributes"]["zone"].strip()] = data["attributes"]["key"]

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

INITIAL_BLACKOUTS = ["eCb9-eWgi-GWMS-Pxg9", "RdgX-W4HP-o0FE-h8eV", "wfue-m3Io-PgQT-P3Xa" ] 

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

def __character_name(data: Dict[str, Any]) -> str:
    """Return names in the same ``surname, name`` form used by CTX files."""
    return f"{data['sirname'].strip()}, {data['name'].strip()}".strip()

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

def get_zone_key_from_name(name: str) -> str | None: 
    if name in zones: 
        return zones[name] 
    print("NAME NOT FOUND!: ", name)
    return None

def get_encrypted_pub(key: str, identities) -> str: 
    for identity in identities: 
        if identity["key"] == key: 
            return identity["encrypted_pub"]
    return ""

def transform(data, identities): 
    key = data["key"]
    encrypted_pub = get_encrypted_pub(key, identities)
    # Load existing character
    ctx = load_char_ctx(key)

    print(ctx["name"])
        
    # Exit if name has changed!
    expected_name = __character_name(data)
    ctx["name"] = ctx["name"].strip()
    if isinstance(ctx["attributes"].get("name"), str):
        ctx["attributes"]["name"] = ctx["attributes"]["name"].strip()
    if ctx["name"] != expected_name:
        print(f"Character {key}: Has CHANGED NAME!!: \"{ctx['name']}\" != \"{expected_name}\"")
        ok = input("ok? (y/n) ")
        if ok != "y": 
            exit("aborted")
        else: 
            ctx["name"] = expected_name

    # Notify if zone has changed
    if ctx["attributes"]["zone"] != data["zone"]: 
        print(f"Character {key}: Updating zone: {ctx['attributes']['zone']} => {data['zone']}")


    zone_name = data["zone"]
    zone_key = get_zone_key_from_name(zone_name)
    if not zone_key and "1.A.X" in zone_name: 
        zone_name = "1.A.X"
        zone_key = get_zone_key_from_name(zone_name)

    # Update flexible attributes
    ctx["attributes"]["encrypted_pub"] = encrypted_pub
    ctx["attributes"]["entropie"] = str(__calc_aitropie(data))
    ctx["attributes"]["gen_diff"] = str(__calc_gen_diff(data))
    ctx["attributes"]["emotions"] = str(1)
    ctx["attributes"]["zone"] = zone_name
    ctx["attributes"]["zone_key"] = zone_key
    ctx["attributes"]["president"] = str(TAG_PRESIDENT in __tags(data))
    ctx["attributes"]["secu"] = str(TAG_SECU in __tags(data))
    ctx["attributes"]["block_mandate"] = "0"
    ctx["attributes"]["in_blackout"] = str(key in INITIAL_BLACKOUTS)
    ctx["attributes"]["amc_bloc"] = "[]"
    ctx["attributes"]["amc_zone"] = "[]"
    connections = data["connections"]
    connections.append(PALADIN_KEY)
    ctx["attributes"]["amc_private"] = str(connections)

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

def add_hidden_links(
    chars: List[Dict[str, Any]], source_data: List[Dict[str, Any]]
) -> None:
    chars_by_name = {char["name"].strip(): char for char in chars}
    chars_by_key = {char["attributes"]["key"]: char for char in chars}

    for data in source_data:
        source = chars_by_key[data["key"]]
        for tag in __tags(data):
            if not tag.strip().lower().startswith(TAG_HIDDEN):
                continue

            target_name = tag.split(":", 1)[1].strip()
            if not target_name:
                raise ValueError(f"Character {data['key']} has an empty hidden tag")
            if target_name not in chars_by_name:
                raise ValueError(
                    f"Character {data['key']} links hidden character "
                    f"{target_name!r}, but no matching name exists"
                )

            target = chars_by_name[target_name]
            source_key = source["attributes"]["key"]
            target_key = target["attributes"]["key"]
            source["attributes"]["linked"] = target_key
            target["attributes"]["linked"] = source_key

def __distribute_evenly(
    char_groups: List[List[Dict[str, Any]]], attribute: str, tracks: List[str]
) -> None:
    for index, char_group in enumerate(char_groups):
        track = tracks[index % len(tracks)]
        for char in char_group:
            char["attributes"][attribute] = track

def __linked_groups(
    chars: List[Dict[str, Any]],
) -> List[List[Dict[str, Any]]]:
    chars_by_key = {char["attributes"]["key"]: char for char in chars}
    visited = set()
    groups = []

    for char in chars:
        key = char["attributes"]["key"]
        if key in visited:
            continue

        group = []
        pending = [char]
        while pending:
            member = pending.pop()
            member_key = member["attributes"]["key"]
            if member_key in visited:
                continue
            visited.add(member_key)
            group.append(member)

            linked_key = member["attributes"].get("linked")
            if linked_key and linked_key in chars_by_key:
                pending.append(chars_by_key[linked_key])

        groups.append(group)

    return groups

def distribute_audiowalk_tracks(chars: List[Dict[str, Any]]) -> None:
    groups = __linked_groups(chars)
    random.shuffle(groups)
    __distribute_evenly(groups, "audiowalk_prolog", PROLOG_TRACKS)

    for char in chars:
        char["attributes"].pop("audiowalk_epilog_main", None)
        char["attributes"]["audiowalk_epilog"] = "ritual-und-epilog"

    forced_part_c = [
        group for group in groups
        if any(
            char["attributes"].get("username", "").strip()
            in PART_C_USERNAMES
            for char in group
        )
    ]
    found_usernames = {
        char["attributes"]["username"].strip()
        for group in forced_part_c
        for char in group
        if char["attributes"].get("username", "").strip()
        in PART_C_USERNAMES
    }
    missing_usernames = PART_C_USERNAMES - found_usernames
    if missing_usernames:
        raise ValueError(
            "Required Part C usernames not found: "
            + ", ".join(sorted(missing_usernames))
        )
    if len(groups) < 32:
        raise ValueError(
            "At least 32 characters (counting each linked group once) are "
            "required for Parts A and C"
        )

    remaining = [group for group in groups if group not in forced_part_c]
    part_c = forced_part_c + remaining[:16 - len(forced_part_c)]
    remaining = remaining[16 - len(forced_part_c):]
    parts = {
        "a": remaining[:16],
        "b": remaining[16:],
        "c": part_c,
    }
    for part, part_groups in parts.items():
        __distribute_evenly(
            part_groups, "audiowalk_main", list(MAIN_TRACKS[part])
        )

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
        print("DIFF: ", diff(orig, char))
        # ok = input("apply? (y/n) ")
        # if ok != "y": 
        #     exit("aborted")
        with open(PATH_TO_TXTAD_CHARS.joinpath(f"{key}.ctx"), 'w') as f:
            json.dump(char, f)

if __name__ == "__main__": 
    identities = []
    with open("resources/identities.json", "r") as f:
        identities = json.load(f)
    chars = []
    published_data = []
    for file in PATH_TO_DOST_CHARS.glob("*.json"):
        with open(file, "r") as f:
            data = json.load(f)
            if not data["_published"]: 
                print(
                    f"Skipping unpublished character: {data['name']}, {data['sirname']}"
                )
            else:
                transformed = transform(data.copy(), identities)
                chars.append(transformed)
                published_data.append(data)

    add_hidden_links(chars, published_data)
    distribute_audiowalk_tracks(chars)
    add_contacts(chars) 
    safe_all(chars)

    # Add all characters to paladin:
    all_keys = [char["attributes"]["key"] for char in chars] 
    paladin = JSON_CTX_TEMPLATE;
    paladin["attributes"]["key"] = PALADIN_KEY
    paladin["attributes"]["name"] = "Paladin"
    paladin["attributes"]["pub_key"] = "pub_1789"
    paladin["attributes"]["priv"] = "161"
    paladin["attributes"]["entropie"] = str(0)
    paladin["attributes"]["gen_diff"] = str(0)
    paladin["attributes"]["zone"] = "TEST ZONE"
    paladin["attributes"]["president"] = str(False)
    paladin["attributes"]["secu"] = str(False)
    paladin["attributes"]["amc_bloc"] = "[]"
    paladin["attributes"]["amc_zone"] = "[]"
    paladin["attributes"]["amc_private"] = str(all_keys)
    paladin["attributes"]["inactive"] = "True"
    paladin["attributes"]["block"] = "TEST"

    with open(PATH_TO_TXTAD_CHARS.joinpath(f"{PALADIN_KEY}.ctx"), 'w') as f:
        json.dump(paladin, f)
