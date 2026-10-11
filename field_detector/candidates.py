"""Stage 2: cheap, deterministic candidate generation from labels, lines and squares."""
import re
from dataclasses import dataclass

from .extract import PageData, Word

KINDS = [  # first match wins, order matters
    ('initials', re.compile(r'\binitials?\b', re.I)),
    ('signature', re.compile(r'\b(signature|signed|sign here|sign)\b', re.I)),
    ('date', re.compile(r'\bdate\b', re.I)),
    ('name', re.compile(r'\b(printed name|print name|full name|name)\b', re.I)),
]
ROLE_WORDS = ['client', 'contractor', 'company', 'employee', 'employer', 'landlord', 'tenant',
              'witness', 'buyer', 'seller', 'customer', 'vendor']
HEIGHT = {'signature': 32, 'initials': 24, 'date': 18, 'name': 18}
MAX_LABEL_CHARS = 40


@dataclass
class Candidate:
    id: str
    page: int
    kind: str
    label: str
    role: str | None
    box: tuple[float, float, float, float]  # points: x0, y0, x1, y1
    confidence: float
    reason: str
    context: str
    source: str = 'rule'
    required: bool = True


def _kind(text: str) -> str | None:
    for name, pattern in KINDS:
        if pattern.search(text):
            return name
    return None


def _role(text: str) -> str | None:
    low = text.lower()
    return next((r for r in ROLE_WORDS if r in low), None)


def _fill_region(page: PageData, seg: list[Word], next_x0: float):
    """Find the line or underscore run the label points at."""
    underscores = [w for w in seg if len(w.text) >= 4 and set(w.text) == {'_'}]
    label_words = [w for w in seg if w not in underscores]
    if underscores:
        u = underscores[0]
        return label_words, (u.x0, u.x1, u.y1 - 1), 'underscore run next to label'
    x1 = max(w.x1 for w in seg)
    y0, y1 = min(w.y0 for w in seg), max(w.y1 for w in seg)
    best = None
    for ln in page.lines:
        if y0 - 2 <= ln.y <= y1 + 8 and x1 - 10 <= ln.x0 <= min(x1 + 80, next_x0):
            if best is None or ln.x0 < best.x0:
                best = ln
    if best:
        return label_words, (best.x0, best.x1, best.y), 'ruled line next to label'
    return label_words, None, None


def generate(page: PageData) -> list[Candidate]:
    cands: list[Candidate] = []
    segs = sorted(page.segments, key=lambda s: (round(s[0].y0), s[0].x0))
    for seg in segs:
        text = ' '.join(w.text for w in seg)
        label_text = ' '.join(w.text for w in seg if set(w.text) != {'_'}).strip()
        kind = _kind(label_text)
        if not kind or len(label_text) > MAX_LABEL_CHARS:
            continue
        same_row = [s for s in segs if s is not seg and abs(s[0].y0 - seg[0].y0) < 4
                    and s[0].x0 > seg[-1].x1]
        next_x0 = min((s[0].x0 for s in same_row), default=page.width)
        _, region, why = _fill_region(page, seg, next_x0)
        has_colon = ':' in label_text
        if region is None and not has_colon:
            continue  # a plain word in a sentence, not a form label
        h = HEIGHT[kind]
        if region:
            x0, x1, y = region
            box = (x0, y - h, x1, y)
            conf, reason, src = 0.9, f'{kind} label with {why}', 'rule'
        else:
            x0 = seg[-1].x1 + 6
            y1 = max(w.y1 for w in seg)
            box = (x0, y1 - h, min(x0 + 150, page.width - 20), y1)
            conf, reason, src = 0.5, f'{kind} label with no visible line, position guessed', 'rule-guess'
        cands.append(Candidate(f'p{page.number}-{len(cands)}', page.number, kind, label_text,
                               _role(label_text), box, conf, reason, text, src))

    for sq in page.squares:
        words = [w for seg in page.segments for w in seg
                 if abs((w.y0 + w.y1) / 2 - (sq.y0 + sq.y1) / 2) < 8 and 0 <= w.x0 - sq.x1 <= 40]
        if not words:
            continue
        first = words[0]
        tail = [w for seg in page.segments for w in seg
                if abs(w.y0 - first.y0) < 4 and w.x0 >= first.x0]
        label = ' '.join(w.text for w in sorted(tail, key=lambda w: w.x0))[:60]
        cands.append(Candidate(f'p{page.number}-{len(cands)}', page.number, 'checkbox', label,
                               None, (sq.x0, sq.y0, sq.x1, sq.y1), 0.8,
                               'empty square next to text', label, 'rule', required=False))
    return cands
