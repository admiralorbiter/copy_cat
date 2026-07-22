from pathlib import Path
from copycat.services.settings_service import SettingsService, UserSettings

def test_settings_service_default_and_persistence(tmp_path: Path):
    service = SettingsService(config_dir=tmp_path)
    assert service.settings.voice == "en-US-JennyNeural"
    assert service.settings.rate == "+0%"

    new_settings = UserSettings(
        voice="en-US-GuyNeural",
        rate="+25%",
        code_mode="omit",
    )
    service.save_settings(new_settings)

    # Reload service from same path
    reloaded_service = SettingsService(config_dir=tmp_path)
    assert reloaded_service.settings.voice == "en-US-GuyNeural"
    assert reloaded_service.settings.rate == "+25%"
    assert reloaded_service.settings.code_mode == "omit"

def test_settings_service_corrupted_json_recovery(tmp_path: Path):
    config_file = tmp_path / "settings.json"
    config_file.write_text("{corrupt json syntax", encoding="utf-8")

    service = SettingsService(config_dir=tmp_path)
    assert service.settings.voice == "en-US-JennyNeural"
