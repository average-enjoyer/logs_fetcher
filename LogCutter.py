import os
import re
from dateutil import parser as date_parser
from dateutil.parser import ParserError
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

    def cut_log(self):
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
        start_line_posix = 0.0 # POSIX timestamp of the first line to include
        end_line_posix = 0.0 # POSIX timestamp of the last line to include
        with open(log_file_path, "r") as log_file:
            lines = log_file.readlines()
            start_line_posix = self.find_start_line(lines)
            end_line_posix = self.find_end_line(lines)

    def extract_date_from_line(self, line: str):
        # Regular expression to match various date formats
        # date_patterns may require adding ^ to match at the start of the line only
        date_patterns = [
            r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d+)?Z?",  # 2024-10-09 15:30:45 or with milliseconds and Z
            r"[A-Za-z]{3} \d{1,2}, \d{4} \d{1,2}:\d{2} [AP]M",   # Oct 9, 2024 3:30 PM
            r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}",              # 09/10/2024 15:30:45
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?"   # 2024-10-09T15:30:45.123Z
        ]
        for pattern in date_patterns:
            match = re.search(pattern, line)
            if match:
                date_str = match.group(0)
                try:
                    parsed_date = date_parser.parse(date_str)
                    posix_timestamp = parsed_date.timestamp()
                    logging.debug(f"Extracted date '{date_str}' as POSIX timestamp: {posix_timestamp}")
                    return posix_timestamp
                except (ValueError, OverflowError, ParserError) as e:
                    self.logger.error(f"Error parsing date string '{date_str}': {e}")
        return None

    # find_start_line and find_end_line are practically identical; consider refactoring with optimization
    def find_start_line(self, lines: list[str]) -> int:
        for line in lines:
            date_in_line = self.extract_date_from_line(line) # returns POSIX timestamp or None
            if date_in_line:
                if date_in_line >= self.from_date.timestamp():
                    self.logger.debug(f"Found start line: {line.strip()}")
                    return line

    def find_end_line(self, lines: list[str]) -> int:
        for line in lines:
            date_in_line = self.extract_date_from_line(line) # returns POSIX timestamp or None
            if date_in_line:
                if date_in_line >= self.to_date.timestamp():
                    self.logger.debug(f"Found end line: {line.strip()}")
                    return line
