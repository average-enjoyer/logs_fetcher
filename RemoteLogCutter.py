from LogCutter import LogCutter
import paramiko
import stat


class RemoteLogCutter(LogCutter):
    """A LogCutter subclass that fetches logs from a remote server via SSH before cutting them."""

    def __init__(self, hostname, username, password, port=22, *args, **kwargs):
        """
        Initialize the RemoteLogCutter with an SSH client.

        :param hostname: The remote server's hostname or IP address.
        :param username: The SSH username.
        :param password: The SSH password.
        :param port: The SSH port (default is 22).
        """
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname=hostname, username=username, password=password, port=port)
        super().__init__(*args, **kwargs)
        self.ssh_client = ssh_client

        self.lc = LogCutter(
            from_date="2025-10-20 08:00:00",
            to_date="2025-10-20 08:23:00",
            dest_path="res")
        print(f"agrs: {args}")
        print(f"kwargs: {kwargs}")

    # # def fetch_remote_logs(self) -> None:
    # #     """Fetch log files from the remote server via SFTP."""
    # #     sftp_client = self.ssh_client.open_sftp()
    # #     for remote_file in self.log_files:
    # #         local_path = f"/tmp/{remote_file.split('/')[-1]}"
    # #         sftp_client.get(remote_file, local_path)
    # #         self.log_files[self.log_files.index(remote_file)] = local_path
    # #     sftp_client.close()

    # def cut_logs(self) -> None:
    #     """Fetch remote logs and then cut them using the parent class method."""
    #     # self.fetch_remote_logs()
    #     sftp_client = self.ssh_client.open_sftp()
    #     files = []
    #     for log_file in self.log_files:
    #         file_attr = sftp_client.stat(log_file)
    #         if stat.S_ISDIR(file_attr.st_mode):
    #             for item in sftp_client.listdir(log_file):
    #                 files.append(sftp_client.listdir(f"{log_file}/{item}"))
    #         files.append(sftp_client.listdir(log_file))
    #     print(files)
    #     # super().cut_log()
