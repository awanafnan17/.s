"""Parsers for official result-list PDFs used by the PDF Name Comparison tool.

Two known layouts are supported:

- ``name_only`` (CSS/FPSC "Annex-A" style):
  Merit No. | Roll No. | Name of Candidate | Domicile | Group | Remarks.
  There is no father-name column, and long names wrap onto a second line.

- ``with_father_name`` (PPSC/ECP style):
  Either a single column "Name of Candidate with Father's Name" joined by
  S/O / D/O / W/O markers, or separate Name and Father Name columns
  (which PyPDF2 flattens into one run of words per row).

Anything else is treated as ``unknown`` and handled by the caller's
generic line-based fallback.
"""

import re
from typing import Dict, List, Optional

FORMAT_NAME_ONLY = 'name_only'
FORMAT_WITH_FATHER = 'with_father_name'
FORMAT_UNKNOWN = 'unknown'

# Tokens that mark the end of the name portion of a row (domicile /
# group / remarks columns). Compared uppercase.
NON_NAME_KEYWORDS = {
    # Domiciles / regions
    'PUNJAB', 'SINDH', 'SINDH(R)', 'SINDH(U)', 'KPK', 'KHYBER',
    'PAKHTUNKHWA', 'BALOCHISTAN', 'BALUCHISTAN', 'AJK', 'AZAD', 'JAMMU',
    'KASHMIR', 'GILGIT', 'BALTISTAN', 'GB', 'ISLAMABAD', 'ICT', 'FATA',
    'TRIBAL', 'AREAS', 'RURAL', 'URBAN', 'CAPITAL', 'TERRITORY',
    # Group / remarks / table words
    'GENERAL', 'MINORITY', 'MINORITIES', 'WOMEN', 'DISABLED', 'QUALIFIED',
    'PROVISIONALLY', 'PASS', 'PASSED', 'FAIL', 'FAILED', 'ABSENT',
    'GROUP', 'REMARKS', 'DOMICILE', 'MERIT', 'ROLL', 'CANDIDATE',
    'CANDIDATES', 'NAME', 'FATHER', 'FATHERS', "FATHER'S", 'NO', 'NO.',
    'SR', 'SR.', 'S#', 'APP', 'APPLICATION', 'PAGE', 'TOTAL', 'RESULT',
    'LIST', 'ANNEX-A', 'ANNEX',
}

# S/O, D/O, W/O, "son of", "daughter of", "wife of"
FATHER_SEPARATOR_RE = re.compile(
    r'\b(?:s\s*/\s*o|d\s*/\s*o|w\s*/\s*o|son\s+of|daughter\s+of|wife\s+of)\b[.:]?',
    re.IGNORECASE,
)

# A row starts with a merit/serial number, optionally followed by a
# roll/application number (digits, possibly with - or /).
ROW_START_RE = re.compile(r'^\s*(\d{1,7})[.)]?\s+([A-Za-z]{0,4}[-/]?\d[\d\-/]*)?\s*(.*)$')

NAME_TOKEN_RE = re.compile(r"^[A-Za-z][A-Za-z\-.']*$")


def _normalize_wrapped_slashes(text: str) -> str:
    """Join wrapped-name slashes ("ZEESHAN / ALTAF" -> "ZEESHAN ALTAF").

    Single-letter slash pairs (S/O, D/O, W/O) are preserved because they
    are father-name separators, not line-wrap artifacts.
    """
    return re.sub(r'\b([A-Za-z]{2,})\s*/\s*([A-Za-z]{2,})\b', r'\1 \2', text)


def _is_name_token(token: str) -> bool:
    stripped = token.strip('.,;:()')
    if not stripped or not NAME_TOKEN_RE.match(stripped):
        return False
    return stripped.upper() not in NON_NAME_KEYWORDS


def _take_name_tokens(tokens: List[str]) -> List[str]:
    """Take leading tokens that look like name parts, stopping at the
    first column keyword (domicile/group/remarks) or non-alpha token."""
    name: List[str] = []
    for token in tokens:
        if not _is_name_token(token):
            break
        name.append(token.strip('.,;:()'))
    return name


def detect_pdf_format(text: str) -> str:
    """Classify extracted PDF text as one of the two known result layouts."""
    lowered = text.lower()
    if FATHER_SEPARATOR_RE.search(lowered) or 'father' in lowered:
        return FORMAT_WITH_FATHER
    if 'domicile' in lowered and ('merit' in lowered or 'roll' in lowered):
        return FORMAT_NAME_ONLY
    return FORMAT_UNKNOWN


def _split_name_and_father(text: str) -> Dict[str, Optional[str]]:
    """Split "ALI RAZA S/O MUHAMMAD ASLAM ..." into name and father name."""
    match = FATHER_SEPARATOR_RE.search(text)
    if not match:
        name = _take_name_tokens(text.split())
        return {'name': ' '.join(name), 'father_name': None}
    name = _take_name_tokens(text[:match.start()].split())
    father = _take_name_tokens(text[match.end():].split())
    return {
        'name': ' '.join(name),
        'father_name': ' '.join(father) or None,
    }


def extract_candidates(text: str) -> List[Dict]:
    """Extract candidate rows from result-PDF text.

    Returns a list of dicts:
        name         -- candidate name (may be '' if a row had no usable name)
        father_name  -- father's name or None (name_only format never has one)
        roll_no      -- roll/application number string or None
        raw_line     -- the source line(s), for display/logging
        combined     -- every name-like word on the row (name + father blob);
                        used for subset matching when columns can't be split
    """
    pdf_format = detect_pdf_format(text)
    text = _normalize_wrapped_slashes(text)
    lines = [ln.strip() for ln in text.split('\n') if ln.strip()]

    candidates: List[Dict] = []
    last_candidate_line_idx = -2
    for idx, line in enumerate(lines):
        row = ROW_START_RE.match(line)
        if not row:
            # Possible wrapped continuation of the previous row's name: a
            # short run of name tokens with no leading number, immediately
            # following a candidate row. Trailing column words (domicile /
            # group / remarks) are allowed after the name tokens.
            tokens = line.split()
            extra_tokens = _take_name_tokens(tokens)
            if (
                candidates
                and idx == last_candidate_line_idx + 1
                and 1 <= len(extra_tokens) <= 3
                and all(not _is_name_token(t) for t in tokens[len(extra_tokens):])
            ):
                prev = candidates[-1]
                extra = ' '.join(extra_tokens)
                if prev['father_name'] is not None:
                    prev['father_name'] = f"{prev['father_name']} {extra}".strip()
                else:
                    prev['name'] = f"{prev['name']} {extra}".strip()
                prev['combined'] = f"{prev['combined']} {extra}".strip()
                prev['raw_line'] = f"{prev['raw_line']} / {line}"
                last_candidate_line_idx = idx
            continue

        _merit_no, roll_no, rest = row.groups()
        if not rest:
            continue

        if pdf_format == FORMAT_WITH_FATHER:
            parts = _split_name_and_father(rest)
        else:
            parts = {'name': ' '.join(_take_name_tokens(rest.split())), 'father_name': None}

        combined = ' '.join(t.strip('.,;:()') for t in rest.split() if _is_name_token(t))
        if not parts['name'] and not combined:
            continue

        candidates.append({
            'name': parts['name'],
            'father_name': parts['father_name'],
            'roll_no': roll_no,
            'raw_line': line,
            'combined': combined,
        })
        last_candidate_line_idx = idx

    return candidates
