import logging
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
    def compose(self) -> ComposeResult:
        yield Label("Copy from localhost:", id="copy_from_localhost_label")
        yield Switch(id="copy_from_localhost", value=True, animate=True)
        with Container(id="ssh_inputs_container"):
            yield Label("SSH Settings")
            yield Input(placeholder="Host IP", id="host_ip", valid_empty=False)
            yield Input(placeholder="Username", id="username", valid_empty=False)
            yield Input(placeholder="Password", password=True, id="password", valid_empty=False)

class PathField(Static):
    def compose(self) -> ComposeResult:
        yield Input("/var/log/messages", id="log_dirs")

class LogsFetcher(App):
    """A Textual App to fetch logs from specified directories within a date range."""

    logger = logging.getLogger("LogsFetcher")

    BINDINGS = [
        ("a", "add_path", "Add path"),
        ]

    CSS_PATH = "logs_fetcher.tcss"

    from_time = (datetime.now() - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")
    to_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def compose(self) -> ComposeResult:
        self.logger.info("The app is composing the layout.")
        yield Header()
        yield Footer()
        with Grid(id="main-container"):
            with Grid(id="dates", classes="panel"):
                yield Label("From date:", id="from_date_label")
                yield Input(placeholder=self.from_time, classes="datetime_input", value=self.from_time, valid_empty=False)
                yield Label("To date:", id="to_date_label")
                yield Input(placeholder=self.to_time, classes="datetime_input", value=self.to_time, valid_empty=False)
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

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        if event.button.id == "add_path":
            self.action_add_path()
        if event.button.id == "copy_btn":
            self.action_copy()
    
    def on_switch_changed(self, event: Switch.Changed) -> None:
        """Called when the switch is toggled."""
        container = self.query_one("#ssh_inputs_container", Container)
        if event.switch.id == "copy_from_localhost" and Switch.value == True:
            container.display = False
        elif event.switch.id == "copy_from_localhost" and Switch.value == False:
            container.display = True


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.WARNING,  # Set the lowest level to capture. Logging levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
        filename="logs/app.log",
        filemode="a",         # "w" overwrite, "a" append
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    app = LogsFetcher()
    app.run()
