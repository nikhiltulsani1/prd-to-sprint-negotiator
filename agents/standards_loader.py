import os


def load_standards(standards_file: str = "standards.md") -> dict:
    """
    Load team standards from optional standards.md file.
    Returns empty dict if file doesn't exist — always safe to call.
    """
    if not os.path.exists(standards_file):
        return {}

    with open(standards_file, 'r', encoding='utf-8') as f:
        content = f.read()

    return {
        "exists": True,
        "content": content,
        "raw": content,
    }
