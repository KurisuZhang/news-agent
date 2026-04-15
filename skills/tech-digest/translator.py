from __future__ import annotations
import re
import time
import requests

_CACHE: dict[str, str] = {}
_API = "https://translate.googleapis.com/translate_a/single"


def _is_chinese(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def translate_to_zh(text: str, retries: int = 2) -> str:
    """Translate text to Simplified Chinese. Returns original on failure.
    Skips translation if text already contains Chinese characters."""
    if not text or _is_chinese(text):
        return text
    if text in _CACHE:
        return _CACHE[text]

    params = {
        "client": "gtx",
        "sl": "auto",
        "tl": "zh-CN",
        "dt": "t",
        "q": text,
    }
    for attempt in range(retries):
        try:
            resp = requests.get(_API, params=params, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            result = "".join(seg[0] for seg in data[0] if seg[0])
            _CACHE[text] = result
            return result
        except Exception:
            if attempt < retries - 1:
                time.sleep(0.5)
    return text  # fallback: return original
