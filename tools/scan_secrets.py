"""Secret scanner for this repository (standard library only).

Usage:
    python tools/scan_secrets.py            scan every tracked file in the working tree
    python tools/scan_secrets.py --staged   scan only the files staged for the next commit (used by the pre-commit hook)
    python tools/scan_secrets.py --history  scan the full git history (every commit, every file version)
    python tools/scan_secrets.py --check-ignore   verify that the .gitignore rules that keep key files out are present and effective

Exit code 0 means nothing suspicious was found; 1 means findings (they are printed with the file name and the first characters only,
never the whole value). The same script runs in CI (.github/workflows/secret-scan.yml) and as a pre-commit hook (tools/hooks/pre-commit).
"""

import re
import subprocess
import sys
import tempfile
from pathlib import Path

PATTERNS = {
    "Google API key (AIza...)": re.compile(r"AIza[0-9A-Za-z_\-]{30,}"),
    "Google express-mode key (AQ.Ab8...)": re.compile(r"AQ\.Ab8[0-9A-Za-z_\-]{10,}"),
    "OpenRouter key (sk-or-v1-...)": re.compile(r"sk-or-v1-[0-9a-fA-F]{20,}"),
    "generic secret key (sk-...)": re.compile(r"\bsk-[A-Za-z0-9]{24,}"),
    "bearer token": re.compile(r"Bearer\s+[A-Za-z0-9_\-\.]{24,}"),
    "private key block": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "assigned API key literal": re.compile(r"(?i)\b(?:api[_-]?key|secret|token|password)\b\s*[:=]\s*['\"][A-Za-z0-9_\-\.]{20,}['\"]"),
    "key exported in a shell line": re.compile(r"(?i)export\s+[A-Z_]*(?:KEY|TOKEN|SECRET)[A-Z_]*=\S{16,}"),
}
REQUIRED_IGNORES = ["*.env", ".env*", "*.key", "*.pem", "secrets*", "*keys*", ".venv/"]
ROOT = Path(__file__).resolve().parents[1]


def git(*args, **kw):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, **kw)


def scan_text(label, text, findings):
    for name, rx in PATTERNS.items():
        for m in rx.finditer(text):
            findings.append((name, label, m.group(0)[:6] + "..."))


def scan_files(paths):
    findings = []
    for rel in paths:
        p = ROOT / rel
        if not p.is_file() or p.stat().st_size > 30_000_000:
            continue
        scan_text(rel, p.read_text(encoding="utf-8", errors="ignore"), findings)
    return findings


def scan_history():
    findings = []
    commits = git("rev-list", "--all").stdout.decode().split()
    for c in commits:
        files = git("ls-tree", "-r", "--name-only", c).stdout.decode(errors="ignore").splitlines()
        for f in files:
            blob = git("show", f"{c}:{f}").stdout
            if len(blob) > 30_000_000:
                continue
            scan_text(f"{c[:8]}:{f}", blob.decode("utf-8", errors="ignore"), findings)
    return findings, len(commits)


def check_ignore():
    ok = True
    text = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for rule in REQUIRED_IGNORES:
        if rule not in text.splitlines():
            print("missing .gitignore rule:", rule)
            ok = False
    # effectiveness: a throw-away key file must be ignored by git
    for name in ("gem.env", "my_api_keys.txt", "secrets.json", "server.pem", "x.key", ".env.local"):
        r = git("check-ignore", "-q", name)
        if r.returncode != 0:
            print("NOT ignored by git:", name)
            ok = False
    print("gitignore check:", "OK" if ok else "FAILED")
    return ok


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "--check-ignore":
        sys.exit(0 if check_ignore() else 1)
    if mode == "--history":
        findings, n = scan_history()
        print(f"scanned {n} commit(s) of history")
    elif mode == "--staged":
        names = git("diff", "--cached", "--name-only", "--diff-filter=ACM").stdout.decode().splitlines()
        findings = scan_files(names)
    else:
        findings = scan_files(git("ls-files").stdout.decode().splitlines())
    for name, where, head in findings[:30]:
        print(f"FOUND {name} in {where}: {head}")
    print("findings:", len(findings))
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
