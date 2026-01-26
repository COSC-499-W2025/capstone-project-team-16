"""
Small utility helpers used by alternative_analysis.py

"""

from __future__ import annotations

import shutil
from datetime import datetime
from typing import Any, Sequence


def center_text(text: str) -> str:
    """Centers a string for terminal output."""
    width = shutil.get_terminal_size(fallback=(80, 20)).columns
    if len(text) >= width:
        return text
    padding = (width - len(text) + 1) // 2
    return " " * padding + text


def to_datetime(dt_value: Any) -> datetime:
    """
    Converts common timestamp formats into a datetime.

    Supports:
    - zipfile tuple/list: (Y, M, D, H, M, S, ...)
    - ISO strings: "2025-11-19T01:23:45" or "...Z"
    Falls back to datetime.now() if parsing fails.
    """
    # zipfile gives time as tuple/list (Y, M, D, H, M, S)
    if isinstance(dt_value, (list, tuple)) and len(dt_value) >= 6:
        try:
            y, mo, d, h, mi, s = dt_value[:6]
            return datetime(int(y), int(mo), int(d), int(h), int(mi), int(s))
        except Exception:
            pass

    # ISO string like "2025-11-19T01:23:45" or "2025-11-19T01:23:45Z"
    if isinstance(dt_value, str):
        try:
            return datetime.fromisoformat(dt_value.replace("Z", ""))
        except Exception:
            pass

    return datetime.now()
