import os
import time
from abc import ABC, abstractmethod
from typing import List
import bot_tools

class FileSubject:
    def __init__(self, filename: str):
        self.filename = filename
        self.observers: List[FileObserver] = []
        self.last_modified = self._get_last_modified()

    def attach(self, observer: 'FileObserver') -> None:
        self.observers.append(observer)

    def detach(self, observer: 'FileObserver') -> None:
        self.observers.remove(observer)

    def notify(self) -> None:
        for observer in self.observers:
            observer.update(self.filename)

    def _get_last_modified(self) -> float:
        return os.path.getmtime(self.filename)

    def check_file(self) -> None:
        current_modified = self._get_last_modified()
        if current_modified != self.last_modified:
            self.last_modified = current_modified
            self.notify()

class FileObserver(ABC):
    @abstractmethod
    def update(self, filename: str) -> None:
        pass

class LoggingObserver(FileObserver):
    def __init__(self, log_file: str):
        self.log_file = log_file

    def update(self, filename: str) -> None:
        log_message = f"File '{filename}' was modified at {time.ctime()}\n"
        bot_tools.append(self.log_file, log_message)
        print(f"Logged change to {self.log_file}")

class BackupObserver(FileObserver):
    def update(self, filename: str) -> None:
        backup_filename = f"{filename}.backup"
        with open(filename, 'r') as original_file:
            content = original_file.read()
        bot_tools.rewrite(backup_filename, content)
        print(f"Created backup: {backup_filename}")

class NotificationObserver(FileObserver):
    def update(self, filename: str) -> None:
        print(f"NOTIFICATION: File '{filename}' has been modified!")

# Demo
def run_demo():
    # Create the observed file if it doesn't exist
    observed_file = 'observed_file.txt'
    if not os.path.exists(observed_file):
        bot_tools.rewrite(observed_file, "Initial content")

    # Create FileSubject
    file_subject = FileSubject(observed_file)

    # Create observers
    logging_observer = LoggingObserver('file_changes.log')
    backup_observer = BackupObserver()
    notification_observer = NotificationObserver()

    # Attach observers
    file_subject.attach(logging_observer)
    file_subject.attach(backup_observer)
    file_subject.attach(notification_observer)

    print("File monitoring started. Press Ctrl+C to exit.")
    try:
        while True:
            file_subject.check_file()
            time.sleep(1)  # Check every second
    except KeyboardInterrupt:
        print("\nFile monitoring stopped.")

    # Clean up demo files
    os.remove(observed_file)
    os.remove('file_changes.log')
    os.remove(f"{observed_file}.backup")

if __name__ == "__main__":
    run_demo()

# To demonstrate file changes, use the following code in a separate Python session:
# import bot_tools
# bot_tools.append('observed_file.txt', "\nNew content added!")