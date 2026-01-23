import json


class Config():
    configs = {}

    def __init__(self) -> None:
        self.configs = self.load_config()

    def load_config(self) -> dict:
        """Load configuration settings."""
        with open("src/log_harvester/settings.json", "r") as f:
            configs = json.load(f)
        return configs
