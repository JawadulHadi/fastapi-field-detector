# Changelog

All notable changes to fastapi-field-detector. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). The project has no version tags yet, so
past entries are grouped by merged pull request and date.

Every change adds an entry under **Unreleased** in the same pull request. CI checks this.

## [Unreleased]

### Added
- Vercel deployment: `vercel.json`, `.vercelignore`, `.python-version` (3.12) and the
  `[tool.vercel]` entrypoint in `pyproject.toml`.
- `docs/deployment.md`, covering Vercel, its 4.5 MB upload limit, and the Render fallback.
- `tests/test_deploy_config.py`, which checks the Vercel entrypoint resolves to the FastAPI app.
- `CHANGELOG.md` (this file), a pull request template, and a CI job that fails a pull request
  which doesn't update the changelog. Label a PR `skip-changelog` to bypass it.

### Changed
- README "Deploy (free)" now points at Vercel. Render and the Dockerfile stay as a fallback.

### Security
- The `changelog` CI workflow now limits its token to read-only repository access.

## PR #2 (2026-10-12)

### Added
- First real `NOTES.md` entries.

## PR #1 (2026-10-11)

### Added
- Architecture diagram in the README, a Render free-tier blueprint, `Dockerfile`, MIT license and
  `.env.example`.
- CI: ruff, pytest, and the synthetic eval with an F1 gate of 0.9.

## Initial commits (2026-10-11)

### Added
- FastAPI service that detects signature, initials, date, name and checkbox fields in PDFs:
  PyMuPDF extraction, rule-based candidates and classifier, optional local LLM classifier with
  rule fallback, validation, and a synthetic eval harness.
