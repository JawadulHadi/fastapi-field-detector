import pymupdf
import pytest

from field_detector.pipeline import PdfError, detect


def make_pdf(draw) -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    draw(page)
    return doc.tobytes()


def test_finds_signature_with_ruled_line():
    def draw(page):
        page.insert_text((60, 700), 'Client Signature:', fontsize=11)
        page.draw_line((190, 702), (340, 702))
    result = detect(make_pdf(draw))
    sig = next(f for f in result.fields if f.type == 'signature')
    assert sig.role_key == 'client' and sig.confidence >= 0.9 and sig.source == 'rule'


def test_sentence_with_keyword_is_not_a_field():
    def draw(page):
        page.insert_text((60, 700), 'Please sign here only after reading the whole agreement.', fontsize=11)
    assert detect(make_pdf(draw)).fields == []


def test_label_without_line_is_low_confidence_guess():
    def draw(page):
        page.insert_text((60, 700), 'Signature:', fontsize=11)
    result = detect(make_pdf(draw))
    assert result.fields[0].source == 'rule-guess'
    assert any('needs review' in w for w in result.warnings)


def test_checkbox_detected_and_optional():
    def draw(page):
        page.draw_rect(pymupdf.Rect(60, 600, 70, 610))
        page.insert_text((80, 609), 'I agree to the terms', fontsize=10)
    box = detect(make_pdf(draw)).fields[0]
    assert box.type == 'checkbox' and box.required is False


def test_date_inherits_role_of_nearest_signature():
    def draw(page):
        page.insert_text((60, 600), 'Tenant Signature:', fontsize=11)
        page.draw_line((190, 602), (340, 602))
        page.insert_text((60, 640), 'Date:', fontsize=11)
        page.draw_line((100, 642), (220, 642))
    fields = {f.type: f for f in detect(make_pdf(draw)).fields}
    assert fields['date'].role_key == 'tenant'


def test_boxes_are_normalised_inside_page():
    def draw(page):
        page.insert_text((60, 700), 'Signature:', fontsize=11)
        page.draw_line((130, 702), (330, 702))
    for f in detect(make_pdf(draw)).fields:
        assert 0 <= f.box.x <= 1 and 0 <= f.box.y <= 1
        assert f.box.x + f.box.w <= 1.0001 and f.box.y + f.box.h <= 1.0001


def test_rejects_non_pdf():
    with pytest.raises(PdfError):
        detect(b'hello')
