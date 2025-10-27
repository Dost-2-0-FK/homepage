#!/usr/bin/env python3
import json, os, subprocess, sys
from pathlib import Path

DOMAIN = "dost-2-0-fk.art"
JSON_PATH = "/etc/dost/collectives.json"
OUT = "/etc/postfix/virtual_collectives"   # wir bauen LMDB daraus

def main(path = None, out = None): 
    if path:
        JSON_PATH = path 
    if out: 
        OUT = out
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    users = {k.strip().lower(): v.strip().lower() for k, v in data.get("users", {}).items()}
    # Mapping: kollektiv -> [emails], (nick, kollektiv) -> email
    coll_to_emails = {}
    nickcoll_to_email = {}

    for email, spec in users.items():
        if "." in spec:
            nick, coll = spec.split(".", 1)
            nickcoll_to_email[(nick, coll)] = email
        else:
            coll = spec
        coll_to_emails.setdefault(coll, []).append(email)

    lines = []

    # Gruppenadressen
    for coll, emails in sorted(coll_to_emails.items()):
        rcpts = sorted(set(e for e in emails if e))
        if not rcpts:
            continue  # keine leere Alias-Zeile schreiben
        lines.append(f"{coll}@{DOMAIN}\t{', '.join(rcpts)}")

    # Nickname+Kollektiv
    for (nick, coll), email in sorted(nickcoll_to_email.items()):
        if email:
            lines.append(f"{nick}.{coll}@{DOMAIN}\t{email}")

    content = "\n".join(lines) + ("\n" if lines else "")
    Path(OUT).write_text(content, encoding="utf-8")

    # LMDB bauen und Postfix neu laden
    if not path and not out:
        subprocess.check_call(["postmap", f"lmdb:{OUT}"])
        subprocess.check_call(["systemctl", "reload", "postfix"])
        print(f"Built {OUT} with {len(lines)} aliases.")

if __name__ == "__main__":
    try:
        main("resources/communicate.json", "virtual")
    except Exception as e:
        print("ERROR:", e, file=sys.stderr)
        sys.exit(1)

