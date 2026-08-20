import contextlib
import logging

from mcp.server import MCPServer

from Config import Config
from LogCutter import LogCutter
from RemoteLogCutter import RemoteLogCutter, SSH_CONNECT_TIMEOUT

mcp = MCPServer(name="log-harvester")


class CollectingLogHandler(logging.Handler):
    """Collects formatted WARNING+ records instead of just leaving them in app.log.

    LogCutter/RemoteLogCutter only log per-file problems (missing files, rsync
    failures) without raising, so a bare wrapper would silently "succeed" even
    when some requested paths failed.
    """

    def __init__(self, level: int = logging.WARNING):
        super().__init__(level=level)
        self.records: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(self.format(record))


@contextlib.contextmanager
def collect_warnings():
    handler = CollectingLogHandler()
    loggers = [logging.getLogger("LogCutter"), logging.getLogger("RemoteLogCutter")]
    for lg in loggers:
        lg.addHandler(handler)
    try:
        yield handler.records
    finally:
        for lg in loggers:
            lg.removeHandler(handler)


@mcp.tool()
def cut_local_logs(from_date: str, to_date: str, dest_path: str, log_paths: list[str]) -> dict:
    """Cut local log files or directories down to the given date range.

    Args:
        from_date: Start of the date range (e.g. "2025-10-09 15:30:00").
        to_date: End of the date range.
        dest_path: Local directory to write the cut log files into.
        log_paths: Local file or directory paths to cut. Directories are
            scanned non-recursively for files to cut.
    """
    with collect_warnings() as warnings:
        logs_cutter = LogCutter(from_date=from_date, to_date=to_date, dest_path=dest_path)
        logs_cutter.cut_local_logs(log_paths)

    return {
        "status": "ok" if not warnings else "completed_with_warnings",
        "dest_path": dest_path,
        "warnings": warnings,
    }


@mcp.tool()
def cut_remote_logs(
    from_date: str,
    to_date: str,
    dest_path: str,
    log_paths: list[str],
    hostname: str | None = None,
    port: int | None = None,
) -> dict:
    """Cut log files from a remote host (over SSH) down to the given date range.

    SSH username and password are read from the local ssh_settings config
    (the same one the LogHarvester TUI uses) rather than being passed in here,
    so credentials never appear in a tool call. hostname/port optionally
    override the configured values for this call only.

    Args:
        from_date: Start of the date range (e.g. "2025-10-09 15:30:00").
        to_date: End of the date range.
        dest_path: Local directory to write the cut log files into.
        log_paths: Remote file or directory paths to cut. A trailing "/" on
            the last entry treats all given paths as directories.
        hostname: Overrides the configured SSH host for this call, if given.
        port: Overrides the configured SSH port for this call, if given.
    """
    ssh_settings = Config().configs.get("ssh_settings", {})

    with collect_warnings() as warnings:
        remote_lc = RemoteLogCutter(
            from_date=from_date,
            to_date=to_date,
            dest_path=dest_path,
            hostname=hostname or ssh_settings.get("hostname", ""),
            username=ssh_settings.get("username", ""),
            password=ssh_settings.get("password", ""),
            port=port or ssh_settings.get("port", 22),
            timeout=SSH_CONNECT_TIMEOUT,
        )
        remote_lc.cut_logs(log_paths)

    return {
        "status": "ok" if not warnings else "completed_with_warnings",
        "dest_path": dest_path,
        "warnings": warnings,
    }


if __name__ == "__main__":
    mcp.run()
