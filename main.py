from dateutil import parser as date_parser
from textual.app import App, ComposeResult
from textual.widgets import Digits

from datetime import datetime


dates = [
    "2024-10-09 15:30:45",
    "Oct 9, 2024 3:30 PM", 
    "09/10/2024 15:30:45",
    "2024-10-09T15:30:45.123Z"
]
