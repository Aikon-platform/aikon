import json
import logging
import os
import random
import traceback
import time
from pathlib import Path

from django.utils.html import strip_tags
from typing import Any, Iterable, Optional, Union

from app.webapp.utils.paths import BASE_DIR, LOG_DIR
from app.config.settings import DEBUG


def sanitize(v):
    """
    Helper function to convert non-serializable values to string representations.
    """
    if isinstance(v, (str, int, float, bool, type(None))):
        return v
    elif isinstance(v, (list, tuple)):
        return [sanitize(x) for x in v]
    elif isinstance(v, dict):
        return {str(k): sanitize(val) for k, val in v.items()}
    else:
        # For custom objects, include class name in representation
        return f"{v.__class__.__name__}({str(v)})"


def pprint(o):
    if isinstance(o, str):
        if "html" in o:
            return strip_tags(o)[:500]
        try:
            return json.dumps(json.loads(o), indent=4, sort_keys=True)
        except ValueError:
            return o
    elif isinstance(o, dict) or isinstance(o, list):
        try:
            return json.dumps(o, indent=4, sort_keys=True)
        except TypeError:
            try:
                if isinstance(o, dict):
                    sanitized = {str(k): sanitize(v) for k, v in o.items()}
                else:
                    sanitized = [sanitize(v) for v in o]
                return json.dumps(sanitized, indent=4, sort_keys=True)
            except Exception:
                return str(o)
    return str(o)


class Logger:
    """
    Unified logger for the IIIF downloader that handles:
    - Console output with colors
    - File logging
    - Progress bars
    - Error tracking
    """

    # ANSI Color codes
    COLORS = {
        "error": "\033[91m",  # red
        "warning": "\033[93m",  # yellow
        "info": "\033[94m",  # blue
        "success": "\033[92m",  # green
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "black": "\033[90m",
        "bold": "\033[1m",
        "underline": "\033[4m",
        "end": "\033[0m",
    }

    def __init__(self, log_dir: Union[str, Path]):
        """
        Initialize the logger with a directory for log files

        Args:
            log_dir: Directory where log files will be stored
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.compact = False

        self.error_log = self.log_dir / "error.log"
        self.download_log = self.log_dir / "download.log"

        # Setup logging
        self.logger = logging.getLogger("aikon")
        self.logger.setLevel(logging.INFO)

        for log_file in [self.error_log, self.download_log]:
            if not os.path.exists(log_file):
                with open(log_file, "x") as _:
                    pass

        fh = logging.FileHandler(self.error_log)
        fh.setLevel(logging.ERROR)
        self.logger.addHandler(fh)

        # Only write info messages to console
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        self.logger.addHandler(ch)

    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp in readable format."""
        return time.strftime("%Y-%m-%d %H:%M:%S")

    def get_color(self, color: str) -> str:
        """Get the ANSI color code for a message type."""
        return self.COLORS.get(color, "")

    def format_message(self, *msg: Any, msg_type: str = "info") -> str:
        """Format a message with timestamp and colors."""
        color = self.get_color(msg_type)
        timestamp = self._get_timestamp()

        formatted = "\n".join([f"{color}{self.COLORS['bold']}{pprint(m)}" for m in msg])
        if self.compact:
            return f"\n{timestamp}{color}{formatted}{self.COLORS['end']}"

        return f"\n\n{timestamp}\n{color}{formatted}{self.COLORS['end']}\n\n"

    @staticmethod
    def format_exception(exception: Exception) -> str:
        """Format an exception with timestamp and colors."""
        msg = f"\n[{exception.__class__.__name__}] {str(exception)}"
        msg += f"\n{traceback.format_exc()}"

        return msg

    def error(self, *msg: Any, exception: Optional[Exception] = None):
        """
        🚨 Log an error message and optionally an exception

        Args:
            msg: Message to log
            exception: Optional exception to include in log
        """
        error_msg = self.format_message(*msg, msg_type="error")
        if exception:
            error_msg += self.format_exception(exception)

        self.logger.error(error_msg)

    def log(self, *msg: Any, msg_type: Optional[str] = None):
        """Log a message with a given type."""
        msg_type = msg_type or random.choice(list(self.COLORS.keys()))
        self.logger.info(self.format_message(*msg, msg_type=msg_type))

    def warning(self, *msg: Any):
        """⚠️ Log a warning message."""
        self.logger.warning(self.format_message(*msg, msg_type="warning"))

    def info(self, *msg: Any):
        """ℹ️ Log an info message."""
        self.logger.info(self.format_message(*msg, msg_type="info"))

    def magic(self, *msg: Any):
        """🔮 Log a magical message."""
        self.logger.info(self.format_message(*msg, msg_type="magenta"))

    def water(self, *msg: Any):
        """🪼 Log a watery message."""
        self.logger.info(self.format_message(*msg, msg_type="cyan"))

    def white(self, *msg: Any):
        """🏳 Log a white message."""
        self.logger.info(self.format_message(*msg, msg_type="white"))

    def black(self, *msg: Any):
        """️🏴 Log a black message."""
        self.logger.info(self.format_message(*msg, msg_type="black"))

    def success(self, *msg: Any):
        """✅ Log a success message."""
        self.logger.info(self.format_message(*msg, msg_type="success"))

    def progress(self, iterable: Iterable, desc: str = "", total: Optional[int] = None):
        """
        Create a progress bar for an iteration

        Args:
            iterable: The iterable to track
            desc: Description of the progress
            total: Total number of items (optional)

        Returns:
            tqdm: Progress bar object
        """
        self.logger.info(desc)
        # from tqdm import tqdm
        # return tqdm(
        #     iterable,
        #     total=total,
        #     unit="image",
        #     ncols=100,
        #     bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
        # )

    def log_failed_download(self, img_path: str, img_url: str):
        """
        Log a failed download attempt

        Args:
            img_path: Path of the image that should have been downloaded
            img_url: URL that failed to be downloaded
        """
        self.add_to_file(self.download_log, f"{img_path} {img_url}\n", mode="a")

    @staticmethod
    def add_to_file(log_file, content, mode="w"):
        """Add a message to the log file."""
        with open(log_file, mode) as f:
            try:
                if mode == "a" and f.tell() > 0:
                    f.write("\n")
                json.dump(content, f)
            except Exception as e:
                f.write(pprint(content))


# Create a global logger instance
logger = Logger(f"{BASE_DIR}/{LOG_DIR}")


def log(msg, exception: Exception = None, msg_type=None):
    if exception:
        logger.error(msg, exception=exception)
        return
    logger.log(msg, msg_type=msg_type)


def console(msg="🚨🚨🚨", msg_type=None):
    print(pprint(msg))
    logger.log(msg, msg_type=msg_type)


def download_log(img_name, img_url):
    logger.log_failed_download(img_name, img_url)
