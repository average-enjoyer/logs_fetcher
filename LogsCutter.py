import os
import re
from dateutil import parser as date_parser
import logging # debug level is set in main.py


# Example date strings to parse
dates = [
    "2024-10-09 15:30:45",
    "Oct 9, 2024 3:30 PM", 
    "09/10/2024 15:30:45",
    "2024-10-09T15:30:45.123Z",
    "2024-10-09 15:30:45.123Z"
]


class LogsCutter():
    """A class to handle log cutting based on date ranges."""

    def __init__(self, from_date: str, to_date: str, log_files: list[str], dest_path: str):
        self.from_date = date_parser.parse(from_date)
        self.to_date = date_parser.parse(to_date)
        self.log_files = log_files
        self.dest_path = dest_path
        self.logger = logging.getLogger("LogsCutter")
        self.logger.debug(f"Initialized LogsCutter with from_date: {self.from_date} and to_date: {self.to_date}")

    def cut_logs(self):
        self.logger.debug("Starting to cut logs...")
        self.logger.debug(f"From date: {self.from_date}, To date: {self.to_date}")
        self.logger.debug(f"Log files: {self.log_files}")
        for log in self.log_files:
            if os.path.exists(log):
                if os.path.isdir(log):
                    self.logger.debug(f"Processing log directory: {log}")
                    for logfile in os.listdir(log):
                        log_path = os.path.join(log, logfile)
                        if os.path.isfile(log_path):
                            self.logger.debug(f"Processing log file: {log_path}")
                            self.cut_log_file(log_path)
                elif os.path.isfile(log):
                    self.logger.debug(f"Processing a single log file: {log}")
                    self.cut_log_file(log)
            else:
                self.logger.error(f"Log file or directory does not exist: {log}")

    def cut_log_file(self, log_file_path:str):
        with open(log_file_path, "r") as log_file:
            lines = log_file.readlines()

