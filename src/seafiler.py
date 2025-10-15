import os
import requests
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
BASE = os.getenv("SEAFILE_BASE").rstrip("/")
REPO  = os.getenv("SEAFILE_REPO_ID")
USERNAME = os.getenv("SEAFILE_USER")  # path inside the repo
PASSWORD = os.getenv("SEAFILE_PASS")  # path inside the repo

class Seafile: 
    def __init__(self, use_seafile: bool): 
        self.use_seafile = use_seafile
        if not self.use_seafile:
            print("Skipping initializing seafile")
            return
        print("Initializing Seafile")
        self.token = self.__seafile_login()
        print("GOT TOKEN", self.token)
        self.headers = {"Authorization": f"Token {self.token}"} 

    def upload_csv(self, local_path: str, target_dir: str, replace: bool = True):
        target_dir = target_dir if target_dir.startswith("/") else "/" + target_dir
        self.__ensure_dir(target_dir)

        upload_url = self.get_upload_link(target_dir)
        filename = Path(local_path).name

        with open(local_path, "rb") as f:
            files = {"file": (filename, f, "text/csv")}
            data = {
                "parent_dir": target_dir,
                "replace": "1" if replace else "0",
                # "relative_path": ""  # optional
            }
            r = requests.post(upload_url, headers=self.headers, data=data, files=files, timeout=30)
            r.raise_for_status()
        return True

    def get_upload_link(self, target_dir: str) -> str:
        r = requests.get(
            f"{BASE}/api2/repos/{REPO}/upload-link/",
            headers=self.headers,
            params={"p": target_dir},
            timeout=15,
        )
        r.raise_for_status()
        # API returns a JSON string, sometimes quoted like "https://..."
        url = r.text.strip().strip('"')
        return url

    def __ensure_dir(self, path: str):
        """Create a directory in the repo if it doesn't exist."""
        # Check if exists
        r = requests.get(
            f"{BASE}/api2/repos/{REPO}/dir/", headers=self.headers, params={"p": path}
        )
        if r.status_code == 200:
            print("Dir exists")
            return
        # Create (mkdir)
        print("creating dir: ", r.status_code, r.url)
        r = requests.post(
            f"{BASE}/api2/repos/{REPO}/dir/",
            headers=self.headers,
            params={"p": path},
            data={"operation": "mkdir"},
            timeout=15,
        )
        r.raise_for_status()

    def __seafile_login(self): 
        r = requests.post(f"{BASE}/api2/auth-token/",
                          data={"username": USERNAME, "password": PASSWORD})
        r.raise_for_status()
        token = r.json()["token"]
        return token


if __name__ == "__main__":
    seaf = Seafile() 
    ok = seaf.upload_csv("data/anmeldungen.csv", "/Orga/Anmeldungen")
    print("Uploaded:", ok)
