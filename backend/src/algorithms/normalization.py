"""Attribute canonicalisation and similarity primitives.

Shared by both real algorithms:
  * SCD2 zipper  -> decides whether a value really changed (after normalisation);
  * conflict merge -> decides whether a cross-source disagreement is cosmetic,
    similar, or a true conflict needing a human decision.

Design notes
------------
* Phone numbers: strip every non digit, then drop a leading 86 country code.
* Org codes: a small mapping table folds the three upstream spellings
  (``ORG-BJ01`` / ``BJ01`` / ``华北一区``) into one canonical code.
* Names: homophone detection uses a curated, tone-stripped pinyin table
  (see ``PINYIN``). Unknown characters fall back to themselves — documented
  as a known simplification in TESTING.md.
"""
from __future__ import annotations

import re
from difflib import SequenceMatcher

_PHONE_NON_DIGIT = re.compile(r"[^0-9]")
_ORG_PREFIX = re.compile(r"^ORG[-_ ]?", re.IGNORECASE)

ORG_FORMS: dict[str, tuple[str, ...]] = {
    "BJ01": ("ORG-BJ01", "BJ01", "华北一区", "北京分公司"),
    "SH02": ("ORG-SH02", "SH02", "华东二区", "上海分公司"),
    "GZ03": ("ORG-GZ03", "GZ03", "华南三区", "广州分公司"),
    "CD04": ("ORG-CD04", "CD04", "西南四区", "成都分公司"),
}

ORG_MAP: dict[str, str] = {
    form.upper(): canonical for canonical, forms in ORG_FORMS.items() for form in forms
}

# Tone-stripped pinyin for the characters used by the demo customer names.
PINYIN: dict[str, str] = {
    "王": "wang", "李": "li", "张": "zhang", "刘": "liu", "陈": "chen",
    "杨": "yang", "赵": "zhao", "黄": "huang", "周": "zhou", "吴": "wu",
    "徐": "xu", "孙": "sun", "马": "ma", "朱": "zhu", "胡": "hu",
    "郭": "guo", "何": "he", "高": "gao", "林": "lin", "罗": "luo",
    "嘉": "jia", "佳": "jia", "禾": "he", "和": "he", "子": "zi",
    "墨": "mo", "默": "mo", "雨": "yu", "羽": "yu", "桐": "tong",
    "彤": "tong", "思": "si", "远": "yuan", "源": "yuan", "若": "ruo",
    "溪": "xi", "希": "xi", "振": "zhen", "宇": "yu", "晚": "wan",
    "晴": "qing", "清": "qing", "书": "shu", "舒": "shu", "言": "yan",
    "宁": "ning", "凝": "ning", "云": "yun", "知": "zhi", "明": "ming",
    "敏": "min", "俊": "jun", "杰": "jie", "伟": "wei", "静": "jing",
    "婷": "ting", "欣": "xin", "悦": "yue", "一": "yi",
}


def canonical_phone(value: object) -> str:
    digits = _PHONE_NON_DIGIT.sub("", str(value or ""))
    if len(digits) == 13 and digits.startswith("86"):
        digits = digits[2:]
    return digits


def canonical_org(value: object) -> str:
    text = str(value or "").strip().upper().replace(" ", "")
    if text in ORG_MAP:
        return ORG_MAP[text]
    stripped = _ORG_PREFIX.sub("", text)
    if stripped in ORG_MAP:
        return ORG_MAP[stripped]
    return stripped


def canonical_text(value: object) -> str:
    return str(value or "").strip()


def pinyin_of(text: str) -> str:
    return "".join(PINYIN.get(char, char) for char in text)


def canonical_value(normalization: str, value: object) -> str:
    """Return the comparison/storage form for one attribute value."""
    if value is None:
        return ""
    if normalization == "phone_digits":
        return canonical_phone(value)
    if normalization == "org_code_map":
        return canonical_org(value)
    return canonical_text(value)


def similarity(normalization: str, left: object, right: object) -> float:
    """0..1 similarity used to decide 'same value, different spelling'."""
    a = canonical_text(left)
    b = canonical_text(right)
    if a == b:
        return 1.0
    if normalization == "phone_digits":
        da, db = canonical_phone(a), canonical_phone(b)
        if da and da == db:
            return 1.0
        return 0.0
    if normalization == "org_code_map":
        ca, cb = canonical_org(a), canonical_org(b)
        return 1.0 if ca and ca == cb else 0.0
    if normalization == "name_homophone":
        pa, pb = pinyin_of(a), pinyin_of(b)
        if pa and pa == pb:
            return 1.0
        return round(SequenceMatcher(None, pa, pb).ratio(), 4)
    return 0.0
