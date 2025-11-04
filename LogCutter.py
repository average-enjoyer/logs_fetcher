import os
import re
from dateutil import parser as date_parser
from dateutil.parser import ParserError
import logging # debug level is set in main.py


# Example date strings to parse
dates = [
    "2025-10-09 15:30:45",
    "Oct 9, 2025 3:30 PM",
    "09/10/2025 15:30:45",
    "2025-10-09T15:30:45.123Z",
    "2025-10-09 15:30:45.123Z"
]


class LogCutter():
    """A class to handle log cutting based on date ranges."""

    def __init__(self, from_date: str, to_date: str, dest_path: str):
        self.from_date = date_parser.parse(from_date, ignoretz=True)
        self.to_date = date_parser.parse(to_date, ignoretz=True)
        self.dest_path = dest_path
        self.logger = logging.getLogger("LogCutter")
        self.logger.debug(f"Initialized LogCutter with from_date: {self.from_date} and to_date: {self.to_date}")

    def cut_log(self, log_file_path:str, lines:list[str]) -> None:
        start_line_posix = 0.0 # POSIX timestamp of the first line to include
        end_line_posix = 0.0 # POSIX timestamp of the last line to include
        start_line_posix = self.find_start_line(lines)
        end_line_posix = self.find_end_line(lines)
        if start_line_posix is not None and end_line_posix is not None:
            self.logger.debug(f"Cutting log file from line {start_line_posix} to {end_line_posix}")
            if end_line_posix < start_line_posix:
                self.logger.warning(f"End line {end_line_posix} is before start line {start_line_posix} in file {log_file_path}. Skipping cut.")
                return
            elif start_line_posix == end_line_posix:
                self.logger.warning(f"Start and end lines are the same ({start_line_posix}) in file {log_file_path}. Skipping cut.\n"
                "It just means no logs found in the specified date range.\n")
                return
            elif end_line_posix == 0:
                self.logger.error(f"End line not found in file {log_file_path}. Skipping cut.")
                return
            cut_lines = lines[start_line_posix:end_line_posix]
            dest_file_path = os.path.join(self.dest_path, os.path.basename(log_file_path))
            try:
                if not os.path.exists(self.dest_path):
                    os.makedirs(self.dest_path, exist_ok=True)
            except OSError as e:
                    self.logger.error(f"Error creating destination directory {self.dest_path}: {e}")
            try:
                with open(dest_file_path, "w") as dest_file:
                    dest_file.writelines(cut_lines)
            except OSError as e:
                self.logger.error(f"Error writing to destination file {dest_file_path}: {e}")
            self.logger.info(f"Cut log saved to: {dest_file_path}")
        elif start_line_posix is None:
            self.logger.warning(f"No start line found in log file: {log_file_path}")
        elif end_line_posix is None:
            self.logger.warning(f"No end line found in log file: {log_file_path}")

    def extract_date_from_line(self, line: str):
        """Extract a date from a log line and convert it to a POSIX timestamp.

        This method searches for common date patterns in a log line using regex patterns
        and parses the first matching date string into a POSIX timestamp.

        Args:
            line (str): A single line from a log file that may contain a date.

        Returns:
            float: POSIX timestamp of the extracted date, or None if no valid date is found.

        Supported date formats:
            - ISO 8601: "2025-10-09 15:30:45", "2025-10-09 15:30:45.123Z"
            - Human readable: "Oct 9, 2025 3:30 PM"
            - Date/time: "09/10/2025 15:30:45"
            - ISO 8601 with T: "2025-10-09T15:30:45.123Z"
        """
        # date_patterns may require adding ^ to match at the start of the line only
        date_patterns = [
            r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d+)?Z?",  # 2025-10-09 15:30:45 or with milliseconds and Z
            r"[A-Za-z]{3} \d{1,2}, \d{4} \d{1,2}:\d{2} [AP]M",   # Oct 9, 2025 3:30 PM
            r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}",              # 09/10/2025 15:30:45
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?"   # 2025-10-09T15:30:45.123Z
        ]
        for pattern in date_patterns:
            match = re.search(pattern, line)
            if match:
                date_str = match.group(0)
                try:
                    parsed_date = date_parser.parse(date_str, ignoretz=True)
                    posix_timestamp = parsed_date.timestamp()
                    logging.debug(f"Extracted date '{date_str}' as POSIX timestamp: {posix_timestamp}")
                    return posix_timestamp
                except (ValueError, OverflowError, ParserError) as e:
                    self.logger.error(f"Error parsing date string '{date_str}': {e}")
        return None

    # find_start_line and find_end_line are practically identical; consider refactoring with optimization
    def find_start_line(self, lines: list[str]) -> int:
        """Find the first line in the log that matches or exceeds the from_date.

        Iterates through log lines sequentially and returns the number of the first line whose
        timestamp is greater than or equal to the configured from_date.

        Args:
            lines (list[str]): List of log lines to search through.

        Returns:
            int: The line number of the first line that matches the date criteria, or None if no matching line is found.
        """
        for line in lines:
            date_in_line = self.extract_date_from_line(line) # returns POSIX timestamp or None
            if date_in_line:
                if date_in_line >= self.from_date.timestamp():
                    self.logger.debug(f"Found start line: {line.strip()}")
                    return lines.index(line)

    def find_end_line(self, lines: list[str]) -> int:
        """Find the first line in the log that matches or exceeds the to_date.

        Iterates through log lines sequentially and returns the number of the first line whose
        timestamp is greater than or equal to the configured to_date.

        Args:
            lines (list[str]): List of log lines to search through.

        Returns:
            int: The line number of the first line that matches the date criteria, or None if no matching line is found.
        """
        line_number = 0
        for line in lines:
            date_in_line = self.extract_date_from_line(line) # returns POSIX timestamp or None
            if date_in_line:
                if date_in_line >= self.to_date.timestamp():
                    self.logger.debug(f"Found end line: {line.strip()}")
                    line_number = lines.index(line)
                    break
        # If no end line found, return the last line number. So, we include all lines till the end.
        if line_number > 0:
            return line_number
        else:
            return len(lines)
