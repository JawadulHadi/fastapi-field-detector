# Notes: mistakes and fixes

## 2026-10-11: CI "failed" in 3 seconds with no logs

**What happened:** The first CI runs went red in 2 to 3 seconds. `gh run view --log-failed` returned "log not found", which made it look like a broken workflow file.
**Root cause:** Not the code or the workflow. The run annotation said the job was not started because the GitHub account was locked over a billing issue, so no step ever ran.
**Fix:** Once the account lock was cleared, re-ran the checks. CI then passed on the same workflow with no changes to it.
**What I would do differently:** Read the run annotations (`gh run view <id>`) before touching the workflow. A red check that finishes in seconds with no logs is an account or runner problem, not a test failure.

## 2026-10-11: The whole project was committed one folder too deep

**What happened:** The first commit (18b0347) put everything under `fastapi-field-detector/` inside the repo, including `.github/workflows/ci.yml`. GitHub only reads workflows from `.github/` at the repo root, so CI was never wired up, and the README's `pip install -e .` instructions did not work from a fresh clone.
**Root cause:** The repo was initialised one level above the project folder, so the folder itself became the first path segment.
**Fix:** Moved every file up to the repo root (commit 3f563b6).
**What I would do differently:** After the first push, open the repo on GitHub and check that `.github/` and `README.md` sit at the top level before anything else.
