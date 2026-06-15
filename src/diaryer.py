import copy
import dataclasses
import json
import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

DIARY_PATH = "data/diaries"
DIARY_CONFIG_PATH = "resources/diary-config.json"

class ParseError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)

@dataclass 
class Message: 
    name: str 
    message: str 

@dataclass 
class Chat: 
    messages: list[Message] = field(default_factory=list)
    people: list[str] = field(default_factory=list)

@dataclass 
class DiaryEntry: 
    date: str 
    entry: str
    chats: list

@dataclass 
class Diary: 
    key: str 
    name: str 
    entries: List[DiaryEntry] = field(default_factory=list)

class Diaryer: 
    def __init__(self, comm, umanager, secrator: Secrator):
        if not os.path.exists(DIARY_PATH):
            os.makedirs(DIARY_PATH)
        self.config = self.__load_data(DIARY_CONFIG_PATH)
        self.diaries = self.__load_diaries()
        self.comm = comm 
        self.umanager = umanager
        self.secrator = secrator

    def get_diaries(self, key: str) -> List[Diary]: 
        diaries = [] 
        for diary in self.diaries: 
            # Find corresponding secret-file entry to get creator
            file = self.secrator.secret_file.get(diary.key)
            if file is not None:
                # compare creator to current user
                if key == file._creator: 
                    diaries.append(diary) 
        return diaries

    def get_diary(self, char_key: str) -> Diary: 
        for diary in self.diaries: 
            print("comparing: ", char_key, diary.key)
            if diary.key == char_key: 
                return diary 
        return None

    def find_diary_entry_by_date(self, date: str, diary: Diary) -> Optional[Diary]:
        return next((e for e in diary.entries if e.date == date), None)

    def parse_diary(self, text: str) -> str:
        lines = text.split("\n")
        name, lines = self.parse_name(lines)
        if not name: 
            raise ParseError(
                f"Leading character-name tag (<i>[Sirname, Name]</i>) not found!"
            )
        key = self.secrator.get_entry_key_by_name(name)
        if not key: 
            raise ParseError(
                f"Character name \"{name}\" does not match any secret-file entries!"
            )

        diary = Diary(key, name)

        def is_date(line: str) -> bool: 
            pattern = r'^\[\d{4}[-.]\d{2}[-.]\d{2}\]$'
            return bool(re.match(pattern, line))

        cur = None
        for i, line in enumerate(lines): 
            if is_date(line.strip()): 
                if cur == None: 
                    print(f" - found first date after {i} lines")
                    cur = []
                else: 
                    print(f" - created entry after {i} lines")
                    diary.entries.append(self.parse_diary_entry(cur))
                cur = [line]
            # Don't add, if first line not found yet
            elif cur != None: 
                cur.append(line)
                            
        # Parse last entry from remaining lines)
        if cur != []: 
            diary.entries.append(self.parse_diary_entry(cur))
       
        print(f"For: {name} got {len(diary.entries)}")
        self.run_config(copy.deepcopy(diary))
        self.__save_diary(diary)
        self.__replace_or_add_diary(diary)
        return diary.name

    def parse_name(self, lines: List[str]) -> Tuple[str, List[str]]: 
        """ FORMAT "[Sirname, Name]" """
        def matches(line: str) -> bool: 
            return line[0] == "[" and line[-1] == "]" and "," in line

        for i, line in enumerate(lines): 
            if len(line) > 3 and matches(line.strip()): 
                return line.strip()[1:-1], lines[i+1:]
        return None, None

    def parse_diary_entry(self, lines: List[str]) -> DiaryEntry: 
        date = lines[0].strip()[1:-1] 
        if "." in date: 
            date.replace(".", "-")
        entry = ""
        chats = []

        for i, line in enumerate(lines[1:]):
            # Chats come last, so break loop after [CHAT].
            if line.strip().lower() == "[CHAT]".lower(): 
                try:
                    chats = self.parse_chats(lines[i+1:]) 
                except ParseError as ex: 
                    raise ParseError(
                        f"Error: <b>{ex.message}</b>\n\nIn entry <b>{date}</b>: >>{'\n'.join(lines)}<< "
                    )
                break
            # Add all previous lines to diary entry
            else: 
                entry += line

        return DiaryEntry(date, entry, chats)

    def parse_chats(self, lines: List[str]) -> List[Chat]: 
        chats = []
        cur = []
        for i, line in enumerate(lines[1:]):
            if line.strip().lower() == "[CHAT]".lower(): 
                chats.append(self.parse_chat(cur)) 
                cur = [] 
            else: 
                cur.append(line)

        # Parse last chat from remaining lines 
        if cur != []: 
            chats.append(self.parse_chat(cur)) 
            
        return chats

    def parse_chat(self, lines: List[str]) -> Chat: 
        people = []
        messages = []
        cur_sender = ""
        cur_message = ""
        for line in lines: 
            l = line.strip()
            if len(l) > 0 and l[0] == "[" and ":]" in l: 
                if cur_sender != "" and cur_message != "": 
                    messages.append(Message(cur_sender, cur_message))
                cur_sender = l[1:l.find(":]")] 
                if self.secrator.get_entry_key_by_name(cur_sender) is None:
                    raise ParseError(
                        f"For CHAT character \"{cur_sender}\" not found!"
                    )
                if cur_sender not in people: 
                    people.append(cur_sender)
                cur_message = l[l.find(":]")+3:] 
            else: 
                cur_message += line 

        # Add last message from remaining lines: 
        if cur_sender != "" and cur_message != "": 
            messages.append(Message(cur_sender, cur_message)) 
        
        return Chat(messages, people)

    def run_config(self, diary: Diary) -> None: 
        if diary.name not in self.config: 
            print("run_config: Nothing to do...") 
            return
        executed = 0
        for date, actions in self.config[diary.name].items(): 
            entry = self.find_diary_entry_by_date(date, diary)
            if entry: 
                for action in actions: 
                    if action['cmd'] == "replace_hint": 
                        src = action["from"]
                        to = action["to"] 
                        if src not in entry.entry: 
                            raise ParseError(
                                f"run_config: for \"{diary.name}\" at \"{date}\" hint \"{src}\" not found!"
                            )
                        entry.entry.replace(src, to)
                        executed += 1 
            else: 
                raise ParseError(
                    f"run_config: for \"{diary.name}\" date \"{date}\" not found!"
                )

        print(f"run_config: Config executed {executed} on {diary.name}") 
        return diary

    def __replace_or_add_diary(self, new_diary: Diary): 
        for i, existing in enumerate(self.diaries):
            if existing.key == new_diary.key:
                self.diaries[i] = new_diary
                return True
        self.diaries.append(new_diary)

    def __save_diary(self, diary: Diary): 
        with open(f"{os.path.join(DIARY_PATH, diary.key)}.json", "w") as f: 
            json.dump(dataclasses.asdict(diary), f)

    def __load_diaries(self) -> List[Diary]: 
        """ Loads secret service files """
        diaries = []
        for filename in os.listdir(DIARY_PATH): 
            json_data = self.__load_data(os.path.join(DIARY_PATH, filename))
            diaries.append(Diary(**json_data))
        return diaries

    def __load_data(self, path: str):  
        with open(path, "r") as f: 
            data = json.load(f)
            return data
