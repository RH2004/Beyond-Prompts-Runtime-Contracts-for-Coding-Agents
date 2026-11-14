# Secrets policy

This repository contains no API keys, tokens or passwords, and none must ever be added.

- Model API keys are read only from environment variables at run time (`GEMINI_KEYS`, see `README.md`) and are never written to files in the repository.
- `.gitignore` excludes key and credential files (`*.env`, `*.key`, `*.pem`, `secrets*`, `*keys*`, and others).
- `tools/scan_secrets.py` detects key-like strings. It runs on every push and pull request (`.github/workflows/secret-scan.yml`), over the working tree and the full history, and it can run as a pre-commit hook (`git config core.hooksPath tools/hooks`).

If you find a credential in this repository, please report it to the contact in `COMMERCIAL.md`.
