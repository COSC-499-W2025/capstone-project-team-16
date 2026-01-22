# Handles file classification logic:
# - activity type (code, test, docs, design)
# - framework detection
# - skill inference from extensions


def detect_activity(category: str, filename: str) -> str:
    low = filename.lower()

    # test files
    if (
        "test" in low
        or low.endswith((".spec.js", ".test.js", ".test.py", ".spec.ts"))
    ):
        return "test"

    if category == "documentation":
        return "documentation"

    if category == "assets":
        return "design"

    return "code"


def detect_framework(filename: str) -> str:
    fn = filename.lower()

    if "package.json" in fn:
        return "Node / React"

    if "requirements.txt" in fn or "pyproject.toml" in fn:
        return "Python (requirements)"

    if "pom.xml" in fn:
        return "Java (Maven)"

    if "build.gradle" in fn:
        return "Java/Kotlin (Gradle)"

    if "cargo.toml" in fn:
        return "Rust (Cargo)"

    return "None"


def skill_from_ext(ext: str):
    ext = ext.lower()

    if ext == ".py":
        return "Python Programming"

    if ext in (".js", ".ts", ".jsx", ".tsx"):
        return "JavaScript / Frontend"

    if ext in (".html", ".css"):
        return "Web Dev"

    if ext == ".java":
        return "Java Stuff"

    if ext in (".md", ".pdf", ".docx", ".txt"):
        return "Docs / Writing"

    return None
