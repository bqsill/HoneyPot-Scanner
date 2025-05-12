
class Event():
    def __init__(self, file_name, timestamp, details, uuid):
        self.file_path = file_name
        self.timestamp = timestamp
        self.has_been_caught = False
        self.details = details
        self.uuid = uuid
        