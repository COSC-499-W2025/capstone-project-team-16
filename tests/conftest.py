import os
import tempfile
from pathlib import Path


def pytest_configure(config) -> None:
    temp_root = Path(__file__).resolve().parent.parent / ".pytest-tmp"
    temp_root.mkdir(exist_ok=True)
    config.option.basetemp = str(temp_root)
    os.environ["TMPDIR"] = str(temp_root)
    os.environ["TEMP"] = str(temp_root)
    os.environ["TMP"] = str(temp_root)
    tempfile.tempdir = str(temp_root)
