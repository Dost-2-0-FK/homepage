from pulp import *
import json
import sys

def norm(s):
    return s.strip().casefold()

total_offending_set = set()
total_offending_set_nogo = set()
def build_ilp(players, characters):
    model = LpProblem("PlayerCharacterAssignment", LpMaximize)

    player_keys = [p["key"] for p in players]
    char_keys = [c["key"] for c in characters]

    player_by_key = {p["key"]: p for p in players}
    char_by_key = {c["key"]: c for c in characters}

    x = {
        (p, c): LpVariable(f"x_{p}_{c}", cat="Binary")
        for p in player_keys
        for c in char_keys
    }


    for p in player_keys:
        model += lpSum(x[p, c] for c in char_keys) == 1

    for c in char_keys:
        model += lpSum(x[p, c] for p in player_keys) <= 1

    score = {}
    for p in players:
        nogo_tags = {
            norm(t)
            for t in p.get("nogo_tags", [])
            if t.strip()
        }

        for character in characters:
            char_tags = {
                norm(t)
                for t in character.get("tags", [])
            }
            # Score preferences
            score[p["key"],character["key"]] = len(
                set(map(norm,p["positive_tags"])) &
                set(map(norm,character["tags"]))
            )

            score[p["key"],character["key"]] -= len(
                set(map(norm,p["negative_tags"])) &
                set(map(norm,character["tags"]))
            )


            # Forbid nogo tags
            if nogo_tags & char_tags:
                model += x[p["key"], character["key"]] == 0

    contacts = {}
    all_contacts = {}

    # Only prevent private contacts, more make the model infeasible
    for c in characters:
        contacts[c["key"]] = set(
            c.get("private_contacts", [])
        )
        all_contacts[c["key"]] = set(
            c.get("private_contacts", [])
            + c.get("zone_contacts", [])
            + c.get("block_contacts", [])
        )

    character_replace = {
      "": "",
      "X8": "1txX-Elq4-oUDm-a1oe",
      "Dr. Khorana, Rishi;": "CzCh-jnoo-sxew-K9qp", 
      "Batyr, Bogenbay;": "7kYc-WgGX-Iafe-TLju",
      "Ruth Antonia Vogelvrai": "0VgW-Q0xK-PKK8-tNKt",
      "Vogelvrai, Ruth": "0VgW-Q0xK-PKK8-tNKt",
      "Guanqi, Luo Shi ": "5XeZ-elqC-DYLA-AU17", 
      "Ingrid Cavelti": "0kOD-jJw6-eTUk-0xEW",
      "Song, Yeji ": "jGCO-kAF0-KI0S-iuBC"
    }

    for p in players:
        p_key = p["key"]

        nogo_players = {
            q.strip() for q in p.get("nogo_contacts", [])
            if q.strip()
        }

        for q_key in nogo_players:
            if q_key not in player_by_key:
                print(f"Unknown key of {p_key} in nogo players: {q_key}, ignoring.")
                total_offending_set_nogo.add(q_key)
                continue

            for c_key in char_keys:
                for d_key in contacts[c_key]:
                    if d_key not in char_by_key:
                        if d_key not in character_replace:
                            print(f"Unknown key in private contacts of character {c_key}: {d_key}, ignoring.")
                            total_offending_set.add(d_key)
                            continue
                        d_key = character_replace[d_key]
                        if d_key not in char_by_key:
                            continue

                    model += (
                        x[p_key, c_key]
                        + x[q_key, d_key]
                        <= 1
                    )

    ARRIVAL_EXCLUSIONS = {
        "später": {"präsident", "security"},
        "16:00": {"ikac"},
        "17:30": {"ikac"},
    }

    for player in players:
        arrival = norm(player.get("arrival", ""))

        forbidden_tags = {
            norm(tag)
            for tag in ARRIVAL_EXCLUSIONS.get(arrival, set())
        }

        if not forbidden_tags:
            continue

        for character in characters:
            char_tags = {
                norm(tag)
                for tag in character.get("tags", [])
            }

            if forbidden_tags & char_tags:
                model += x[player["key"], character["key"]] == 0

    model += lpSum(
        score[(p, c)] * x[p, c]
        for p in player_keys
        for c in char_keys
    )

    return model, x

with open("players.json", "r") as jsonfile: 
    players = json.load(jsonfile)
with open("characters.json", "r") as jsonfile2: 
    characters = json.load(jsonfile2)
print(f"{len(players)} and {len(characters)}")
model,x = build_ilp(players,characters)
model.solve()
print("Status:", LpStatus[model.status])

assignments = []

player_keys = [p["key"] for p in players]
char_keys = [c["key"] for c in characters]

assigned_players = set()
assigned_characters = set()
for p in player_keys:
    for c in char_keys:
        if value(x[p, c]) > 0.99:
            if p in assigned_players:
                print("Double assignment!")
                sys.exit(-1)
            assigned_players.add(p)
            if c in assigned_characters:
                print("Double assignment to same character!")
                sys.exit(-1)
            assigned_characters.add(c)
            assignments.append({
                "player": p,
                "character": c
            })

if len(p) != len(c):
    print("Sanity check failed! #Players != #Characters!")
    sys.exit(-1)
with open("output.json","w") as w:
    json.dump(assignments,w)
print(f"Missing character keys {total_offending_set}")
print(f"Missing nogo keys {total_offending_set_nogo}")
