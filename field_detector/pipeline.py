import pymupdf

from .candidates import generate
from .classify import LLMClassifier, RuleClassifier
from .extract import extract_page
from .models import DetectResponse
from .validate import clean

MAX_PAGES = 50


class PdfError(ValueError):
    pass


def detect(pdf: bytes, classifier=None) -> DetectResponse:
    classifier = classifier or RuleClassifier()
    if not pdf.startswith(b'%PDF'):
        raise PdfError('not a PDF file')
    try:
        doc = pymupdf.open(stream=pdf, filetype='pdf')
    except Exception as exc:
        raise PdfError(f'cannot open PDF: {exc}') from exc
    if doc.page_count > MAX_PAGES:
        raise PdfError(f'too many pages (max {MAX_PAGES})')
    cands, sizes = [], {}
    for i, page in enumerate(doc, start=1):
        data = extract_page(page, i)
        sizes[i] = (data.width, data.height)
        cands += generate(data)
    fields, warnings = clean(classifier.classify(cands, sizes))
    return DetectResponse(pages=doc.page_count, fields=fields, warnings=warnings)


__all__ = ['detect', 'PdfError', 'LLMClassifier', 'RuleClassifier']
