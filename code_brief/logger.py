import logging
from datetime import datetime
from pathlib import Path

LOG_DIR = Path.home() / ".codebrief" / "logs"
LOG_FILE = LOG_DIR / f"codebrief_{datetime.now().strftime('%Y%m%d')}.log"


def _make_handler() -> logging.Handler:
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    except OSError:
        handler = logging.NullHandler()

    formatter = logging.Formatter(
        fmt="[%(asctime)s] %(levelname)-8s %(name)s - %(message)s",
        datefmt="%H:%M:%S",
    )
    handler.setFormatter(formatter)
    return handler


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.addHandler(_make_handler())

    return logger


def set_log_level(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.getLogger("code_brief").setLevel(level)

    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n{'-' * 60}\n")
    except OSError:
        return
