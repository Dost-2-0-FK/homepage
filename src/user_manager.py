import csv
import json
import os
from threading import Lock
from typing import Dict

from src.seafiler import Seafile

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


class User: 
    def __init__(self, ujson: Dict[str, str]) -> None:
        self.key = ujson.get("key")
        self.email = ujson.get("email")
        self.name = ujson.get("name", "") 
        self.pdream = ujson.get("pdream", "") 
        self.ndream = ujson.get("ndream", "") 
        self.pnature = ujson.get("pnature", "") 
        self.nnature = ujson.get("nnature", "") 
        self.pspirit = ujson.get("pspirit", "") 
        self.nspirit = ujson.get("nspirit", "") 

    def update_field(self, field: str, value: str) -> None: 
        if field == "name": 
            self.name = value 
        if field == "pnature": 
            self.pnature = value 
        if field == "nnature": 
            self.nnature = value 
        if field == "pspirit": 
            self.pspirit = value 
        if field == "nspirit": 
            self.nspirit = value 
        if field == "pdream": 
            self.pdream = value 
        if field == "ndream": 
            self.ndream = value 

class UManager: 
    def __init__(self):
        self.CSV_PATH = "data/anmeldungen.csv"
        self.SEAF_CSV_DIR = "/Orga/Anmeldungen"
        self.mutex = Lock()
        self.csv = self.__read_from_csv() 
        self.seaf = Seafile(os.getenv("USE_SEAFILE", "False") == "True")

    def email_exists(self, email: str) -> bool: 
        with self.mutex: 
            for row in self.csv: 
                if row[1].strip().lower() == email.lower(): 
                    return True 
            return False 

    def key_exists(self, key: str) -> bool: 
        print("Checking path: ",self.__make_user_path(key))
        return os.path.exists(self.__make_user_path(key))

    def get_user(self, key: str) -> User | None: 
        if self.key_exists(key): 
            with open(self.__make_user_path(key), "r") as f: 
                return User(json.load(f)) 
        return None

    def save_user(self, user: User): 
        with open(self.__make_user_path(user.key), "w") as fp: 
            json.dump(vars(user), fp)
        # Update CSV fields: 
        with self.mutex: 
            changed = False
            for row in self.csv: 
                if row[1].strip().lower() == user.email.lower(): 
                    if row[2].strip() != user.name: 
                        row[2] = user.name 
                        changed = True
            if changed: 
                self.__write_csv()
                print("Saved CSV!")


    def add_user(self, email: str, key: str): 
        with self.mutex: 
            # Add E-Mail to User-CSV 
            self.csv.append([str(len(self.csv)), email, "", "", "", ""]) 
            self.__write_csv()
            # Create new User-Json 
            with open(self.__make_user_path(key), "w") as fp: 
                json.dump({"key": key, "email": email}, fp)

    # Function to write data to CSV
    def __write_csv(self):
        with open(self.CSV_PATH, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerows(self.csv)
        try:
            if self.seaf.use_seafile: 
                ok = self.seaf.upload_csv(self.CSV_PATH, self.SEAF_CSV_DIR)
                print("Uploaded:", ok)
            else: 
                print("Skipped seafile")
        except: 
            pass

    # Function to read data from CSV
    def __read_from_csv(self):
        with open(self.CSV_PATH, 'r') as csvfile:
            csv_reader = csv.reader(csvfile)
            data = list(csv_reader)
        return data

    def __make_user_path(self, key: str) -> str: 
        return f"data/{key}.json"
