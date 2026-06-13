import logging
from pathlib import Path
from datetime import datetime

LOG_DIR = Path.home() / ".codebrief" / "logs"
LOG_FILE = LOG_DIR / f"codebrief_{datetime.now().strftime('%Y%m%d')}.log"


def get_logger(name: str) -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        formatter = logging.Formatter(
            fmt="[%(asctime)s] %(levelname)-8s %(name)s — %(message)s",
            datefmt="%H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def set_log_level(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.getLogger("code_brief").setLevel(level)

    # write a separator at the start of each run
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n{'─' * 60}\n")