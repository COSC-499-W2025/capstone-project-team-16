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
        return "Node.js / React"

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

    # Python & Data
    if ext == ".py":
        return "Python Development"
    if ext == ".ipynb":
        return "Data Science (Jupyter)"

    # Web & JavaScript
    if ext in (".js", ".jsx", ".mjs", ".cjs"):
        return "JavaScript Development"
    if ext in (".ts", ".tsx"):
        return "TypeScript Development"
    if ext in (".html", ".htm"):
        return "HTML / Web Markup"
    if ext in (".css", ".scss", ".sass", ".less"):
        return "CSS / Web Styling"
    if ext == ".vue":
        return "Vue.js Development"

    # Java / JVM
    if ext == ".java":
        return "Java Development"
    if ext in (".kt", ".kts"):
        return "Kotlin Development"
    if ext == ".scala":
        return "Scala Development"

    # C-Family
    if ext in (".c", ".h"):
        return "C Programming"
    if ext in (".cpp", ".hpp", ".cc", ".cxx", ".c++"):
        return "C++ Programming"
    if ext == ".cs":
        return "C# / .NET Development"

    # Systems / Backend
    if ext == ".go":
        return "Go Programming"
    if ext == ".rs":
        return "Rust Systems Programming"
    if ext == ".php":
        return "PHP Development"
    if ext == ".rb":
        return "Ruby Development"
    if ext == ".lua":
        return "Lua Scripting"

    # Database & DevOps
    if ext == ".sql":
        return "SQL / Database Management"
    if ext in (".sh", ".bash", ".zsh"):
        return "Shell Scripting & Automation"
    if ext == ".tf":
        return "Terraform / IaC"

    # Documentation
    if ext in (".md", ".markdown", ".rst", ".txt", ".pdf", ".docx"):
        return "Technical Documentation"

    return None


def skill_from_lang(lang: str, skill_map: dict = None) -> str | None:
    """
    Maps a detected language name (from language_detector) to a professional skill name.
    """
    if not lang or lang == "Unknown":
        return None
    
    l = lang.lower()
    
    # 1. Check dynamic mapping from JSON filters if provided
    if skill_map and l in skill_map:
        return skill_map[l]

    return None
