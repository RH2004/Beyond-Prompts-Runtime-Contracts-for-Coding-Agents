"""Agreement between reviewers and the oracle.

Usage:  python 06_evaluation/review/agreement.py <returned_dir> <out.md>
  <returned_dir> holds reviewer_A.csv, reviewer_B.csv, reviewer_M.csv (any subset, at least two). Letters are anonymous ids.
Reads the private key (06_evaluation/review/private/key.csv). Values: 0 not violated, 1 violated, 9 cannot tell (excluded, counted).

Reported before any discussion between reviewers: pairwise Cohen's kappa and raw agreement (a) per (packet, rule) decision and
(b) per packet "any violation"; agreement of the reviewers' majority with the oracle; every disagreement listed.
"""

import csv
import itertools
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RULES = ["ARCH-LAYER-001", "SEC-EVAL-001", "PERM-PATH-001", "PERM-CMD-001", "SEC-SQL-001", "SEC-SECRET-001", "SEC-SHELL-001"]


def kappa(a, b):
    n = len(a)
    if n == 0:
        return None, None
    po = sum(x == y for x, y in zip(a, b)) / n
    pa1, pb1 = sum(a) / n, sum(b) / n
    pe = pa1 * pb1 + (1 - pa1) * (1 - pb1)
    return po, (None if pe == 1 else (po - pe) / (1 - pe))


def fmt(x):
    return "n/a" if x is None else f"{x:.2f}"


def load(path):
    out = {}
    for r in csv.DictReader(open(path, encoding="utf-8")):
        out[r["packet"]] = {k: (int(r[k]) if str(r[k]).strip() in ("0", "1", "9") else None) for k in RULES}
    return out


def main():
    ret, outp = Path(sys.argv[1]), Path(sys.argv[2])
    key = {r["packet"]: r for r in csv.DictReader(open(HERE / "private" / "key.csv", encoding="utf-8"))}
    revs = {p.stem.split("_")[1]: load(p) for p in sorted(ret.glob("reviewer_*.csv"))}
    names = list(revs)
    packets = sorted(key)
    L = ["# Reviewer agreement (computed before any discussion)\n", f"Reviewers: {', '.join(names)}; packets: {len(packets)}.\n"]
    # decisions
    dec = {n: {} for n in names}
    anyv = {n: {} for n in names}
    cant = {n: 0 for n in names}
    for n in names:
        for p in packets:
            row = revs[n].get(p, {})
            vals = []
            for r in RULES:
                v = row.get(r)
                if v == 9 or v is None:
                    cant[n] += 1
                else:
                    dec[n][(p, r)] = v
                    vals.append(v)
            if len(vals) == len(RULES):
                anyv[n][p] = int(any(vals))
    L.append("## Cannot-tell / missing cells\n\n" + ", ".join(f"{n}: {cant[n]}" for n in names) + "\n")
    L.append("## Pairwise agreement\n\n| Pair | level | n | raw agreement | Cohen's kappa |\n|---|---|---|---|---|")
    for x, y in itertools.combinations(names, 2):
        cells = sorted(set(dec[x]) & set(dec[y]))
        po, k = kappa([dec[x][c] for c in cells], [dec[y][c] for c in cells])
        L.append(f"| {x} vs {y} | rule decisions | {len(cells)} | {fmt(po)} | {fmt(k)} |")
        ps = sorted(set(anyv[x]) & set(anyv[y]))
        po, k = kappa([anyv[x][p] for p in ps], [anyv[y][p] for p in ps])
        L.append(f"| {x} vs {y} | packet any-violation | {len(ps)} | {fmt(po)} | {fmt(k)} |")
    # oracle
    orc = {(p, r): (1 if key[p][f"oracle_{r}"] == "fail" else 0) for p in packets for r in RULES}
    orc_any = {p: int(key[p]["oracle_any_violation"]) for p in packets}
    L.append("\n## Each reviewer against the oracle\n\n| Reviewer | level | n | raw agreement | Cohen's kappa |\n|---|---|---|---|---|")
    for n in names:
        cells = sorted(dec[n])
        po, k = kappa([dec[n][c] for c in cells], [orc[c] for c in cells])
        L.append(f"| {n} | rule decisions | {len(cells)} | {fmt(po)} | {fmt(k)} |")
        ps = sorted(anyv[n])
        po, k = kappa([anyv[n][p] for p in ps], [orc_any[p] for p in ps])
        L.append(f"| {n} | packet any-violation | {len(ps)} | {fmt(po)} | {fmt(k)} |")
    # majority vs oracle
    maj = {}
    for c in orc:
        votes = [dec[n][c] for n in names if c in dec[n]]
        if len(votes) >= 2 and sum(votes) * 2 != len(votes):
            maj[c] = int(sum(votes) * 2 > len(votes))
    cells = sorted(maj)
    po, k = kappa([maj[c] for c in cells], [orc[c] for c in cells])
    L.append(f"\n## Majority of reviewers against the oracle\n\nn = {len(cells)} decisions with a clear majority; raw agreement {fmt(po)}; kappa {fmt(k)}.\n")
    L.append("## Disagreements between the majority and the oracle (examine each)\n\n| Packet | Rule | oracle | reviewers (" + ", ".join(names) + ") | task | condition |\n|---|---|---|---|---|---|")
    for c in cells:
        if maj[c] != orc[c]:
            p, r = c
            votes = "/".join(str(dec[n].get(c, "-")) for n in names)
            L.append(f"| {p} | {r} | {orc[c]} | {votes} | {key[p]['task']} | {key[p]['condition']} |")
    L.append("\n## Disagreements between reviewers (any pair)\n\n| Packet | Rule | " + " | ".join(names) + " |\n|---|---|" + "---|" * len(names))
    for c in sorted(orc):
        v = [dec[n].get(c) for n in names]
        present = [x for x in v if x is not None]
        if len(set(present)) > 1:
            L.append(f"| {c[0]} | {c[1]} | " + " | ".join("-" if x is None else str(x) for x in v) + " |")
    outp.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[:20]))


if __name__ == "__main__":
    main()
