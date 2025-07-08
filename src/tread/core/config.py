"""Configuration management module for tRead."""

import json
import os
from typing import Dict, Any, List


class Config:
    """Handles loading and accessing configuration from config.json."""

    def __init__(self, config_path: str = None):
        if config_path is None:
            # Look for config.json in the project root
            config_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "..", "config.json"
            )
            config_path = os.path.abspath(config_path)
        self.config_path = config_path
        self._config_data = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Warning] Could not load config.json: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        return {
            "keybinds": {
                "quit": ["q"],
                "chapter_menu": ["c"],
                "next_page": ["j", "\u001b[B", " ", "\u001b[6~"],
                "prev_page": ["k", "\u001b[A", "b", "\u001b[5~"],
                "next_chapter": ["n"],
                "prev_chapter": ["p"],
                "start": ["s"],
                "end": ["e"],
                "bookmark_save": ["b"],
                "bookmark_goto": ["g"],
                "chapter_menu_down": ["\u001b[B", "j"],
                "chapter_menu_up": ["\u001b[A", "k"],
                "chapter_menu_select": ["\r"],
                "chapter_menu_close": ["q", "c"],
                "help": ["h"],
            },
            "formatting": {
                "paragraph_spacing": 1,
                "preserve_line_breaks": True,
                "paragraph_indent": 0,
            },
            "bookmarks": {
                "auto_bookmark_on_exit": True,
                "auto_load_bookmark_on_open": True,
            },
        }

    @property
    def keybinds(self) -> Dict[str, List[str]]:
        return self._config_data.get("keybinds", {})

    @property
    def formatting(self) -> Dict[str, Any]:
        return self._config_data.get("formatting", {})

    @property
    def bookmarks(self) -> Dict[str, Any]:
        return self._config_data.get("bookmarks", {})


# Global configuration instance
_config = None


def get_config() -> Config:
    global _config
    if _config is None:
        _config = Config()
    return _config
