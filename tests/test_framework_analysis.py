import json
import builtins
from unittest.mock import mock_open, patch

from metadata_extractor import detect_frameworks  

# ---------------------------------------------------------
# PYTHON FRAMEWORK FILES
# ---------------------------------------------------------
def test_detect_frameworks_python_files():
    """
    SCENARIO: Framework file is any Python-related file
    EXPECTED: detect_frameworks returns dependency names correctly.
    """
    text_content = "flask==2.0.0\nrequests>=2.30\n# comment\n"
    yaml_content = "dependencies:\n  - flask\n  - requests\n"

    file_map = {
        "requirements.txt": text_content,
        "pipfile": text_content,
        "pyproject.toml": text_content,
        "environment.yml": yaml_content,
    }

    for filename, content in file_map.items():
        entry = {"filename": f"/path/{filename}"}

        with patch.object(builtins, "open", mock_open(read_data=content)):
            result = detect_frameworks(entry)

        assert isinstance(result, list)
        assert set(result) == {"flask", "requests"}




def test_detect_frameworks_python_read_error():
    """
    SCENARIO: Python framework file exists but cannot be read (I/O error)
    EXPECTED: Returns an empty dependency list
    """

    entry = {"filename": "/path/requirements.txt"}

    with patch.object(builtins, "open", side_effect=Exception("read error")):
        result = detect_frameworks(entry)

    # New behavior: function returns just a list
    assert isinstance(result, list)
    assert result == []



# ---------------------------------------------------------
# NODE / PACKAGE.JSON
# ---------------------------------------------------------
def test_detect_frameworks_node_package_json():
    """
    SCENARIO: package.json contains dependencies and devDependencies
    EXPECTED: Returns a combined list of dependency names
    """
    fake_json = {
        "dependencies": {"express": "1.0"},
        "devDependencies": {"jest": "29"}
    }

    entry = {"filename": "/repo/package.json"}

    with patch.object(builtins, "open", mock_open(read_data=json.dumps(fake_json))):
        result = detect_frameworks(entry)

    # New behavior: function returns a list of dependency names
    assert isinstance(result, list)
    assert set(result) == {"express", "jest"}



def test_detect_frameworks_node_json_error():
    """
    SCENARIO: package.json exists but cannot be parsed due to JSON or file error
    EXPECTED: Returns an empty list of dependencies
    """
    entry = {"filename": "/repo/package.json"}

    with patch.object(builtins, "open", side_effect=Exception("json fail")):
        result = detect_frameworks(entry)

    # New behavior: function returns only a list
    assert isinstance(result, list)
    assert result == []



# ---------------------------------------------------------
# OTHER ECOSYSTEMS
# ---------------------------------------------------------
def test_detect_frameworks_other_ecosystems():
    """
    SCENARIO: File matches known ecosystem-specific filename
    EXPECTED: Returns placeholder strings only for ecosystems that have them,
              empty list for others.
    """
    cases = [
        ("cargo.toml", []),
        ("go.mod", []),
        ("pom.xml", ["See pom.xml"]),
        ("build.gradle", ["See build.gradle"]),
        ("gemfile", []),
        ("dockerfile", ["Dockerfile dependencies"]),
    ]

    for filename, expected in cases:
        entry = {"filename": f"/x/{filename}"}
        result = detect_frameworks(entry)

        assert isinstance(result, list)
        assert result == expected




# ---------------------------------------------------------
# UNKNOWN FILE
# ---------------------------------------------------------
def test_detect_frameworks_unknown_file():
    """
    SCENARIO: File does not match any known ecosystem-defining filenames
    EXPECTED: No dependencies returned
    """
    entry = {"filename": "/path/unknown.config"}

    result = detect_frameworks(entry)

    assert isinstance(result, list)
    assert result == []
