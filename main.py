import logging
import json
from Config import Config
from typing import cast
from dateutil import parser as date_parser
from datetime import datetime, timedelta
from textual.app import App, ComposeResult
from textual.containers import Grid, Container, VerticalScroll
from textual.widgets import Footer, Header, Static, Label, Input, Switch, Button

# Example date strings to parse
dates = [
    "2024-10-09 15:30:45",
    "Oct 9, 2024 3:30 PM", 
    "09/10/2024 15:30:45",
    "2024-10-09T15:30:45.123Z"
]


class SSHSettings(Static):
    configs = Config().configs
    def compose(self) -> ComposeResult:
        yield Label("Copy from localhost:", id="copy_from_localhost_label")
        yield Switch(id="copy_from_localhost", value=self.configs.get("copy_from_local", True), animate=True)

        with Container(id="ssh_inputs_container"):
            yield Label("SSH Settings")
            yield Input(placeholder="Host IP", id="host_ip", valid_empty=False)
            yield Input(placeholder="Username", id="username", valid_empty=False)
            yield Input(placeholder="Password", password=True, id="password", valid_empty=False)

    def on_mount(self) -> None:
        container = self.query_one("#ssh_inputs_container", Container)
        container.display = not self.configs.get("copy_from_local", True)

class PathField(Static):
    configs = Config().configs
    def compose(self) -> ComposeResult:
        if self.id == "dest_path_field":
            yield Input(self.configs.get("dest_path", "/home/user/heap"), id="dest_path")
        else:
            yield Input(self.configs.get("log_file_path", "/var/log/messages"), id="log_dirs")

class LogsFetcher(App):
    """A Textual App to fetch logs from specified directories within a date range."""

    logger = logging.getLogger("LogsFetcher")

    BINDINGS = [
        ("a", "add_path", "Add path"),
        ]

    CSS_PATH = "logs_fetcher.tcss"

    from_time = (datetime.now() - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")
    to_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    configs = None

    def compose(self) -> ComposeResult:
        self.logger.info("The app is composing the layout.")
        self.configs = Config().configs
        logging.debug(f"Loaded configurations: {self.configs}")
        logging.debug(f"Destination path from config: {self.configs.get('dest_path')}")
        yield Header()
        yield Footer()
        with Grid(id="main-container"):
            with Grid(id="dates", classes="panel"):
                yield Label("From date:", id="from_date_label")
                yield Input(placeholder=self.from_time, classes="datetime_input", id="from_date", value=self.from_time, valid_empty=False)
                yield Label("To date:", id="to_date_label")
                yield Input(placeholder=self.to_time, classes="datetime_input", id="to_date", value=self.to_time, valid_empty=False)
                yield Label("Slow mode:", id="slow_mode_label")
                yield Switch(id="slow_mode", value=self.configs.get("slow_mode", False), animate=True)
                yield Label("Directories with logs:", id="log_dirs_label")
                yield VerticalScroll(PathField(), id="path_fields")
                yield Button("Add path", id="add_path", variant="success")
                yield Label("") # Spacer
                yield Label("Destination:", id="log_destination_label")
                yield PathField(id="dest_path_field")
            yield SSHSettings(id="ssh_settings", classes="panel")
            yield Button("COPY", id="copy_btn", variant="primary")


    def action_add_path(self) -> None:
        """An action to add a path."""
        new_path = PathField()
        self.query_one("#path_fields").mount(new_path)
        new_path.scroll_visible()

    def action_copy(self) -> None:
        """An action to start copying logs."""
        from_date_input = self.query_one("#from_date", Input)
        to_date_input = self.query_one("#to_date", Input)
        # Query for inputs and cast each result to Input so Pylance knows about `.value`
        log_inputs = list(self.query("#path_fields Input"))
        log_dirs_input = [cast(Input, inp).value for inp in log_inputs]
        dest_path_input = self.query_one("#dest_path", Input)

        logs_cutter = LogsCutter(
            from_date=from_date_input.value,
            to_date=to_date_input.value,
            log_dirs=log_dirs_input,
            dest_path=dest_path_input.value,
        )
        logs_cutter.cut_logs()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        if event.button.id == "add_path":
            self.action_add_path()
        if event.button.id == "copy_btn":
            self.action_copy()
    
    def on_switch_changed(self, event: Switch.Changed) -> None:
        """Called when the switch is toggled."""
        container = self.query_one("#ssh_inputs_container", Container)
        # Use the instance value (event.switch.value) rather than the Switch class attribute.
        if event.switch.id == "copy_from_localhost" and event.switch.value is True:
            container.display = False
        elif event.switch.id == "copy_from_localhost" and event.switch.value is False:
            container.display = True


class LogsCutter():
    """A class to handle log cutting based on date ranges."""

    def __init__(self, from_date: str, to_date: str, log_dirs: list[str], dest_path: str):
        self.from_date = date_parser.parse(from_date)
        self.to_date = date_parser.parse(to_date)
        self.log_dirs = log_dirs
        self.dest_path = dest_path
        self.logger = logging.getLogger("LogsCutter")
        self.logger.debug(f"Initialized LogsCutter with from_date: {self.from_date} and to_date: {self.to_date}")

    def cut_logs(self):
        self.logger.debug("Starting to cut logs...")
        self.logger.debug(f"From date: {self.from_date}, To date: {self.to_date}")
        for log_dir in self.log_dirs:
            self.logger.debug(f"Processing log directory: {log_dir}")
        self.logger.debug(f"Logs have been cut and saved to {self.dest_path}")
        # for log_dir in self.log_dirs:
        #     with open(log_dir, 'r') as file:
        #         for line in file:
        #             pass


if __name__ == "__main__":
    configs = Config().configs

    logging.basicConfig(
        level=configs.get(f"debug_level", "WARNING"),  # Logging levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
        filename=configs.get("logs_fetcher_log_file_path", "logs/app.log"),
        filemode="a",         # "w" overwrite, "a" append
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    app = LogsFetcher()
    app.run()
