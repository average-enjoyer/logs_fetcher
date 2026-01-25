import os
import sys
import json
import shutil
from pathlib import Path

APP_NAME = "log_harvester"
CONFIG_FILE = "settings.json"
DEFAULT_CONFIG_FILE = "default_settings.json"

class Config():
    configs = {}

    def __init__(self) -> None:
        self.configs = self.load_config()

    def get_config_dir(self) -> Path:
        if sys.platform.startswith("win"):
            base = Path(os.environ["APPDATA"])
        else:
            base = Path.home() / ".config"

        return base / APP_NAME

    def get_user_config_path(self) -> Path:
        return self.get_config_dir() / CONFIG_FILE

    def get_default_config_path(self) -> Path:
        # if hasattr(sys, "_MEIPASS"):
            # return Path(sys._MEIPASS) / DEFAULT_CONFIG_FILE
        return Path(__file__).parent / DEFAULT_CONFIG_FILE

    def ensure_user_config_exists(self) -> None:
        config_dir = self.get_config_dir()
        user_config = self.get_user_config_path()

        if not user_config.exists():
            config_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy(self.get_default_config_path(), user_config)

    def load_config(self) -> dict:
        """Load configuration settings."""

        self.ensure_user_config_exists()
        with open(self.get_user_config_path(), "r", encoding="utf-8") as f:
            return json.load(f)

        # with open("src/log_harvester/settings.json", "r") as f:
        #     configs = json.load(f)
        # return configs
