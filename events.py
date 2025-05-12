import os 
import smtplib
from event import Event



class EventHandler():
    def __init__(self,email_addr: list):
        self.unhandled_events = {}
        self.smtp_server = 'smtp.gmail.com'
        self.smtp_port = 587
        self.email_addr = email_addr

    def event_handler(self, curr_event: Event): 
        pass

    

    
          