import re

def detect_language_from_snippet(content, ext):
    """
    Analyzes a text snippet (content) and file extension to identify the programming language.
    
    Logic Flow:
    1. Shebang Check: Looks for #!/bin/... at the start.
    2. Priority Verification: If extension matches a known language, checks that language's regex first.
    3. General Heuristics: Scans for all language patterns (the "backup" / fallthrough).
    """
    
    # 1. Check Shebangs (Scripts)
    # Looks for interpreter directives on the first line (e.g., #!/bin/bash)
    first_line = content.split('\n')[0]
    if first_line.startswith("#!"):
        if "python" in first_line: return "Python"
        if "node" in first_line: return "JavaScript"
        if "bash" in first_line or "sh" in first_line: return "Shell"
        if "perl" in first_line: return "Perl"
        if "ruby" in first_line: return "Ruby"
        if "php" in first_line: return "PHP"

    # 2. Priority Verification (Extension Trust)
    # If the file extension strongly suggests a language, check that SPECIFIC pattern first.
    # This prevents "Polyglot" confusion (e.g., a Python file with C comments being detected as C).
    
    # Python
    if ext.lower() == ".py":
        # Matches function/class definitions or import statements
        # Added [:(\] requirement to def/class to avoid matching text like "class Summary"
        if re.search(r'^\s*(def|class)\s+\w+\s*[:\(]|^\s*import\s+\w+|^\s*from\s+\w+\s+import', content, re.MULTILINE):
            return "Python"

    # Java
    if ext.lower() == ".java":
        # Matches package declarations or public class definitions
        if re.search(r'^\s*package\s+[\w.]+;|^\s*public\s+class\s+\w+', content, re.MULTILINE):
            return "Java"

    # HTML
    if ext.lower() in (".html", ".htm"):
        # Matches HTML5 doctype or html tag
        if re.search(r'^\s*<!DOCTYPE\s+html>|^\s*<html', content, re.IGNORECASE | re.MULTILINE):
            return "HTML"

    # JavaScript / TypeScript
    if ext.lower() in (".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"):
        # Matches ES6 imports, variable declarations, or function definitions
        if re.search(r'^\s*(import\s+.*\s+from\s+[\'"]|const\s+\w+\s*=|let\s+\w+\s*=|var\s+\w+\s*=|function\s+\w+\s*\(|console\.log\()', content, re.MULTILINE):
            # Simple heuristic to distinguish TS: Looks for type annotations or interfaces
            if ext.lower() in (".ts", ".tsx"):
                return "TypeScript"
            return "JavaScript"

    # C / C++
    if ext.lower() in (".c", ".cpp", ".h", ".hpp", ".cc", ".cxx"):
        # Matches #include directives common in C/C++
        if re.search(r'^\s*#include\s+[<"]', content, re.MULTILINE):
            # Distinguishes C++ by looking for class, template, namespace, or std:: usage
            if re.search(r'\b(class|template|namespace|std::|cout|cin)\b', content):
                return "C++"
            if ext.lower() in (".cpp", ".hpp", ".cc", ".cxx"):
                return "C++"
            return "C"

    # C#
    if ext.lower() == ".cs":
        # Matches C# specific 'using System;' directive
        if re.search(r'^\s*using\s+System;', content, re.MULTILINE):
            return "C#"

    # CSS
    if ext.lower() == ".css":
        # Matches CSS rules: selector { property: value }
        if re.search(r'^\s*[.#a-zA-Z0-9_-]+\s*\{\s*[\w-]+\s*:', content, re.MULTILINE):
            return "CSS"

    # SQL
    if ext.lower() == ".sql":
        # Stricter check: Requires context like 'SELECT * FROM' or 'INSERT INTO'
        if re.search(r'\bSELECT\b[\s\S]+?\bFROM\b|\bINSERT\s+INTO\b|\bCREATE\s+TABLE\b|\bUPDATE\b[\s\S]+?\bSET\b', content, re.IGNORECASE):
            return "SQL"

    # Ruby
    if ext.lower() == ".rb":
        # Matches def, class, module keywords or require statements
        if re.search(r'^\s*(?:class|module)\s+[A-Z]\w*(?:\s*<|\s*$)|^\s*def\s+\w+|^\s*require\s+[\'"]', content, re.MULTILINE):
            return "Ruby"

    # Go
    if ext.lower() == ".go":
        # Matches 'package main' or function definitions
        if re.search(r'^\s*package\s+main|^\s*func\s+\w+', content, re.MULTILINE):
            return "Go"

    # PHP
    if ext.lower() == ".php":
        # Matches standard PHP opening tag or short echo tag
        if re.search(r'<\?(php|=)', content, re.IGNORECASE):
            return "PHP"

    # XML
    if ext.lower() == ".xml":
        # Matches standard XML declaration at start of file
        if re.search(r'^\s*<\?xml', content):
            return "XML"

    # 3. Regex Heuristics (The "Backup" / Fallthrough)
    # If priority verification failed (e.g. spoofed file) or extension was unknown, check everything.
    
    # XML
    if re.search(r'^\s*<\?xml', content): return "XML"
    
    # C / C++ / C#
    if re.search(r'^\s*#include\s+[<"]', content, re.MULTILINE):
        if re.search(r'\b(class|template|namespace|std::|cout|cin)\b', content): return "C++"
        return "C"
    if re.search(r'^\s*using\s+System;', content, re.MULTILINE): return "C#"
    
    # JS / TS (Moved up to prevent Python import confusion)
    if re.search(r'^\s*(import\s+.*\s+from\s+[\'"]|const\s+\w+\s*=|let\s+\w+\s*=|var\s+\w+\s*=|function\s+\w+\s*\(|console\.log\()', content, re.MULTILINE):
        if re.search(r':\s*(string|number|boolean|any|void)\b|interface\s+\w+', content): return "TypeScript"
        return "JavaScript"

    # Python
    if re.search(r'^\s*(def|class)\s+\w+\s*[:\(]|^\s*import\s+\w+|^\s*from\s+\w+\s+import', content, re.MULTILINE): return "Python"
    
    # Java
    if re.search(r'^\s*package\s+[\w.]+;|^\s*public\s+class\s+\w+', content, re.MULTILINE): return "Java"
    
    # Go
    if re.search(r'^\s*package\s+main|^\s*func\s+\w+', content, re.MULTILINE): return "Go"
    
    # Ruby
    if re.search(r'^\s*(?:class|module)\s+[A-Z]\w*(?:\s*<|\s*$)|^\s*def\s+\w+|^\s*require\s+[\'"]', content, re.MULTILINE): return "Ruby"
    
    # PHP
    if re.search(r'<\?php', content): return "PHP"
    
    # HTML
    if re.search(r'^\s*<!DOCTYPE\s+html>|^\s*<html', content, re.IGNORECASE | re.MULTILINE): return "HTML"
    
    # CSS
    if re.search(r'^\s*[.#a-zA-Z0-9_-]+\s*\{\s*[\w-]+\s*:', content, re.MULTILINE): return "CSS"
    
    # SQL
    if re.search(r'\bSELECT\b[\s\S]+?\bFROM\b|\bINSERT\s+INTO\b|\bCREATE\s+TABLE\b|\bUPDATE\b[\s\S]+?\bSET\b', content, re.IGNORECASE): return "SQL"

    return None
