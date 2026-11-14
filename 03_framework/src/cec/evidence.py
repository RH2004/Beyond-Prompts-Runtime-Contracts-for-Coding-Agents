"""Append-only JSONL evidence log, one file per run (decisions 0010, 0016)."""

import hashlib
import json
import time
from pathlib import Path


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sha256_obj(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


class EvidenceLog:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._seq = 0

    def event(self, type_: str, **fields) -> dict:
        self._seq += 1
        rec = {"seq": self._seq, "ts": time.time(), "type": type_, **fields}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, default=str) + "\n")
        return rec

    def read(self) -> list[dict]:
        if not self.path.exists():
            return []
        return [json.loads(l) for l in self.path.read_text(encoding="utf-8").splitlines() if l.strip()]
