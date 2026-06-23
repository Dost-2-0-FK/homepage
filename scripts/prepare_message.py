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
PATH_TO_POSTS_TEMPLATE = Path("resources/private_chats.json")

PATH_TO_PLEROMA_POSTS_JSON = Path("pleroma/chats.json")

def __tags(data: Dict[str, Any]) -> List[str]: 
    if "_tags" in data: 
        return data["_tags"] 
    return []

def prepare_posts(post_template, chars): 
    post = post_template.copy() 
    mentions = post_template["recipients"] 

    mentioned_usernames = []
    # Attributes 
    for attribute, pattern in mentions["attributes"]:
        regex = re.compile(pattern)
        for char, ctx in chars:
            attr_value = ctx.get("attributes", {}).get(attribute)
            if attr_value is not None and regex.fullmatch(attr_value):
                mentioned_usernames.append(ctx["attributes"]["username"])
    # Tags
    for tag in mentions["tags"]: 
        for (char, ctx) in chars: 
            if tag in __tags(char): 
                mentioned_usernames.append(ctx["attributes"]["username"]) 

    # Direct
    for account in mentions["accounts"]: 
        mentioned_usernames.append(account) 

    # Add mentions to mentions field 
    post["recipients"] = mentioned_usernames
    # Add mentions to text 
    post["text"] += " "
    for username in mentioned_usernames: 
        post["text"] += "@" 
        post["text"] += username
        post["text"] += " " 

    # Update path to absolute path 
    for i, media in enumerate(post["media"]): 
        post["media"][i]["path"] = os.path.abspath(media["path"])

    return post.copy()


if __name__ == "__main__": 
    # Load all Chars (for tags) and matching Contexts first
    chars = []
    for file in PATH_TO_DOST_CHARS.glob("*.json"):
        char = None 
        ctx = None 
        with open(file, "r") as f:
            char = json.load(f)
        with open(PATH_TO_TXTAD_CHARS.joinpath(f"{char['key']}.ctx"), 'r') as f:
            ctx = json.load(f)
        if char and ctx: 
            chars.append((char, ctx))

    # Open template for posts
    posts = []
    post_templates = None
    with open(PATH_TO_POSTS_TEMPLATE, 'r') as f:
        post_templates = json.load(f) 

    for i, post_template in enumerate(post_templates): 
        if post_template["posted"] == True: 
            continue
        else:
            posts.append(prepare_posts(post_template, chars))
            post_templates[i]["posted"] = True

    # Store posted
    with open(PATH_TO_POSTS_TEMPLATE, 'w') as f:
        json.dump(post_templates, f) 

    
    # Store prepared posts
    with open(PATH_TO_PLEROMA_POSTS_JSON, 'w') as f:
        json.dump(posts, f)
