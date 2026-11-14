"""Print the size and SHA-256 of a file as JSON. Usage: python scripts/digest.py --file PATH"""

import argparse
import hashlib
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--file", required=True)
args = parser.parse_args()
data = Path(args.file).read_bytes()
print(json.dumps({"file": args.file, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}))
