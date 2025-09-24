#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Settings management for Dream Background Remover plugin
"""

import json
import os
import platform
from typing import cast, Dict, Union, Literal

ModelKey = Literal["851-labs", "bria"]
SettingsDict = Dict[str, Union[str, bool]]

CONFIG_FILE_NAME = "dream-background-remover-config.json"
GIMP_VERSION = "3.0"
FILE_PERMISSIONS = 0o600

AVAILABLE_MODELS = {
    "851-labs": ("851-labs/background-remover:"
                 "a029dff38972b5fda4ec5d75d7d1cd25aeff621d2cf4946a41055d7db66"
                 "b80bc"),
    "bria": "bria/remove-background"
}
MODEL_DISPLAY_NAMES = {
    "851-labs": "851 Labs Background Remover (Default)",
    "bria": "Bria Remove Background"
}

DEFAULT_MODEL = "851-labs"
DEFAULT_MODE = "layer"
DEFAULT_API_KEY_VISIBLE = False
DEFAULT_SETTINGS: SettingsDict = {
    "api_key": "",
    "mode": DEFAULT_MODE,
    "api_key_visible": DEFAULT_API_KEY_VISIBLE,
    "model": DEFAULT_MODEL
}


def get_config_file() -> str:
    """Get path to config file in GIMP's user directory"""
    system = platform.system()

    if system == "Windows":
        gimp_dir = _get_windows_config_dir()
    elif system == "Darwin":
        gimp_dir = _get_macos_config_dir()
    else:
        gimp_dir = _get_linux_config_dir()

    try:
        os.makedirs(gimp_dir, exist_ok=True)
    except (OSError, PermissionError) as e:
        print(f"Warning: Could not create config directory {gimp_dir}: {e}")

    return os.path.join(gimp_dir, CONFIG_FILE_NAME)


def get_model_display_name(model_key: str) -> str:
    """Get a user-friendly display name for the model"""
    return MODEL_DISPLAY_NAMES.get(model_key, model_key)


def get_model_name(model_key: ModelKey) -> str:
    """
    Get the full model identifier from a model key.

    Args:
        model_key: Short model key (e.g., "bria", "851-labs")

    Returns:
        Full model identifier for Replicate API

    Examples:
        >>> get_model_name("bria")
        "bria/remove-background"
        >>> get_model_name("invalid")
        "851-labs/background-remover:a029dff38972b5fda4ec5d75d7d1cd25aeff621d2cf4946a41055d7db66b80bc"
    """
    return AVAILABLE_MODELS.get(model_key, AVAILABLE_MODELS[DEFAULT_MODEL])


def load_settings() -> SettingsDict:
    """Load settings from config file"""
    try:
        config_file = get_config_file()
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                loaded_settings = cast(SettingsDict, json.load(f))
                for key, default_value in DEFAULT_SETTINGS.items():
                    if key not in loaded_settings:
                        loaded_settings[key] = default_value
                return loaded_settings
    except (OSError, PermissionError) as e:
        print(f"Failed to read settings file: {e}")
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in settings file: {e}")
    except Exception as e:
        print(f"Unexpected error loading settings: {e}")

    return DEFAULT_SETTINGS.copy()


def store_settings(api_key: str, mode: str, api_key_visible: bool,
                   model: str = DEFAULT_MODEL) -> None:
    """Store settings to config file"""
    if mode not in ("layer", "file"):
        raise ValueError(f"Invalid mode: {mode}. Must be 'layer' or 'file'")

    if model not in AVAILABLE_MODELS:
        print(f"Warning: Unknown model '{model}', using default "
              f"'{DEFAULT_MODEL}'")
        model = DEFAULT_MODEL

    try:
        config_file = get_config_file()
        settings = {
            "api_key": api_key,
            "mode": mode,
            "api_key_visible": api_key_visible,
            "model": model
        }

        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)

        os.chmod(config_file, FILE_PERMISSIONS)

    except (OSError, PermissionError) as e:
        print(f"Failed to store settings: {e}")
    except (TypeError, ValueError) as e:
        print(f"Invalid data for JSON encoding: {e}")
    except Exception as e:
        print(f"Unexpected error storing settings: {e}")


def _get_linux_config_dir() -> str:
    """Get Linux config directory"""
    return os.path.join(os.path.expanduser("~"), '.config', 'GIMP',
                        GIMP_VERSION)


def _get_macos_config_dir() -> str:
    """Get macOS config directory"""
    home = os.path.expanduser("~")
    return os.path.join(home, "Library", "Application Support", "GIMP",
                        GIMP_VERSION)


def _get_windows_config_dir() -> str:
    """Get Windows config directory"""
    appdata = os.environ.get('APPDATA')
    if not appdata:
        appdata = os.path.expanduser("~\\AppData\\Roaming")
    return os.path.join(appdata, "GIMP", GIMP_VERSION)
