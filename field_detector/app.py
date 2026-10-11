from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, UploadFile

from .classify import LLMClassifier, RuleClassifier
from .models import DetectResponse
from .pipeline import PdfError, detect

MAX_BYTES = 10 * 1024 * 1024

app = FastAPI(title='Field detector', version='0.1.0')


@app.get('/health')
def health():
    return {'status': 'ok'}


@app.post('/detect', response_model=DetectResponse)
def detect_fields(file: UploadFile,
                  classifier: Annotated[str, Query(pattern='^(rules|llm)$')] = 'rules'):
    data = file.file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(413, 'file larger than 10 MB')
    if file.content_type not in ('application/pdf', 'application/octet-stream'):
        raise HTTPException(415, 'upload a PDF')
    try:
        return detect(data, LLMClassifier() if classifier == 'llm' else RuleClassifier())
    except PdfError as exc:
        raise HTTPException(422, str(exc)) from exc
