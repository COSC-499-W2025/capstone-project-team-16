"""
Configures logging for the application.

This module provides a centralized function to set up the root logger.
"""
import logging
import sys
 
def setup_logging(log_level: int = logging.INFO, log_file: str = "skill_scope.log") -> None:
    """
    Configures the root logger for the entire application.

    This function sets up two handlers: one that streams logs to the console
    (stdout) and another that writes logs to a specified file.

    Args:
        log_level (int): The minimum logging level to capture (e.g., logging.INFO).
        log_file (str): The path to the log file.
    """
    # Create a root logger configuration
    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, mode='a', encoding='utf-8')
    ]

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers
    )