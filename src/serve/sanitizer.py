import re


_BLOCK_PATTERNS = [
    # <think>...</think>, <thinkl>...</thinkl>, <0think>...</0think>, etc.
    re.compile(r"(?is)<\s*([0-9]*think[\w\-]*)[^>]*>.*?</\s*\1\s*>")
    ,
    # <thinking>...</thinking>, <reasoning>...</reasoning>
    re.compile(r"(?is)<\s*(thinking|reasoning)[^>]*>.*?</\s*\1\s*>")
]

_SINGLE_TAG_PATTERNS = [
    # <think> / </think> / <think .../> variants
    re.compile(r"(?is)</?\s*[0-9]*think[\w\-]*\s*/?>")
    ,
    re.compile(r"(?is)</?\s*(thinking|reasoning)\s*/?>")
]


def sanitize_model_output(text: str) -> str:
    """Remove chain-of-thought style tags and enclosed content from model output.

    This removes blocks like <think>...</think>, <0think>...</0think>, <thinking>...</thinking>,
    and also strips any standalone opening/closing/self-closing variants of these tags.
    """
    if not text:
        return text

    cleaned = text

    # Remove paired blocks (repeat until stable in case of nested blocks)
    changed = True
    while changed:
        changed = False
        for pat in _BLOCK_PATTERNS:
            new_cleaned = pat.sub("", cleaned)
            if new_cleaned != cleaned:
                cleaned = new_cleaned
                changed = True

    # Remove any leftover single tags
    for pat in _SINGLE_TAG_PATTERNS:
        cleaned = pat.sub("", cleaned)

    # Normalize excessive whitespace around removed regions
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned.strip()


