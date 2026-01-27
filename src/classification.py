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


def get_skill(ext: str, lang: str = None, skill_map: dict = None, ext_map: dict = None) -> str | None:
    """
    Determines the professional skill based on language (priority) or extension.
    Uses the provided maps to look up skills dynamically.
    """
    ext = ext.lower()

    # 1. Priority: Verified Language
    if lang and lang != "Unknown" and skill_map:
        l = lang.lower()
        if l in skill_map:
            return skill_map[l]

    # 2. Fallback: Derive language from extension (if maps provided)
    if ext and ext_map and skill_map:
        derived_lang = ext_map.get(ext)
        if derived_lang:
            l = derived_lang.lower()
            if l in skill_map:
                return skill_map[l]

    return None
