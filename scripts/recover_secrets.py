#!/usr/bin/env python3
"""Recover secrets from a running homepage process through its rendered pages."""

import argparse
import json
import os
from pathlib import Path
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup


def user_keys(data_dir: Path):
    for path in sorted(data_dir.glob("*.json")):
        try:
            user = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        key = user.get("key")
        if key:
            yield key


def secrets_from_page(html: str, creator: str):
    soup = BeautifulSoup(html, "html.parser")
    recovered = []
    for identifier_input in soup.select('form input[name="identifier"]'):
        form = identifier_input.find_parent("form")
        question_input = form.select_one('input[name="question"]')
        answer_input = form.select_one('input[name="answer"]')
        if question_input is None or answer_input is None:
            raise RuntimeError(f"Malformed secret form for creator {creator}")
        recovered.append(
            {
                "creator": creator,
                "identifier": identifier_input.get("value", ""),
                "question": question_input.get("value", ""),
                "answer": answer_input.get("value", ""),
            }
        )
    return recovered


def main():
    parser = argparse.ArgumentParser(
        description="Recover unsaved secrets from a still-running homepage instance."
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("RECOVERY_BASE_URL", "http://127.0.0.1:5000"),
        help="URL of the running instance (default: %(default)s)",
    )
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/lists/secrets.recovered.json"),
    )
    args = parser.parse_args()

    if args.output.exists():
        parser.error(f"refusing to overwrite existing file: {args.output}")

    recovered = []
    skipped = []
    keys = list(user_keys(args.data_dir))
    with requests.Session() as session:
        for position, key in enumerate(keys, start=1):
            url = f"{args.base_url.rstrip('/')}/scrts/{quote(key, safe='')}"
            response = session.get(url, timeout=15, allow_redirects=False)
            response.raise_for_status()
            if response.is_redirect:
                destination = response.headers.get("Location", "unknown destination")
                skipped.append(key)
                print(
                    f"[{position}/{len(keys)}] skipped {key}: "
                    f"redirected to {destination}"
                )
                continue
            secrets = secrets_from_page(response.text, key)
            recovered.extend(secrets)
            print(f"[{position}/{len(keys)}] recovered {len(secrets)} for {key}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(
        json.dumps(recovered, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(args.output)
    print(
        f"Recovered {len(recovered)} secrets to {args.output}; "
        f"skipped {len(skipped)} redirected users"
    )


if __name__ == "__main__":
    main()
