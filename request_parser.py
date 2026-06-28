"""
request_parser.py

Purpose:
    Parse an incoming email body and extract:
    1. matter number, e.g. M12205
    2. document type, e.g. Other Documents

Expected input:
    A plain text email body, such as:
    "Hi Agent, Can you give me Other Documents files from M12205? Thanks!"

Expected output:
    A dictionary like:
    {
        "matter_number": "M12205",
        "document_type": "Other Documents",
    }
"""

import re
from difflib import SequenceMatcher


# The exact document types supported by the challenge.
CANONICAL_DOCUMENT_TYPES = [
    "Exhibits",
    "Key Documents",
    "Other Documents",
    "Transcripts",
    "Recordings",
]


# Common ways a user might refer to each document type.
# The key is the phrase we search for; the value is the official document type.
DOCUMENT_TYPE_ALIASES = {
    "exhibit": "Exhibits",
    "exhibits": "Exhibits",

    "key document": "Key Documents",
    "key documents": "Key Documents",
    "key doc": "Key Documents",
    "key docs": "Key Documents",

    "other document": "Other Documents",
    "other documents": "Other Documents",
    "other doc": "Other Documents",
    "other docs": "Other Documents",

    "transcript": "Transcripts",
    "transcripts": "Transcripts",

    "recording": "Recordings",
    "recordings": "Recordings",
}


def normalize_text(text: str) -> str:
    """
    Makes text easier to compare.

    Example:
        "Other Documents, please!" -> "other documents please"
    """
    text = text.lower()

    # Replace punctuation/symbols with spaces.
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    # Collapse repeated spaces.
    text = re.sub(r"\s+", " ", text).strip()

    return text


def extract_matter_number(text: str) -> str | None:
    """
    Extracts a matter number from the email body.

    Matter numbers are expected to look like:
        M12205
        M12383

    This also accepts small variations like:
        m12205
        M 12205
        M-12205

    Returns:
        "M12205" if found, otherwise None.
    """
    match = re.search(r"\bM[\s-]*(\d+)\b", text, re.IGNORECASE)

    if not match:
        return None

    digits = match.group(1)
    return f"M{digits}"


def generate_ngrams(words: list[str], max_size: int = 3) -> list[str]:
    """
    Creates short phrases from the email body so we can fuzzy-match typos.

    Example:
        words = ["please", "send", "other", "docmets"]
        ngrams include:
            "please"
            "send"
            "other"
            "docmets"
            "please send"
            "send other"
            "other docmets"

    This helps catch:
        "Other Docmets" -> "Other Documents"
    """
    phrases = []

    for size in range(1, max_size + 1):
        for i in range(len(words) - size + 1):
            phrase = " ".join(words[i:i + size])
            phrases.append(phrase)

    return phrases


def fuzzy_document_type_match(normalized_text: str) -> tuple[str | None, str | None, float]:
    """
    Attempts to match document type even if there is a typo.

    Example:
        "other docmets" should still match "Other Documents".

    Returns:
        (document_type, matched_phrase, confidence)

    If no good match:
        (None, None, 0.0)
    """
    words = normalized_text.split()
    possible_phrases = generate_ngrams(words, max_size=3)

    best_document_type = None
    best_matched_phrase = None
    best_score = 0.0

    # Compare each short phrase from the email against each known alias.
    for phrase in possible_phrases:
        for alias, canonical_type in DOCUMENT_TYPE_ALIASES.items():
            score = SequenceMatcher(None, phrase, alias).ratio()

            if score > best_score:
                best_score = score
                best_document_type = canonical_type
                best_matched_phrase = phrase

    # Threshold controls how aggressive typo-correction is.
    # 0.80 is strict enough to avoid most random false matches,
    # but still catches simple typos like "docmets".
    if best_score >= 0.80:
        return best_document_type, best_matched_phrase, best_score

    return None, None, 0.0


def extract_document_type(text: str) -> tuple[str | None, str | None, float]:
    """
    Extracts the document type from an email body.

    First:
        Uses exact/simple alias matching.

    Then:
        Uses fuzzy matching for small typos.

    Returns:
        (document_type, matched_phrase, confidence)

    Example:
        "Can I get other docs from M12205?"
        -> ("Other Documents", "other docs", 1.0)
    """
    normalized = normalize_text(text)

    # 1. Exact alias matching first.
    # This is more predictable than fuzzy matching.
    for alias, canonical_type in DOCUMENT_TYPE_ALIASES.items():
        if alias in normalized:
            return canonical_type, alias, 1.0

    # 2. Fuzzy matching fallback.
    return fuzzy_document_type_match(normalized)


def parse_request(email_body: str) -> dict:
    """
    Main function used by the rest of the agent.

    Input:
        email_body: string from the user's email

    Output:
        dictionary containing parsed fields and validation result
    """
    matter_number = extract_matter_number(email_body)
    document_type, matched_phrase, confidence = extract_document_type(email_body)

    errors = []

    if matter_number is None:
        errors.append("Missing or invalid matter number. Expected format like M12205.")

    if document_type is None:
        errors.append(
            "Missing or invalid document type. Expected one of: "
            + ", ".join(CANONICAL_DOCUMENT_TYPES)
            + "."
        )

    return {
        "matter_number": matter_number,
        "document_type": document_type,
        "is_valid": len(errors) == 0,
        "errors": errors,
        "matched_document_phrase": matched_phrase,
        "document_confidence": round(confidence, 2),
    }


# Run this file directly to test the parser:
#     python src/request_parser.py
if __name__ == "__main__":
    test_inputs = [
        "Hi Agent, Can you give me Other Documents files from M12205? Thanks!",
        "Please send key docs for m12383.",
        "Can you get Other Docmets from M12205?",
        "Need transcripts from M99999 please.",
        "Send recordings for M-12205.",
        "Can you send files from M12205?",
        "Can you send invoices from M12205?",
        "Need Exhibits for matter M12383.",
    ]

    for text in test_inputs:
        print("=" * 80)
        print("INPUT:")
        print(text)
        print("\nOUTPUT:")
        print(parse_request(text))