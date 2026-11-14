"""Print a URL slug for a title as JSON. Usage: python scripts/slug.py --title TITLE"""

import argparse
import json
import re

parser = argparse.ArgumentParser()
parser.add_argument("--title", required=True)
args = parser.parse_args()
print(json.dumps({"slug": re.sub(r"[^a-z0-9]+", "-", args.title.lower()).strip("-")}))
