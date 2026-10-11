"""Stage 4: clamp, drop junk, resolve overlaps, and warn about gaps."""
from .models import DetectedField


def iou(a, b) -> float:
    ax1, ay1, bx1, by1 = a.x + a.w, a.y + a.h, b.x + b.w, b.y + b.h
    iw = max(0.0, min(ax1, bx1) - max(a.x, b.x))
    ih = max(0.0, min(ay1, by1) - max(a.y, b.y))
    inter = iw * ih
    union = a.w * a.h + b.w * b.h - inter
    return inter / union if union else 0.0


def clean(fields: list[DetectedField]) -> tuple[list[DetectedField], list[str]]:
    kept: list[DetectedField] = []
    for f in sorted(fields, key=lambda f: -f.confidence):
        b = f.box
        b.x, b.y = max(0.0, b.x), max(0.0, b.y)
        b.w, b.h = min(b.w, 1 - b.x), min(b.h, 1 - b.y)
        if b.w < 0.01 or b.h < 0.004:
            continue
        if any(k.page == f.page and iou(k.box, b) > 0.5 for k in kept):
            continue
        kept.append(f)
    kept.sort(key=lambda f: (f.page, round(f.box.y, 3), f.box.x))
    warnings = []
    roles = {f.role_key for f in kept}
    signers = {f.role_key for f in kept if f.type == 'signature'}
    for role in sorted(roles - signers):
        warnings.append(f'role {role!r} has fields but no signature field')
    for f in kept:
        if f.confidence < 0.6:
            warnings.append(f'low confidence ({f.confidence}) {f.type} on page {f.page}: needs review')
    if not kept:
        warnings.append('no fields detected')
    return kept, warnings
