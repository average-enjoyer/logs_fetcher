import logging
import os
import asyncio
from Config import Config
from typing import cast
from datetime import datetime, timedelta
from textual.app import App, ComposeResult
from textual.containers import Grid, Container, VerticalScroll
from textual.widgets import Footer, Header, Static, Label, Input, Switch, Button, LoadingIndicator

from LogCutter import LogCutter
from RemoteLogCutter import RemoteLogCutter


class SSHSettings(Static):
    configs = Config().configs
    ssh_settings = configs.get("ssh_settings", {})
    def compose(self) -> ComposeResult:
        yield Label("Copy from localhost:", id="copy_from_localhost_label")
        yield Switch(id="copy_from_localhost", value=self.configs.get("copy_from_local", True), animate=True)

        with Container(id="ssh_inputs_container"):
            yield Label("SSH Settings")
            yield Input(placeholder="Host:port", id="hostname", value=f"{self.ssh_settings.get('hostname', '')}:{self.ssh_settings.get('port', '')}", valid_empty=False)
            yield Input(placeholder="Username", id="username", value=self.ssh_settings.get("username", ""), valid_empty=False)
            yield Input(placeholder="Password", id="password", password=True, value=self.ssh_settings.get("password", ""), valid_empty=False)

    def on_mount(self) -> None:
        container = self.query_one("#ssh_inputs_container", Container)
        container.display = not self.configs.get("copy_from_local", True)

class PathField(Static):
    configs = Config().configs
    def compose(self) -> ComposeResult:
        if self.id == "dest_path_field":
            yield Input(self.configs.get("dest_path", "/home/user/heap"), id="dest_path")
        else:
            yield Input(self.configs.get("log_file_path", "/var/log/messages"), id="log_files")

class LogsFetcher(App):
    """A Textual App to fetch logs from specified directories within a date range."""

    logger = logging.getLogger("LogsFetcher")

    BINDINGS = [
        ("a", "add_path", "Add path"),
        ]

    CSS_PATH = "../tcss/logs_fetcher.tcss"

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
                # Implement if needed in the future
                # yield Label("Slow mode:", id="slow_mode_label")
                # yield Switch(id="slow_mode", value=self.configs.get("slow_mode", False), animate=True)
                yield Label("Directories with logs:", id="log_files_label")
                yield VerticalScroll(PathField(), id="path_fields")
                yield Button("Add path", id="add_path", variant="success")
                yield Label("") # Spacer
                yield Label("Destination:", id="log_destination_label")
                yield PathField(id="dest_path_field")
            yield SSHSettings(id="ssh_settings", classes="panel")
            yield Button("COPY", id="copy_btn", variant="primary")
            yield LoadingIndicator(id="loading_indicator")


    def action_add_path(self) -> None:
        """An action to add a path."""
        new_path = PathField()
        self.query_one("#path_fields").mount(new_path)
        new_path.scroll_visible()

    async def action_copy(self) -> None:
        """An async action to start copying logs without blocking the UI."""
        loading_indicator = self.query_one("#loading_indicator", LoadingIndicator)
        # show indicator and yield control so the UI can update
        loading_indicator.display = True
        await asyncio.sleep(0)

        from_date_input = self.query_one("#from_date", Input)
        to_date_input = self.query_one("#to_date", Input)
        # Query for inputs and cast each result to Input so Pylance knows about `.value`
        log_inputs = list(self.query("#path_fields Input"))
        log_files_input = [cast(Input, inp).value for inp in log_inputs]
        dest_path_input = self.query_one("#dest_path", Input)

        # gather ssh info (may be unused for local copy)
        hostname_port = self.query_one("#hostname", Input).value
        hostname = hostname_port.split(":")[0]
        port = 22
        try:
            if hostname_port.split(":")[1]:
                port = int(hostname_port.split(":")[1])
        except Exception:
            port = 22
        username = self.query_one("#username", Input).value
        password = self.query_one("#password", Input).value

        # run the blocking copy code in a thread so the UI can continue to animate
        await asyncio.to_thread(
            self._copy_sync,
            from_date_input.value,
            to_date_input.value,
            dest_path_input.value,
            log_files_input,
            self.query_one("#copy_from_localhost", Switch).value,
            hostname,
            port,
            username,
            password,
        )

        loading_indicator.display = False

    def _copy_sync(self, from_date, to_date, dest_path, log_files_input: list[str], copy_from_local: bool, hostname: str, port: int, username: str, password: str) -> None:
        """Blocking copy logic moved to a sync helper so it can be run in a thread."""
        # This is the same logic as before but running in a background thread.
        if copy_from_local is True:
            logs_cutter = LogCutter(
            from_date=from_date,
            to_date=to_date,
            dest_path=dest_path,
            )
            # TODO: Refactor this
            for log in log_files_input:
                if os.path.exists(log):
                    if os.path.isdir(log):
                        self.logger.debug(f"Processing log directory: {log}")
                        for logfile in os.listdir(log):
                            log_path = os.path.join(log, logfile)
                            if os.path.isfile(log_path):
                                self.logger.debug(f"Processing log file: {log_path}")
                                with open(log_path, "r") as log_file:
                                    log_lines = log_file.readlines()
                                    logs_cutter.cut_log(log_path, log_lines)
                    elif os.path.isfile(log):
                        self.logger.debug(f"Processing a single log file: {log}")
                        with open(log, "r") as log_file:
                            log_lines = log_file.readlines()
                            logs_cutter.cut_log(log, log_lines)
                else:
                    self.logger.error(f"Log file or directory does not exist: {log}")
        else:
            self.logger.debug(f"hostname = {hostname}, port = {port}, username = {username}, password = {password}")
            remote_lc = RemoteLogCutter(
                from_date=from_date,
                to_date=to_date,
                dest_path=dest_path,
                hostname=hostname,
                username=username,
                password=password,
                port=port,
            )
            remote_lc.cut_logs(requested_log_file_paths=log_files_input)


    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        if event.button.id == "add_path":
            self.action_add_path()
        if event.button.id == "copy_btn":
            # schedule the async action so the button handler doesn't block
            asyncio.create_task(self.action_copy())
    
    def on_switch_changed(self, event: Switch.Changed) -> None:
        """Called when the switch is toggled."""
        container = self.query_one("#ssh_inputs_container", Container)
        # Use the instance value (event.switch.value) rather than the Switch class attribute.
        if event.switch.id == "copy_from_localhost" and event.switch.value is True:
            container.display = False
        elif event.switch.id == "copy_from_localhost" and event.switch.value is False:
            container.display = True


if __name__ == "__main__":
    configs = Config().configs

    logging.basicConfig(
        level=configs.get("debug_level", "WARNING"),  # Logging levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
        filename=configs.get("logs_fetcher_log_file_path", "logs/app.log"),
        filemode="a",         # "w" overwrite, "a" append
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    app = LogsFetcher()
    app.run()
