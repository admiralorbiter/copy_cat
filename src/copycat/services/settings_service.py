import os
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional
from platformdirs import user_config_dir

@dataclass
class UserSettings:
    voice: str = "en-US-JennyNeural"
    rate: str = "+0%"
    code_mode: str = "announce_and_skip"
    link_mode: str = "text_only_clean"

AVAILABLE_VOICES = [
    ("en-US-JennyNeural", "English (US) - Jenny (Female)"),
    ("en-US-GuyNeural", "English (US) - Guy (Male)"),
    ("en-US-AriaNeural", "English (US) - Aria (Female)"),
    ("en-GB-SoniaNeural", "English (UK) - Sonia (Female)"),
    ("en-AU-Neural", "English (AU) - Natascha (Female)"),
]

AVAILABLE_RATES = ["-50%", "-25%", "+0%", "+25%", "+50%", "+75%", "+100%"]

class SettingsService:
    """Manages user settings persistence via platformdirs JSON file storage."""

    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is None:
            config_dir = Path(user_config_dir("copy_cat", appauthor=False))
        self.config_dir = config_dir
        self.config_file = self.config_dir / "settings.json"
        self.settings = self.load_settings()

    def load_settings(self) -> UserSettings:
        if not self.config_file.exists():
            return UserSettings()

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return UserSettings(
                voice=data.get("voice", "en-US-JennyNeural"),
                rate=data.get("rate", "+0%"),
                code_mode=data.get("code_mode", "announce_and_skip"),
                link_mode=data.get("link_mode", "text_only_clean"),
            )
        except Exception:
            return UserSettings()

    def save_settings(self, settings: UserSettings) -> None:
        self.settings = settings
        self.config_dir.mkdir(parents=True, exist_ok=True)
        temp_file = self.config_file.with_suffix(".tmp")

        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(asdict(settings), f, indent=2)

        os.replace(temp_file, self.config_file)
