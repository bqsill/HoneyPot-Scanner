from HoneyPot import HoneyPot
from detect import Detect
import threading
import time
import queue
from event import Event

class HoneyPotScanner():
    def __init__(self, file_paths):
        self.d = Detect()
        self.file_paths = file_paths
        self.events = {}  # Dictionary to store events
        self.event_queue = queue.Queue()  # Optional: Keep the queue for other uses

    def add_to_path(self, honey_path: HoneyPot):
        self.file_paths.append(honey_path)

    def scanner(self):
        running_threads = []
        for file in self.file_paths:
            # Pass the entire file object (HoneyPot or MockHoneyPot) to the thread
            thread = threading.Thread(target=self.process_file, args=(file,))
            thread.start()
            running_threads.append(thread)  # Append the thread object
        for thread in running_threads:
            thread.join()

    def process_file(self, file: HoneyPot):
        # Call check_if_accessed and store the result in the dictionary if an event is returned
        event = self.d.check_if_accessed(file)
        if event:
            # Add the event to the dictionary
            self.events[file.file_path] = event
            print(f"Event detected for file: {file.file_path}")  # Debugging output

            # Optionally, put the event in the queue for further processing
            self.event_queue.put(event)

    def keep_scanning(self):
        while True:
            self.scanner()
            # Add a sleep time to avoid busy waiting
            time.sleep(5)