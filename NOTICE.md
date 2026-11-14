# Third-party notices

This repository does not redistribute third-party code. It depends on open-source tools installed from their own sources, each under its own license:

- mini-swe-agent (https://github.com/SWE-agent/mini-swe-agent), MIT license; used as the agent scaffold (version 2.4.6). Its README asks users to cite the SWE-agent paper (Yang et al., NeurIPS 2024).
- The other Python dependencies are listed with exact versions in `03_framework/requirements.lock` and keep their own licenses.
- The sandbox image is built from the public `python:3.12-slim` image and installs pytest and ruff from PyPI (see `03_framework/sandbox/Dockerfile`).

Model outputs in the run logs were produced by Gemini 3.1 Flash-Lite (Study 1) and DeepSeek v4.1 Flash via OpenRouter (Studies 2 and 3). The respective providers' terms apply to those services; the logs are released for scientific reproduction of the analysis.
