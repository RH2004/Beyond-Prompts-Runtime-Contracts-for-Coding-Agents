"""Static checks of main.tex: dashes, unescaped percent signs, labels, citations, approximate length."""
import re
from pathlib import Path

s = (Path(__file__).resolve().parents[1] / "main.tex").read_text(encoding="utf-8")
lines = s.splitlines()
body = "\n".join(l for l in lines if not l.lstrip().startswith("%"))
print("unicode em dashes:", body.count("\u2014"), "| triple hyphens:", body.count("---"))
bad = []
for i, l in enumerate(lines, 1):
    if l.lstrip().startswith("%"):
        continue
    stripped = re.sub(r"\\texttt\{[^}]*\}", "", l)
    if re.search(r"(?<!\\)%", stripped.split(" % ")[0]):
        bad.append((i, l[:90]))
print("possible unescaped percent outside comments:", bad[:6])
labels = set(re.findall(r"\\label\{([^}]+)\}", s))
refs = set(re.findall(r"\\ref\{([^}]+)\}", s))
print("refs without label:", refs - labels, "| labels never referenced:", labels - refs)
cites = {c.strip() for m in re.findall(r"\\cite\{([^}]+)\}", s) for c in m.split(",")}
bib = set(re.findall(r"\\bibitem\{([^}]+)\}", s))
print("cited without bibitem:", cites - bib, "| bibitem never cited:", bib - cites)
words = re.sub(r"\\[a-zA-Z]+\*?", " ", re.sub(r"\\begin\{thebibliography\}.*", "", body, flags=re.S))
print("approx words before the bibliography:", len(words.split()))
