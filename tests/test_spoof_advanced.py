import os
import sys
import pytest

# Add the src directory to the system path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from metadata_extractor import detect_language_by_content

@pytest.mark.parametrize("filename, expected_lang, content", [
    ("python_test.spoof", "Python", "import os\ndef main():\n    print('Hello')"),
    ("java_test.spoof",   "Java",   "package com.example;\npublic class Test {}"),
    ("js_test.spoof",     "JavaScript", "import React from 'react';\nconsole.log('JS Detected');"),
    ("html_test.spoof",   "HTML",   "<!DOCTYPE html>\n<html><body><h1>Hello</h1></body></html>"),
    ("fake_script.py",    "C",      "#include <stdio.h>\nint main() { printf(\"I am C code\"); }"),
    ("fake_source.c",     "Python", "import os\ndef main():\n    print('I am actually Python')"),
    ("hidden_code.txt",   "C",      "#include <stdio.h>\nint main() { return 0; }"),
    ("no_ext_python",     "Python", "import sys\nprint('No extension')"),
    ("shebang_bash",      "Shell",  "#!/bin/bash\necho 'Hello'"),
    ("shebang_node",      "JavaScript", "#!/usr/bin/env node\nconsole.log('Hello')"),
    ("false_positive.txt", None,    "class Summary of the meeting\n - Point 1"),
    ("sql_strict.txt",    "SQL",    "SELECT * FROM users WHERE id = 1;"),
    ("sql_weak.txt",      None,     "Please SELECT one option."),
    ("typescript_check.ts", "TypeScript", "console.log('test');\nconst x: string = 'hello';"),
    ("spoofed_ts.txt",    "TypeScript", "console.log('test');\nconst x: string = 'hello';"),
    ("go_lang.go",        "Go",     "package main\nfunc main() {}"),
    ("ruby_lang.rb",      "Ruby",   "def my_method\n  puts 'hello'\nend"),
    ("php_short.php",     "PHP",    "<?= 'Hello' ?>"),
    ("python_imports.py", "Python", "import sys\nfrom os import path"),
    ("js_imports.js",     "JavaScript", "import React from 'react';"),
])
def test_language_detection(tmp_path, filename, expected_lang, content):
    """
    Verifies that detect_language_by_content correctly identifies the language
    based on file content and extension, handling spoofing and polyglots.
    """
    # Create the file in the temporary directory provided by pytest
    file_path = tmp_path / filename
    file_path.write_text(content, encoding="utf-8")
    
    # Run detection
    detected = detect_language_by_content(str(file_path))
    
    assert detected == expected_lang
