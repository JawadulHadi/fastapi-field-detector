"""Stage 3: turn candidates into fields. Rules by default, optional local LLM refinement."""
import json
import os

import httpx
from pydantic import BaseModel, ValidationError

from .candidates import Candidate
from .models import Box, DetectedField

VALID_TYPES = {'signature', 'initials', 'date', 'name', 'checkbox', 'text'}


def _to_field(c: Candidate, role: str, kind: str, confidence: float, reason: str, source: str,
              size: tuple[float, float]) -> DetectedField:
    w, h = size
    x0, y0, x1, y1 = c.box
    return DetectedField(
        type=kind, role_key=role, page=c.page,
        box=Box(x=x0 / w, y=y0 / h, w=(x1 - x0) / w, h=(y1 - y0) / h),
        label=c.label, required=c.required, confidence=confidence, reason=reason, source=source,
    )


def assign_roles(cands: list[Candidate]) -> dict[str, str]:
    """Named roles win. Unnamed signatures become signer_1, signer_2 in reading order.
    Other unnamed fields inherit the role of the nearest signature in the same column."""
    roles: dict[str, str] = {}
    n = 0
    for c in cands:
        if c.role:
            roles[c.id] = c.role
        elif c.kind == 'signature':
            n += 1
            roles[c.id] = f'signer_{n}'
    anchors = [c for c in cands if c.id in roles and c.kind == 'signature']
    for c in cands:
        if c.id in roles:
            continue
        cx = (c.box[0] + c.box[2]) / 2
        near = [a for a in anchors if a.page == c.page and abs(a.box[3] - c.box[3]) < 120
                and a.box[0] - 40 <= cx <= a.box[2] + 40]
        near.sort(key=lambda a: abs(a.box[3] - c.box[3]))
        roles[c.id] = roles[near[0].id] if near else 'signer_1'
    return roles


class RuleClassifier:
    def classify(self, cands: list[Candidate], sizes: dict[int, tuple[float, float]]):
        roles = assign_roles(cands)
        return [_to_field(c, roles[c.id], c.kind, c.confidence, c.reason, c.source, sizes[c.page])
                for c in cands]


class _Verdict(BaseModel):
    id: str
    type: str
    role_key: str
    confidence: float


class LLMClassifier:
    """Asks a local Ollama model to confirm each candidate. Any failure falls back to rules."""

    def __init__(self, model=None, host=None, client=None):
        model = model or os.environ.get('OLLAMA_MODEL', 'llama3.2')
        host = host or os.environ.get('OLLAMA_HOST', 'http://localhost:11434')
        self.model, self.host = model, host.rstrip('/')
        self.client = client or httpx.Client(timeout=60)
        self.fallback = RuleClassifier()

    def _ask(self, cands: list[Candidate]) -> dict[str, _Verdict]:
        items = [{'id': c.id, 'label': c.label, 'context': c.context, 'guess': c.kind} for c in cands]
        prompt = ('You review form fields found in a contract. For each item return its type '
                  f'(one of {sorted(VALID_TYPES)}), the signing party role as a short lowercase key, '
                  'and your confidence 0..1. Reply as JSON: '
                  '{"fields": [{"id": "...", "type": "...", "role_key": "...", "confidence": 0.9}]}\n'
                  f'Items: {json.dumps(items)}')
        resp = self.client.post(f'{self.host}/api/chat', json={
            'model': self.model, 'stream': False, 'format': 'json',
            'options': {'temperature': 0},
            'messages': [{'role': 'user', 'content': prompt}],
        })
        resp.raise_for_status()
        data = json.loads(resp.json()['message']['content'])
        out = {}
        for row in data['fields']:
            try:
                v = _Verdict(**row)
            except ValidationError:
                continue
            if v.type in VALID_TYPES and 0 <= v.confidence <= 1:
                out[v.id] = v
        return out

    def classify(self, cands: list[Candidate], sizes: dict[int, tuple[float, float]]):
        base = self.fallback.classify(cands, sizes)
        if not cands:
            return base
        try:
            verdicts = self._ask(cands)
        except (httpx.HTTPError, KeyError, ValueError, TypeError):
            return base
        fields = []
        for c, f in zip(cands, base, strict=True):
            v = verdicts.get(c.id)
            if v is None:
                fields.append(f)
                continue
            fields.append(_to_field(c, v.role_key, v.type, round((v.confidence + c.confidence) / 2, 2),
                                    f'{c.reason}; confirmed by model', 'llm', sizes[c.page]))
        return fields
