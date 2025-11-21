from LogCutter import LogCutter
import paramiko
import stat
import logging # debug level is set in main.py
import os
import subprocess


class RemoteLogCutter():
    """A LogCutter subclass that fetches logs from a remote server via SSH before cutting them."""

    def __init__(self, from_date: str, to_date: str, dest_path: str, hostname: str, username: str, password: str, port:int=22):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port
        self.from_date = from_date
        self.to_date = to_date
        self.dest_path = dest_path
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname=hostname, username=username, password=password, port=port)
        self.ssh_client = ssh_client
        self.tmp_dir = "./tmp"

        self.logger = logging.getLogger("RemoteLogCutter")
        self.trans = paramiko.Transport((hostname, port), default_window_size=2147483647)

    def get_log_list(self, requested_log_file_paths: list[str]):
        """
        Fetch list of log files from the remote server via SFTP.
        Args:
            requested_log_file_paths (list[str]): List of log file paths or directories on the remote server.
        Returns:
            list[str]: List of log file paths to download.
        """

        if type(requested_log_file_paths) is not list:
            self.logger.error(f"{requested_log_file_paths} (requested_log_file_paths) must be a list of strings.")
            raise TypeError("requested_log_file_paths must be a list of strings.")
        sftp_client = self.ssh_client.open_sftp()

        is_dir_to_fetch = False
        files_to_fetch = []

        if not os.path.isdir(self.tmp_dir):
            os.makedirs(self.tmp_dir)

        # Remove "/" at the end of the path provided by user
        if requested_log_file_paths[-1] == "/":
            requested_log_file_paths = requested_log_file_paths[:-1]
            is_dir_to_fetch = True

        # Get list of files to fetch
        for log_file_path in requested_log_file_paths:
            print(f'log_file_path="{log_file_path}"')
            # Check if user chooses directory with files to cut
            try:
                file_attr = sftp_client.stat(log_file_path)
            except FileNotFoundError as e:
                self.logger.error(f"Error stating file {log_file_path}: {e}")
                continue
            if is_dir_to_fetch or stat.S_ISDIR(file_attr.st_mode):
                for log_file in sftp_client.listdir(log_file_path):
                    # We take only .log files when directory is chosen
                    if log_file.endswith(".log"):
                        full_path = f"{log_file_path}/{log_file}"
                        # We take only files
                        if not stat.S_ISDIR(sftp_client.stat(full_path).st_mode):
                            print(f'full_path="{full_path}"')
                            print(f"wqerty={log_file}")
                            files_to_fetch.append(full_path)
                            sftp_client.get(remotepath=full_path, localpath=f"{self.tmp_dir}/{log_file}", max_concurrent_prefetch_requests=64)
            # If user chooses a file to cut
            else:
                files_to_fetch.append(log_file_path)
        return files_to_fetch

    def copy_log_files(self, file_paths: list[str]):
        """ Download log files from the remote server via rsync.
        Args:
            file_paths (list[str]): List of log file paths on the remote server.
        Returns:
            bool: True if rsync succeeded, False otherwise.
        """
        cmd = [
        "sshpass", "-p", self.password,
        "rsync", "-az",
        "-e", "ssh -o StrictHostKeyChecking=no"
        ]
        # Add remote file paths
        for f in file_paths:
            cmd.append(f"{self.username}@{self.hostname}:{f}")

        # Destination directory (local)
        cmd.append(self.tmp_dir)
        try:
            result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.logger.debug(f"rsync succeeded: {result.stdout}")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"rsync failed (rc={e.returncode}): {e.stderr}")
            return False
        except FileNotFoundError as e:
            self.logger.error(f"rsync/sshpass not found: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error running rsync: {e}")
            return False
        return True

    def cut_logs(self, requested_log_file_paths: list[str]):
        """Fetch log files from remote server and cut them based on date range.
        Args:
            requested_log_file_paths (list[str]): List of log file paths or directories on the remote server.
        """
        # Get list of log files to fetch
        files_to_fetch = self.get_log_list(requested_log_file_paths)

        # Download log files via rsync
        self.copy_log_files(files_to_fetch)

        # Use LogCutter to cut the fetched log files
        log_cutter = LogCutter(from_date=self.from_date, to_date=self.to_date, dest_path=self.dest_path)
        for log_file in files_to_fetch:
            local_log_path = os.path.join("./tmp", os.path.basename(log_file))
            print(f"local_log_path={local_log_path}")
            try:
                with open(local_log_path, "r") as log_file_handle:
                    log_lines = log_file_handle.readlines()
                    log_cutter.cut_log(local_log_path, log_lines)
            except OSError as e:
                self.logger.error(f"Error opening local log file {local_log_path}: {e}")
        self.remove_temp_files()

    def remove_temp_files(self):
        """Remove temporary files and directory used for storing fetched logs."""
        if os.path.exists(self.tmp_dir):
            for temp_file in os.listdir(self.tmp_dir):
                temp_file_path = os.path.join(self.tmp_dir, temp_file)
                try:
                    os.remove(temp_file_path)
                except OSError as e:
                    self.logger.error(f"Error removing temporary file {temp_file_path}: {e}")
            try:
                os.rmdir(self.tmp_dir)
            except OSError as e:
                self.logger.error(f"Error removing temporary directory {self.tmp_dir}: {e}")
