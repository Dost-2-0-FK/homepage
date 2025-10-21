import csv
import io
import os
from typing import List
import requests
from dotenv import load_dotenv

load_dotenv()
BASE = os.getenv("SEAFILE_BASE").rstrip("/")
REPO  = os.getenv("SEAFILE_REPO_ID")
USERNAME = os.getenv("SEAFILE_USER")  # path inside the repo
PASSWORD = os.getenv("SEAFILE_PASS")  # path inside the repo

class SeafBytes: 
    def __init__(self, data: bytes) -> None:
        self.bytes = data

    @classmethod 
    def from_csv(cls, rows): 
        out = io.StringIO()
        w = csv.writer(out, lineterminator="\n")
        w.writerows(rows)
        return cls(out.getvalue().encode("utf-8"))

    def csv(self) -> List[List[str]]:
        text = self.bytes.decode("utf-8", errors="replace")
        return list(csv.reader(io.StringIO(text)))


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

    def download_data(self, file_path: str) -> SeafBytes: 
        file_path = file_path if file_path.startswith("/") else "/" + file_path
        # 1) get download link (string)
        r = requests.get(
            f"{BASE}/api2/repos/{REPO}/file/", 
            headers=self.headers, 
            params={"p": file_path}
        )
        r.raise_for_status()
        dl = r.text.strip().strip('"')
        # 2) download actual bytes (no auth header needed)
        r2 = requests.get(dl)
        r2.raise_for_status() 
        return SeafBytes(r2.content)

    def upload_data(
        self, data: bytes, path: str, replace: bool = True
    ):
        target_dir, filename = os.path.split(path)
        target_dir = target_dir if target_dir.startswith("/") else "/" + target_dir
        self.__ensure_dir(target_dir)

        upload_url = self.get_upload_link(target_dir)

        files = {"file": (filename, io.BytesIO(data), "text/csv")}
        payload = { "parent_dir": target_dir, "replace": "1" if replace else "0" }
        r = requests.post(
            upload_url, headers=self.headers, data=payload, files=files, timeout=30
        )
        try: 
            r.raise_for_status()
        except requests.HTTPError: 
            print("upload error: ", r.status_code, r.text) 
            raise

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
    seaf = Seafile(True) 
    ok = seaf.upload_csv("data/anmeldungen.csv", "/Orga/Anmeldungen")
    print("Uploaded:", ok)
