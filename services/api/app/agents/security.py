import re

INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+instructions", re.I),
    re.compile(r"export\s+(the\s+)?(customer|user).*(database|emails?)", re.I),
    re.compile(r"reveal\s+(your\s+)?(system|developer)\s+prompt", re.I),
    re.compile(r"send\s+.*(credentials|secrets|api\s*keys?)", re.I),
]


def inspect_untrusted_text(text: str) -> list[str]:
    return [pattern.pattern for pattern in INJECTION_PATTERNS if pattern.search(text)]
