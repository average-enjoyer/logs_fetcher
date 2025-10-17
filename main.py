from typing_extensions import Self
from dateutil import parser as date_parser
from textual.app import App, ComposeResult
from textual.containers import Grid, Container, VerticalScroll
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
        yield Label("Copy from localhost:", id="copy_from_localhost_label")
        yield Switch(id="copy_from_localhost", value=False, animate=True)
        with Container(id="ssh_inputs_container"):
            yield Label("SSH Settings")
            yield Input(placeholder="Host IP", id="host_ip", valid_empty=False)
            yield Input(placeholder="Username", id="username", valid_empty=False)
            yield Input(placeholder="Password", password=True, id="password", valid_empty=False)

class PathField(Static):
    def compose(self) -> ComposeResult:
        yield Input("/var/log/messages", id="log_dirs")

class LogsFetcher(App):
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("a", "add_path", "Add path"),
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
                yield VerticalScroll(PathField(), id="path_fields")
                yield Button("Add path", id="add_path", variant="success")
            yield SSHSettings(id="ssh_settings", classes="panel")
            yield Button("COPY", id="copy_btn", variant="primary")

    def action_add_path(self) -> None:
        """An action to add a path."""
        new_path = PathField()
        self.query_one("#path_fields").mount(new_path)
        new_path.scroll_visible()

    def action_copy(self) -> None:
        pass

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        if event.button.id == "add_path":
            self.action_add_path()
        if event.button.id == "copy_btn":
            self.action_copy()


if __name__ == "__main__":
    app = LogsFetcher()
    app.run()

