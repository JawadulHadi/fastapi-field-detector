FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY pyproject.toml README.md ./
COPY field_detector ./field_detector
RUN pip install .
RUN useradd --create-home app
USER app
EXPOSE 8000
# Render (and most hosts) inject PORT; default to 8000 locally.
CMD ["sh", "-c", "uvicorn field_detector.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
