import pymupdf
from fastapi.testclient import TestClient

from field_detector.app import app

client = TestClient(app)


def pdf() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((60, 700), 'Client Signature:', fontsize=11)
    page.draw_line((190, 702), (340, 702))
    return doc.tobytes()


def test_health():
    assert client.get('/health').json() == {'status': 'ok'}


def test_detect_returns_fields():
    r = client.post('/detect', files={'file': ('a.pdf', pdf(), 'application/pdf')})
    assert r.status_code == 200
    body = r.json()
    assert body['pages'] == 1 and body['fields'][0]['type'] == 'signature'


def test_rejects_non_pdf_content():
    r = client.post('/detect', files={'file': ('a.pdf', b'not a pdf', 'application/pdf')})
    assert r.status_code == 422


def test_rejects_wrong_content_type():
    r = client.post('/detect', files={'file': ('a.txt', pdf(), 'text/plain')})
    assert r.status_code == 415


def test_rejects_oversized_file():
    big = b'%PDF' + b'0' * (10 * 1024 * 1024 + 10)
    r = client.post('/detect', files={'file': ('a.pdf', big, 'application/pdf')})
    assert r.status_code == 413


def test_bad_classifier_param():
    r = client.post('/detect?classifier=magic', files={'file': ('a.pdf', pdf(), 'application/pdf')})
    assert r.status_code == 422
