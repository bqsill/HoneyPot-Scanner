import socket
import os 
import subprocess
import re
from datetime import datetime
from HoneyPot import HoneyPot
from event import Event
import uuid

class Detect:
    def __init__(self):
        self.unhandled_events = {}

    def show_last_accessed(self, honey_path: HoneyPot):
        output = subprocess.check_output(f'dir /TA {honey_path.file_path}', shell=True, text=True)
        # Adjust the regex to match the format YYYY-MM-DD  HH:MM AM/PM
        pattern = r"(\d{4})-(\d{2})-(\d{2})\s{2}(\d{2}:\d{2}\s[AP]M)"
        match = re.search(pattern, output)
        if match:
            # Combine the matched groups into a single string
            date_time_str = f"{match.group(1)}-{match.group(2)}-{match.group(3)} {match.group(4)}"
            # Convert the string to a datetime object
            return datetime.strptime(date_time_str, "%Y-%m-%d %I:%M %p")
        return None

    def check_if_accessed(self, honey_path):
        if not isinstance(honey_path, HoneyPot):
            raise TypeError("honey_path must be an instance of HoneyPot")

        last_accessed = self.show_last_accessed(honey_path)
        if last_accessed:
            if last_accessed > honey_path.when_added and last_accessed not in self.unhandled_events:
                self.unhandled_events[last_accessed] = honey_path.file_path
                new_event = Event(file_name=honey_path.file_path,timestamp=last_accessed,details=f"File {honey_path.file_path} was accessed at {last_accessed}.",uuid=str(uuid.uuid4()))
                return new_event
        return None




