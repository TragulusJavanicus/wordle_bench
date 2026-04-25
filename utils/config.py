"""Configuration loader: reads config.ini with sensible defaults."""

import configparser
import os

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.ini")

DEFAULTS = {
    "PLAY": {"COLOR": "True"},
    "BENCH": {"SAMPLE_SIZE": "1000", "USER": "ADMIN", "SEED": "42"},
}


def load_config() -> configparser.ConfigParser:
    """Load configuration from config.ini, falling back to built-in defaults."""
    config = configparser.ConfigParser()
    config.read_dict(DEFAULTS)
    config.read(CONFIG_FILE)
    return config


def get_play_config(config: configparser.ConfigParser) -> dict:
    return {
        "color": config.getboolean("PLAY", "COLOR", fallback=True),
    }


def get_bench_config(config: configparser.ConfigParser) -> dict:
    return {
        "sample_size": config.getint("BENCH", "SAMPLE_SIZE", fallback=1000),
        "user": config.get("BENCH", "USER", fallback="ADMIN"),
        "seed": config.getint("BENCH", "SEED", fallback=42),
    }
