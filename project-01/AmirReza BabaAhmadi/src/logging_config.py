"""Shared logging setup. One logger, one file: logs/pipeline.log."""
import logging
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

_LOGGER = None


def get_logger(name: str = "etl") -> logging.Logger:
    global _LOGGER
    if _LOGGER is not None:
        return _LOGGER
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    fh = logging.FileHandler(LOG_DIR / "pipeline.log", mode="w", encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(fh)

    sh = logging.StreamHandler()
    sh.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.addHandler(sh)

    _LOGGER = logger
    return logger
