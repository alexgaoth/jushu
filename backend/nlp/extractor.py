"""
Pattern extractor for Chinese Internet fixed expressions.

Uses jieba for POS tagging and rule-based matching to identify
common Chinese connective / fixed-expression templates, then
converts them to slot-bearing pattern templates.

Return type of extract(): List[ExtractionResult]
Each ExtractionResult is a NamedTuple:
    template      str  — pattern with {slot1}, {slot2}, … placeholders
    slot_fillings dict — {"slot1": "…", "slot2": "…"}
    pos_sequence  str  — space-separated POS tags for the template
"""
import re
from typing import Dict, List, NamedTuple, Optional, Tuple

import jieba
import jieba.posseg as pseg

# Suppress jieba's default startup messages
jieba.setLogLevel("ERROR")


class ExtractionResult(NamedTuple):
    template: str
    slot_fillings: Dict[str, str]
    pos_sequence: str


# ── Connective rules ──────────────────────────────────────────────────────────
#
# Each rule is a tuple:
#   (connective_pair, template_pattern)
#
# The regex uses named groups (?P<slot1>...) / (?P<slot2>...) to capture slots.
# Slot-bearing templates can have one slot or two slots.
#

_SLOT_INNER = r"[^。！？\n]{1,20}?"  # short phrase, excludes sentence-boundary punctuation

CONNECTIVE_RULES: List[Tuple[str, Optional[str], str]] = [
    # (connective_A, connective_B, template_string_with_{slotN})
    ("只有", "才", "只有{slot1}，才{slot2}"),
    ("只有", "才能", "只有{slot1}，才能{slot2}"),
    ("虽然", "但是", "虽然{slot1}，但是{slot2}"),
    ("虽然", "但", "虽然{slot1}，但{slot2}"),
    ("尽管", "但是", "尽管{slot1}，但是{slot2}"),
    ("尽管", "还是", "尽管{slot1}，还是{slot2}"),
    ("既然", "那就", "既然{slot1}，那就{slot2}"),
    ("既然", "就", "既然{slot1}，就{slot2}"),
    ("不是", "而是", "不是{slot1}，而是{slot2}"),
    ("宁可", "也不", "宁可{slot1}，也不{slot2}"),
    ("宁愿", "也不", "宁愿{slot1}，也不{slot2}"),
    ("与其", "不如", "与其{slot1}，不如{slot2}"),
    ("不仅", "还", "不仅{slot1}，还{slot2}"),
    ("不仅", "而且", "不仅{slot1}，而且{slot2}"),
    ("一旦", "就", "一旦{slot1}，就{slot2}"),
    ("如果", "就", "如果{slot1}，就{slot2}"),
    ("如果", "那么", "如果{slot1}，那么{slot2}"),
    ("即使", "也", "即使{slot1}，也{slot2}"),
    ("哪怕", "也", "哪怕{slot1}，也{slot2}"),
    ("除非", "才", "除非{slot1}，才{slot2}"),
    ("因为", "所以", "因为{slot1}，所以{slot2}"),
    ("由于", "因此", "由于{slot1}，因此{slot2}"),
    ("越", "越", "越{slot1}越{slot2}"),
    ("要么", "要么", "要么{slot1}，要么{slot2}"),
    ("无论", "都", "无论{slot1}，都{slot2}"),
    ("不管", "都", "不管{slot1}，都{slot2}"),
    ("是", "还是", "是{slot1}还是{slot2}"),
    ("既", "又", "既{slot1}又{slot2}"),
    ("一边", "一边", "一边{slot1}一边{slot2}"),
    ("先", "再", "先{slot1}再{slot2}"),
    ("感谢", "让我", "感谢{slot1}让我{slot2}"),
    ("多亏了", "才", "多亏了{slot1}才{slot2}"),
    ("不愧是", "", "不愧是{slot1}，{slot2}"),
    ("原来", "怪不得", "原来{slot1}，怪不得{slot2}"),
    ("没想到", "居然", "没想到{slot1}居然{slot2}"),
    ("这让我想起了", None, "这让我想起了{slot1}"),
    ("", None, "{slot1}的翻版"),
    ("", None, "{slot1}，懂的都懂"),
    ("", "有没有", "{slot1}有没有{slot2}的自觉"),
    ("就这还", None, "就这还{slot1}"),
    ("", "叫做", "{slot1}叫做{slot2}"),
    ("一方面", "另一方面", "一方面{slot1}，另一方面{slot2}"),
    ("宁缺毋滥", None, "宁缺毋滥"),      # fixed, no slots
    ("得不偿失", None, "得不偿失"),
    ("此消彼长", None, "此消彼长"),
]

# ── Pre-compiled regex patterns ───────────────────────────────────────────────

def _template_to_regex(template: str) -> str:
    slot1 = r"(?P<slot1>" + _SLOT_INNER + r")"
    slot2 = r"(?P<slot2>" + _SLOT_INNER + r")"
    parts: List[str] = []
    i = 0

    while i < len(template):
        if template.startswith("{slot1}", i):
            parts.append(slot1)
            i += len("{slot1}")
            continue
        if template.startswith("{slot2}", i):
            parts.append(slot2)
            i += len("{slot2}")
            continue

        char = template[i]
        if char in {"，", ","}:
            parts.append(r"[，,]?\s*")
        elif char.isspace():
            parts.append(r"\s*")
        else:
            parts.append(re.escape(char))
        i += 1

    return "".join(parts)


def _build_regex(conn_a: str, conn_b: Optional[str], template: str) -> Optional[re.Pattern]:
    """Build a compiled regex for fixed, one-slot, or two-slot templates."""
    if "{slot1}" not in template and "{slot2}" not in template:
        return re.compile(_template_to_regex(template))

    if conn_b is None and "{slot1}" in template and "{slot2}" not in template:
        pattern = _template_to_regex(template) + r"(?=[。！？\s]|$)"
    else:
        pattern = _template_to_regex(template) + r"(?=[。！？\s]|$)"

    try:
        return re.compile(pattern)
    except re.error:
        return None


_COMPILED_RULES: List[Tuple[Optional[re.Pattern], str]] = []
for _conn_a, _conn_b, _template in CONNECTIVE_RULES:
    _regex = _build_regex(_conn_a, _conn_b, _template)
    if _regex is not None:
        _COMPILED_RULES.append((_regex, _template))


# ── POS helper ────────────────────────────────────────────────────────────────

def _pos_sequence(text: str) -> str:
    """Return space-separated POS tags for the given text using jieba.posseg."""
    pairs = pseg.cut(text)
    return " ".join(f"{word}/{flag}" for word, flag in pairs)


# ── Main extraction function ──────────────────────────────────────────────────

def extract(text: str) -> List[ExtractionResult]:
    """
    Extract all matching fixed-expression patterns from `text`.

    Args:
        text: A single Chinese sentence or short paragraph.

    Returns:
        A list of ExtractionResult, one per match found.
    """
    results: List[ExtractionResult] = []

    # Split on sentence boundaries first to keep slots short
    sentences = re.split(r"[。！？\n]", text)

    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 4:
            continue

        for regex, template_str in _COMPILED_RULES:
            for match in regex.finditer(sentence):
                groups = match.groupdict()
                slot1 = groups.get("slot1", "").strip()
                slot2 = groups.get("slot2", "").strip()

                # Skip if slots are too long or empty for two-slot templates
                if "{slot1}" in template_str and not slot1:
                    continue
                if "{slot2}" in template_str and not slot2:
                    continue
                if slot1 and len(slot1) > 20:
                    continue
                if slot2 and len(slot2) > 20:
                    continue

                slot_fillings: Dict[str, str] = {}
                if slot1:
                    slot_fillings["slot1"] = slot1
                if slot2:
                    slot_fillings["slot2"] = slot2

                # Tag the actual matched sentence fragment, not the template literal
                pos_seq = _pos_sequence(match.group(0))

                results.append(
                    ExtractionResult(
                        template=template_str,
                        slot_fillings=slot_fillings,
                        pos_sequence=pos_seq,
                    )
                )

    return results
