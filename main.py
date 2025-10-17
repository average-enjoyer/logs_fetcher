from typing_extensions import Self
from dateutil import parser as date_parser
from textual.app import App, ComposeResult
from textual.containers import Grid
from textual.widgets import Footer, Header, Static, Label, Input, Switch, Button

from datetime import datetime


dates = [
    "2024-10-09 15:30:45",
    "Oct 9, 2024 3:30 PM", 
    "09/10/2024 15:30:45",
    "2024-10-09T15:30:45.123Z"
]

class SSHSettings(Static):
    def compose(self) -> ComposeResult:
        yield Label("SSH Settings")
        yield Label("Copy from localhost:", id="copy_from_localhost_label")
        yield Switch(id="copy_from_localhost", value=False, animate=True)
        yield Input(placeholder="Host IP", id="host_ip", valid_empty=False)
        yield Input(placeholder="Username", id="username", valid_empty=False)
        yield Input(placeholder="Password", password=True, id="password", valid_empty=False)


class LogsFetcher(App):
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ]

    CSS_PATH = "logs_fetcher.tcss"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        with Grid(id="main-container"):
            with Grid(id="dates", classes="panel"):
                yield Label("From date:", id="from_date_label")
                yield Input(placeholder="2025-11-27 15:30", classes="datetime_input", valid_empty=False)
                yield Label("To date:", id="to_date_label")
                yield Input(placeholder="2025-11-27 18:30", classes="datetime_input", valid_empty=False)
                yield Label("Slow mode:", id="slow_mode_label")
                yield Switch(id="slow_mode", value=False, animate=True)
                yield Label("Directories with logs", id="log_dirs_label")
                yield Input("/var/log/messages", id="log_dirs")
                yield Button("Add path", id="add_path_btn", variant="success")
            yield SSHSettings(id="ssh_settings", classes="panel")
            yield Button("COPY", id="copy_btn", variant="primary")

    def toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )


if __name__ == "__main__":
    app = LogsFetcher()
    app.run()

