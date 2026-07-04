from pathlib import Path
import json
import sys

DOST_PATH = "/usr/bin/dost/homepage/"
PATH_TO_DOST_PLAYERS = Path(DOST_PATH, "data/")


def main():
    if len(sys.argv) != 3:
        print(
            f"Usage:\n"
            f"  {sys.argv[0]} <name> <tag>\n"
        )
        sys.exit(1)

    name = sys.argv[1]
    tag = sys.argv[2]

    print(f"Tying to add {tag} to {name}")

    user = None
    for file in PATH_TO_DOST_PLAYERS.glob("*.json"):
        with open(file, "r") as f:
            data = json.load(f)
            if 'name' in data and name.strip() == data["name"].strip(): 
                print(f"Found {name}: {data['name']}") 
                inp = input("Apply? (y/n) ") 
                if inp == "y": 
                    user = data
                else: 
                    continue

    if user is not None: 
        print(f"Adding tag \"{tag}\" to user: {user['name']}")

        if tag in user["nogo_tags"]: 
            print("Tag already exists!") 
        else: 
            user["nogo_tags"].append(tag)

            with open(PATH_TO_DOST_PLAYERS.joinpath(f"{user['key']}.json"), 'w') as f:
                json.dump(user, f)


if __name__ == "__main__": 
    main()
