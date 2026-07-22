import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional
from platformdirs import user_config_dir

logger = logging.getLogger(__name__)

@dataclass
class UserSettings:
    voice: str = "en-US-JennyNeural"
    rate: str = "+0%"
    code_mode: str = "announce_and_skip"
    link_mode: str = "text_only_clean"
    # Phase 3.5 AI Transformation Settings
    ai_mode: str = "off"                      # "off", "code_summary", "data_summary", "gist"
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "gemma3:12b"
    ollama_timeout: float = 3.0

class SettingsService:
    """Manages application settings persistence via platformdirs JSON storage."""

    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path(user_config_dir("copy_cat", appauthor=False))

        self.config_file = self.config_dir / "settings.json"
        self.settings = self.load_settings()

    def load_settings(self) -> UserSettings:
        if not self.config_file.exists():
            return UserSettings()

        try:
            content = self.config_file.read_text(encoding="utf-8")
            data = json.loads(content)
            # Filter only valid UserSettings fields
            valid_keys = {f for f in UserSettings.__dataclass_fields__}
            filtered_data = {k: v for k, v in data.items() if k in valid_keys}
            return UserSettings(**filtered_data)
        except Exception as err:
            logger.warning(f"Failed to load settings file ({err}); using default settings.")
            return UserSettings()

    def save_settings(self, settings: UserSettings) -> None:
        self.settings = settings
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            temp_file = self.config_file.with_suffix(".tmp")
            data = asdict(settings)
            temp_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
            temp_file.replace(self.config_file)
        except Exception as err:
            logger.error(f"Failed to save settings file: {err}")
