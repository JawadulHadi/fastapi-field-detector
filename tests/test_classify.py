import json

import httpx
import pymupdf

from field_detector.classify import LLMClassifier
from field_detector.pipeline import detect


def pdf() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((60, 700), 'Signature:', fontsize=11)
    page.draw_line((130, 702), (330, 702))
    return doc.tobytes()


def client(reply: dict | None, status=200):
    def handler(request):
        if reply is None:
            return httpx.Response(500)
        return httpx.Response(status, json={'message': {'content': json.dumps(reply)}})
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_llm_refines_role_and_marks_source():
    reply = {'fields': [{'id': 'p1-0', 'type': 'signature', 'role_key': 'owner', 'confidence': 0.99}]}
    fields = detect(pdf(), LLMClassifier(client=client(reply))).fields
    assert fields[0].role_key == 'owner' and fields[0].source == 'llm'


def test_llm_failure_falls_back_to_rules():
    fields = detect(pdf(), LLMClassifier(client=client(None))).fields
    assert fields[0].source == 'rule'


def test_llm_garbage_is_ignored():
    reply = {'fields': [{'id': 'p1-0', 'type': 'banana', 'role_key': 'x', 'confidence': 5}]}
    assert detect(pdf(), LLMClassifier(client=client(reply))).fields[0].source == 'rule'
