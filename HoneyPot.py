import subprocess
import re
from datetime import datetime

class HoneyPot:
    def __init__(self, file_path: str = None, when_added: datetime = None):
        self.file_path = file_path
        self.when_added = when_added or datetime.now()

    def add_file(self, path: str):
        self.file_path = path
        self.when_added = datetime.now()

        # Quote the file path to handle spaces or special characters
        quoted_path = f'"{path}"'
        pattern = r"(\d{4})-(\d{2})-(\d{2})\s{2}(\d{2}:\d{2}\s[AP]M)"
        try:
            output = subprocess.check_output(f'dir {quoted_path}', shell=True, text=True)
            match = re.search(pattern, output)
            if match:
                print(f"File {path} added successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error adding file {path}: {e}")
