import json


class Config():
    configs = {}

    def __init__(self) -> None:
        self.configs = self.load_config()

    def load_config(self) -> dict:
        """Load configuration settings."""
        with open("src/logs_fetcher/settings.json", "r") as f:
            configs = json.load(f)
        return configs
