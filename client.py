from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QInputDialog, QScrollArea
)
from PyQt5.QtCore import Qt, QPoint, QTimer
import sys
import os
import threading
import time
from Scanner import HoneyPotScanner
from HoneyPot import HoneyPot
import datetime

class Client(QMainWindow):

    class Page1(QWidget):
        def __init__(self, update_files_func):
            super().__init__()
            self.update_files_func = update_files_func  # Store the update_files_func as an attribute

            layout = QVBoxLayout()

            self.files_layout = QVBoxLayout()
            layout.addLayout(self.files_layout)

            self.setLayout(layout)
            self.update_files_func(self.files_layout)  # Initialize the files layout

    class Page2(QWidget):
        def __init__(self):
            super().__init__()

            # Main layout for Page2
            self.main_layout = QVBoxLayout(self)
            self.main_layout.setContentsMargins(0, 0, 0, 0)

            # Scroll area for events
            self.scroll_area = QScrollArea()
            self.scroll_area.setWidgetResizable(True)
            self.scroll_area.setStyleSheet("background-color: black; border: none;")

            # Container widget for scrollable content
            self.scroll_widget = QWidget()
            self.scroll_layout = QVBoxLayout(self.scroll_widget)
            self.scroll_layout.setContentsMargins(0, 0, 0, 0)
            self.scroll_area.setWidget(self.scroll_widget)

            # Add the scroll area to the main layout
            self.main_layout.addWidget(self.scroll_area)

        def update_events(self, events, mark_as_handled_callback):
            # Clear the layout
            while self.scroll_layout.count():
                child = self.scroll_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            # Add each event as a colored box
            for file_path, event_data in events.items():
                event = event_data["event"]
                handled = event_data["handled"]

                event_widget = QWidget()
                event_layout = QHBoxLayout(event_widget)
                event_layout.setContentsMargins(0, 0, 0, 0)

                # Set the color based on whether the event is handled
                color = "green" if handled else "red"
                event_widget.setStyleSheet(f"background-color: {color}; border: 1px solid black;")
                event_widget.setFixedHeight(40)

                # Add event label
                event_label = QLabel(f"Event: {event.file_path}")
                event_label.setStyleSheet("color: white; padding: 5px;")
                event_layout.addWidget(event_label)

                # Add "Mark as Handled" button if the event is not handled
                if not handled:
                    mark_button = QPushButton("Mark as Handled")
                    mark_button.setStyleSheet("background-color: orange; color: white; border: none; padding: 5px;")
                    mark_button.clicked.connect(lambda _, e=event: mark_as_handled_callback(e))
                    event_layout.addWidget(mark_button)

                self.scroll_layout.addWidget(event_widget)

            # Add stretch to push content to the top
            self.scroll_layout.addStretch()

    def __init__(self):
        super().__init__()

        self.honeypot_files = []
        self.events = {}  # Dictionary to store events
        self.scanner_thread = None  # Thread for background scanning
        self.scanner_running = False  # Flag to control the scanner thread

        # Remove native window frame
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setGeometry(100, 100, 700, 600)

        # Main wrapper widget
        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_widget.setStyleSheet("background-color: black;")
        self.setCentralWidget(self.main_widget)

        # Custom header
        self.header = QWidget()
        self.header.setFixedHeight(40)
        self.header.setStyleSheet("background-color: black;")
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(10, 0, 10, 0)

        title = QLabel("HoneyPot Client")
        title.setStyleSheet("color: white; font-size: 16px;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Add "Switch Page" button to the header
        self.switch_button = QPushButton("Switch Page")
        self.switch_button.setStyleSheet(
            "background-color: blue; color: white; border: none; padding: 5px; font-size: 12px;"
        )
        self.switch_button.setFixedSize(100, 30)
        self.switch_button.clicked.connect(self.toggle_page)
        header_layout.addWidget(self.switch_button)

        # Add close button to the header
        close_button = QPushButton("X")
        close_button.setStyleSheet(
            "background-color: red; color: white; border: none; padding: 5px;"
        )
        close_button.setFixedSize(30, 30)
        close_button.clicked.connect(self.close)
        header_layout.addWidget(close_button)

        self.main_layout.addWidget(self.header)

        # Placeholder for central page widget
        self.page_container = QWidget()
        self.page_layout = QVBoxLayout(self.page_container)
        self.page_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.page_container)

        # Pages
        self.page1 = self.Page1(self.update_honeypot_files)
        self.page2 = self.Page2()

        self.current_page = 1
        self.show_page1()

        # Start the scanner in a background thread
        self.start_scanner()

    def toggle_page(self):
        if self.current_page == 1:
            self.show_page2()
            self.current_page = 2
        else:
            self.show_page1()
            self.current_page = 1

    def show_page1(self):
        self.clear_page_container()
        self.page_layout.addWidget(self.page1)

    def show_page2(self):
        self.clear_page_container()
        self.page_layout.addWidget(self.page2)
        self.page2.update_events(self.events, self.mark_as_handled)  # Pass the callback to Page2

    def clear_page_container(self):
        for i in reversed(range(self.page_layout.count())):
            widget = self.page_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

    def update_honeypot_files(self, files_layout):
        # Clear the layout safely
        while files_layout.count():
            child = files_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Add each honeypot file
        for honeypot in self.honeypot_files:
            file_widget = QWidget()
            file_layout = QHBoxLayout(file_widget)
            file_layout.setContentsMargins(0, 0, 0, 0)

            # Use honeypot.file_path for QLabel
            file_label = QLabel(honeypot.file_path)
            file_label.setStyleSheet("color: white;")
            file_layout.addWidget(file_label)

            delete_button = QPushButton("Delete")
            delete_button.setStyleSheet("background-color: red; color: white; border: none; padding: 2px;")
            delete_button.clicked.connect(lambda _, f=honeypot: self.delete_file(f))
            file_layout.addWidget(delete_button)

            edit_button = QPushButton("Edit")
            edit_button.setStyleSheet("background-color: orange; color: white; border: none; padding: 2px;")
            edit_button.clicked.connect(lambda _, f=honeypot: self.edit_file(f))
            file_layout.addWidget(edit_button)

            files_layout.addWidget(file_widget)

        # Add the "Add File" button at the end
        add_button = QPushButton("+ Add File")
        add_button.setStyleSheet(
            "background-color: green; color: white; font-size: 18px; padding: 10px; border: none;"
        )
        add_button.clicked.connect(self.add_new_file)
        files_layout.addWidget(add_button, alignment=Qt.AlignCenter)

    def delete_file(self, file):
        if file in self.honeypot_files:
            os.remove(file.file_path)
            self.honeypot_files.remove(file)
            self.update_honeypot_files(self.page1.files_layout)

    def edit_file(self, file):
        print(f"Edit file: {file.file_path}")  # Replace with actual edit logic

    def add_new_file(self):
        # Open an input dialog to get the new filename
        new_file_name, ok = QInputDialog.getText(self, "Add New File", "Enter the file path:")
        if ok and new_file_name.strip():  # Check if the user pressed OK and entered a valid filename
            file_path = new_file_name.strip()
            file_path = new_file_name.strip()
            try:
                # Create the file
                with open(file_path, 'w') as f:
                    f.write("")  # Create an empty file

                # Add the file to the honeypot
                new_honeypot = HoneyPot(file_path=file_path)
                new_honeypot.add_file(file_path)
                self.honeypot_files.append(new_honeypot)
                self.update_honeypot_files(self.page1.files_layout)
            except Exception as e:
                print(f"Error creating file {file_path}: {e}")

    def scan_files(self, scanner: HoneyPotScanner):
        scanner.keep_scanning()

    def start_scanner(self):
        """Start the scanner in a background thread."""
        self.scanner_running = True
        self.scanner_thread = threading.Thread(target=self.run_scanner, daemon=True)
        self.scanner_thread.start()

    def run_scanner(self):
        """Run the scanner and update events."""
        scanner = HoneyPotScanner(self.honeypot_files)
        while self.scanner_running:
            scanner.scanner()  # Perform the scanning
            for file_path, event in scanner.events.items():
                if file_path not in self.events:
                    # Add new event
                    self.events[file_path] = {"event": event, "handled": False}
                    print(f"New event detected: {event.details}")  # Debugging output
                elif self.events[file_path]["handled"]:
                    # Check if the file has been accessed again
                    last_accessed = event.timestamp
                    honeypot = next((h for h in self.honeypot_files if h.file_path == file_path), None)
                    if honeypot and last_accessed > honeypot.when_added:
                        # Reset the "handled" status for the file
                        self.events[file_path]["handled"] = False
                        print(f"File '{file_path}' accessed again. Resetting handled status.")
    
            # Update the GUI in the main thread
            QTimer.singleShot(0, lambda: self.page2.update_events(self.events, self.mark_as_handled))
    
            time.sleep(5)  # Avoid busy waiting

    def mark_as_handled(self, event):
        # Mark the event as handled
        for file_path, event_data in self.events.items():
            if event_data["event"] == event:
                self.events[file_path]["handled"] = True
                print(f"Event '{file_path}' marked as handled.")  # Debugging output

                # Update the last accessed time
                for honeypot in self.honeypot_files:
                    if honeypot.file_path == file_path:
                        honeypot.when_added = datetime.datetime.now()

                # Refresh Page 2 to reflect the changes
                self.page2.update_events(self.events, self.mark_as_handled)
                break

    def closeEvent(self, event):
        """Stop the scanner thread when the application is closed."""
        self.scanner_running = False
        if self.scanner_thread:
            self.scanner_thread.join()
        super().closeEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.old_pos = None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Client()
    window.show()
    sys.exit(app.exec_())