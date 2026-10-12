# Deployment

The field detector deploys to **Vercel** (Python runtime, FastAPI preset). It needs no database and
no secrets. The Render blueprint and the `Dockerfile` stay in the repo as a fallback (see
[Render](#render-fallback)).

| Piece | Where | Config |
| --- | --- | --- |
| API | One Vercel Function running the FastAPI app | `vercel.json`, `[tool.vercel]` in `pyproject.toml`, `.python-version` |
| LLM classifier (optional) | Any reachable Ollama | `OLLAMA_HOST`, `OLLAMA_MODEL` |

## Vercel

1. In Vercel: **Add New → Project**, import `JawadulHadi/fastapi-field-detector`. The FastAPI
   preset is detected; leave the build settings empty.
2. Deploy. Vercel installs the dependencies from `pyproject.toml` on Python 3.12 and serves
   `field_detector.app:app` (set in `[tool.vercel] entrypoint`).
3. Smoke test:

   ```bash
   curl https://<project>.vercel.app/health
   curl -F 'file=@eval/samples/01_two_party.pdf;type=application/pdf' https://<project>.vercel.app/detect
   ```

`vercel.json` gives the function 30 seconds and leaves `tests/`, `eval/` and docs out of the bundle.

### Limits on Vercel

- **Uploads above 4.5 MB are rejected by Vercel** with 413 before they reach the app, because that
  is the platform's request body limit. The app's own limit is 10 MB, which still applies on
  Render and locally.
- Functions start cold after idle time, so the first request is slower (about a second, not the
  ~30 s Render free wake-up).
- `?classifier=llm` needs an Ollama the function can reach. Vercel has none, so set `OLLAMA_HOST`
  to a reachable host or the request falls back to rules (as it does everywhere without Ollama).

## Render (fallback)

`render.yaml` is a blueprint for a Render free web service built from the `Dockerfile`. In Render:
**New → Blueprint**, pick this repo. Health check is `GET /health`. Free instances sleep after about
15 minutes idle.

## Local

```bash
pip install -e '.[dev]'
uvicorn field_detector.app:app --reload
```
