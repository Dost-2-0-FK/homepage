#!/usr/bin/env python3
import json, os, subprocess, sys
from pathlib import Path

DOMAIN = "dost-2-0-fk.art"

SRV_PATH = "/usr/bin/dost/homepage/"
POSTFIX_PATH = "/etc/postfix/"

JSON_PATH = "resources/communicate.json"
OUT_FORWARD = "virtual_collectives"   # wir bauen LMDB daraus
OUT_REWRITE = "generic_collectives"   # wir bauen LMDB daraus

def main(path, out_forward, out_rewrite): 
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    users = {k.strip().lower(): v.strip().lower() for k, v in data.get("users", {}).items()}
    # Create Address re-write mapping 
    content = "\n".join(
        [f"{user}\t{mail}@{DOMAIN}" for user, mail in users.items()]
    ) + ("\n" if users else "")
    Path(out_rewrite).write_text(content, encoding="utf-8")

    # Create forward mapping
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
    Path(out_forward).write_text(content, encoding="utf-8")

    # LMDB bauen und Postfix neu laden
    if "/etc" in out_forward:
        subprocess.check_call(["postmap", f"lmdb:{out_forward}"])
        subprocess.check_call(["postmap", f"lmdb:{out_rewrite}"])
        subprocess.check_call(["systemctl", "reload", "postfix"])
        print(f"Built {out_forward} with {len(lines)} aliases.")

if __name__ == "__main__":
    try:
        # srv 
        main(
            f"{SRV_PATH}/{JSON_PATH}", 
            f"{POSTFIX_PATH}/{OUT_FORWARD}", 
            f"{POSTFIX_PATH}/{OUT_REWRITE}"
        )
        # local
        # main(JSON_PATH, OUT_FORWARD, OUT_REWRITE)

    except Exception as e:
        print("ERROR:", e, file=sys.stderr)
        sys.exit(1)
