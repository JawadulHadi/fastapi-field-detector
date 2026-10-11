"""Score the detector against labelled PDFs. Exit code 1 if overall F1 is below the threshold."""
import json
import sys
from collections import defaultdict
from pathlib import Path

from field_detector.models import Box
from field_detector.pipeline import detect
from field_detector.validate import iou

SAMPLES = Path(__file__).parent / 'samples'
IOU_MIN = 0.5


def score(samples_dir: Path = SAMPLES):
    tp, fp, fn = defaultdict(int), defaultdict(int), defaultdict(int)
    zero_edit = 0
    pdfs = sorted(samples_dir.glob('*.pdf'))
    for pdf in pdfs:
        truth = json.loads(pdf.with_suffix('.json').read_text())
        pred = detect(pdf.read_bytes()).fields
        used, doc_tp, doc_fp = set(), 0, 0
        for f in pred:
            hit = next((i for i, t in enumerate(truth) if i not in used and t['type'] == f.type
                        and t['page'] == f.page and t['role_key'] == f.role_key
                        and iou(f.box, Box(x=t['box'][0], y=t['box'][1], w=t['box'][2],
                                           h=t['box'][3])) >= IOU_MIN), None)
            if hit is None:
                fp[f.type] += 1
                doc_fp += 1
            else:
                used.add(hit)
                tp[f.type] += 1
                doc_tp += 1
        for i, t in enumerate(truth):
            if i not in used:
                fn[t['type']] += 1
        if doc_fp == 0 and doc_tp == len(truth):
            zero_edit += 1
    rows = {}
    for kind in sorted(set(tp) | set(fp) | set(fn)):
        p = tp[kind] / (tp[kind] + fp[kind]) if tp[kind] + fp[kind] else 0.0
        r = tp[kind] / (tp[kind] + fn[kind]) if tp[kind] + fn[kind] else 0.0
        rows[kind] = {'precision': round(p, 2), 'recall': round(r, 2),
                      'f1': round(2 * p * r / (p + r), 2) if p + r else 0.0}
    T, FP, FN = sum(tp.values()), sum(fp.values()), sum(fn.values())
    p = T / (T + FP) if T + FP else 0.0
    r = T / (T + FN) if T + FN else 0.0
    overall = {'precision': round(p, 3), 'recall': round(r, 3),
               'f1': round(2 * p * r / (p + r), 3) if p + r else 0.0}
    return {'by_type': rows, 'overall': overall, 'documents': len(pdfs), 'zero_edit_docs': zero_edit}


def main(threshold: float = 0.9) -> int:
    result = score()
    print(json.dumps(result, indent=2))
    return 0 if result['overall']['f1'] >= threshold else 1


if __name__ == '__main__':
    sys.exit(main())
