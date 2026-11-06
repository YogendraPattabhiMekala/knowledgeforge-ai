"""Conservative English lexical evidence gate, independent of retrieval rank.

Scores are query-term coverage, NOT confidence or semantic entailment. Generic
question/policy words cannot establish a topic. Numbers and quoted phrases must
occur in the same passage; evidence is never pooled across unrelated passages.
"""

import re
from .config import settings

STOP_WORDS = set(
    """
a an the and or but what which who where when why how is are was were be been
being do does did can could would should will may might must have has had i we
our you your they their it its this that these those of to in on at by from for
with about as into under over company's company companies employee employees
employer official policy policies document documents handbook information
please tell explain describe find give get need needed apply applies applicable
many much any there regarding according say says us me require requires required
process processes procedure procedures guideline guidelines
""".split()
)


def terms(text: str) -> set[str]:
    result = set()
    for word in re.findall(r"[a-z0-9]+", text.lower()):
        if len(word) < 2 or word in STOP_WORDS:
            continue
        # Small, transparent inflection normalization; no semantic synonym claims.
        if len(word) > 4 and word.endswith("ies"):
            word = word[:-3] + "y"
        elif (
            len(word) > 3
            and word.endswith("s")
            and not word.endswith(("ss", "us", "is"))
        ):
            word = word[:-1]
        if len(word) > 6 and word.endswith("ly"):
            word = word[:-2]
        if len(word) > 5 and word.endswith("ing"):
            word = word[:-3]
        elif len(word) > 4 and word.endswith("ed"):
            word = word[:-2]
        if len(word) > 4 and word.endswith("e"):
            word = word[:-1]
        result.add(word)
    return result


def assess(question: str, passage: str) -> dict:
    wanted = terms(question)
    matched = wanted & terms(passage)
    coverage = len(matched) / len(wanted) if wanted else 0.0
    # Preserve literal numeric qualifiers, including dates, decimals and amounts.
    numbers = set(re.findall(r"(?<!\w)\d+(?:[.,]\d+)*(?!\w)", question))
    available = set(re.findall(r"(?<!\w)\d+(?:[.,]\d+)*(?!\w)", passage))
    quoted = re.findall(r'["“]([^"”]+)["”]', question)
    normalized = " ".join(passage.lower().split())
    qualifiers = numbers <= available and all(
        " ".join(phrase.lower().split()) in normalized for phrase in quoted
    )
    accepted = (
        bool(wanted)
        and any(re.search(r"[a-z]", term) for term in matched)
        and qualifiers
        and (
            len(matched) >= min(settings.relevance_min_matches, len(wanted))
            and coverage >= settings.relevance_min_coverage
        )
    )
    return {
        "accepted": accepted,
        "coverage": coverage,
        "matched": sorted(matched),
        "missing": sorted(wanted - matched),
        "qualifiers_present": qualifiers,
    }


def filter_evidence(question: str, candidates: list[dict]) -> list[dict]:
    return [item for item in candidates if assess(question, item["text"])["accepted"]]


def evidence_question(question: str, history: list[dict]) -> str:
    """Only underspecified follow-ups inherit the previous user topic.

    A specific new question must stand on its own. An isolated 'How many days?'
    can use the prior topic, rather than accepting every passage mentioning days.
    """
    topic = {term for term in terms(question) if re.search(r"[a-z]", term)}
    previous = [message["content"] for message in history if message["role"] == "user"][
        -1:
    ]
    if previous and len(topic) < 2:
        return " ".join(previous + [question])
    return question
