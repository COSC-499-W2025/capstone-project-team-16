import json
import builtins
from unittest.mock import mock_open, patch

from metadata_extractor import detect_frameworks  

# ---------------------------------------------------------
# PYTHON FRAMEWORK FILES
# ---------------------------------------------------------
def test_detect_frameworks_python_files():
    """
    SCENARIO: Framework file is any Python-related file (requirements.txt, environment.yml, Pipfile, pyproject.toml)
    EXPECTED: Ecosystem is detected as Python and package names are parsed correctly
    """
    file_content = "flask==2.0.0\nrequests>=2.30\n# comment\n"

    for filename in ("requirements.txt", "environment.yml", "pipfile", "pyproject.toml"):
        entry = {"filename": f"/path/{filename}"}

        with patch.object(builtins, "open", mock_open(read_data=file_content)):
            result = detect_frameworks(entry)

        assert result["ecosystem"] == "python"
        assert set(result["detected"]) == {"flask", "requests"}


def test_detect_frameworks_python_read_error():
    """
    SCENARIO: Python framework file exists but cannot be read (I/O error)
    EXPECTED: Ecosystem is still Python, but no dependencies collected
    """
    entry = {"filename": "/path/requirements.txt"}

    with patch.object(builtins, "open", side_effect=Exception("read error")):
        result = detect_frameworks(entry)

    assert result["ecosystem"] == "python"
    assert result["detected"] == []


# ---------------------------------------------------------
# NODE / PACKAGE.JSON
# ---------------------------------------------------------
def test_detect_frameworks_node_package_json():
    """
    SCENARIO: package.json contains dependencies and devDependencies
    EXPECTED: Node ecosystem detected and all dependency keys returned
    """
    fake_json = {
        "dependencies": {"express": "1.0"},
        "devDependencies": {"jest": "29"}
    }

    entry = {"filename": "/repo/package.json"}

    with patch.object(builtins, "open", mock_open(read_data=json.dumps(fake_json))):
        result = detect_frameworks(entry)

    assert result["ecosystem"] == "node"
    assert set(result["detected"]) == {"express", "jest"}


def test_detect_frameworks_node_json_error():
    """
    SCENARIO: package.json exists but cannot be parsed due to JSON or file error
    EXPECTED: Ecosystem is Node but no dependencies collected
    """
    entry = {"filename": "/repo/package.json"}

    with patch.object(builtins, "open", side_effect=Exception("json fail")):
        result = detect_frameworks(entry)

    assert result["ecosystem"] == "node"
    assert result["detected"] == []


# ---------------------------------------------------------
# OTHER ECOSYSTEMS
# ---------------------------------------------------------
def test_detect_frameworks_other_ecosystems():
    """
    SCENARIO: File matches a known ecosystem-specific filename (Cargo, Go, Java, Ruby, Docker)
    EXPECTED: Correct ecosystem is identified and no detected dependencies returned
    """
    cases = [
        ("cargo.toml", "rust"),
        ("go.mod", "go"),
        ("pom.xml", "java"),
        ("build.gradle", "java"),
        ("gemfile", "ruby"),
        ("dockerfile", "docker"),
    ]

    for filename, ecosystem in cases:
        entry = {"filename": f"/x/{filename}"}
        result = detect_frameworks(entry)

        assert result["ecosystem"] == ecosystem
        assert result["detected"] == []


# ---------------------------------------------------------
# UNKNOWN FILE
# ---------------------------------------------------------
def test_detect_frameworks_unknown_file():
    """
    SCENARIO: File does not match any known ecosystem-defining filenames
    EXPECTED: No ecosystem detected and no dependencies returned
    """
    entry = {"filename": "/path/unknown.config"}

    result = detect_frameworks(entry)

    assert result["ecosystem"] is None
    assert result["detected"] == []