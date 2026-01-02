import os
import datetime

class LogManager:
    def __init__(self, log_file):
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        self.log_file = log_file

    def log(self, message):
        timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        with open(self.log_file, "a") as file:
            file.write(f"{timestamp} {message}\n")
        print(f"{timestamp} {message}")
