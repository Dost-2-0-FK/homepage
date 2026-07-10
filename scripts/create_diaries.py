
TXTAD_PATH = "/srv/txtad-data/"

PATH_TO_TXTAD_CHARS = Path(TXTAD_PATH, "dost/game_files/Zones/")
PATH_TO_TXTAD_CHARS = Path(TXTAD_PATH, "dost/game_files/Characters/")

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

def create_diary(username

if __name__ == "__main__": 
    for file in PATH_TO_DOST_CHARS.glob("*.ctx"):
        with open(file, "r") as f:
            data = json.load(f)
            user
