from __future__ import annotations

import re
from typing import Any

from pipeline_common import normalize_spaces


def comparable_street_name(value: Any) -> str:
    text = normalize_spaces(value)
    text = text.replace("\u05f4", "").replace("\u05f3", "").replace('"', "").replace("'", "")
    text = text.replace("\u2019", "").replace("`", "")
    words = re.sub(r"[\s.,:/(){}\[\]\-_*]+", " ", text).split()
    if words and words[0] in {"\u05e8\u05d7", "\u05e8\u05d7\u05d5\u05d1"}:
        words = words[1:]
    if words and words[0] == "\u05e9\u05d3":
        words[0] = "\u05e9\u05d3\u05e8\u05d5\u05ea"
    if words and words[0] == "\u05e9\u05db":
        words[0] = "\u05e9\u05db\u05d5\u05e0\u05d4"
    return "".join(sorted(words))
