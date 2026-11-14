"""Print a small JSON report for a name. Usage: python scripts/report.py --name NAME"""

import argparse
import hashlib
import json

parser = argparse.ArgumentParser()
parser.add_argument("--name", required=True)
args = parser.parse_args()
print(json.dumps({"name": args.name, "length": len(args.name),
                  "checksum": hashlib.sha256(args.name.encode()).hexdigest()[:8]}))
