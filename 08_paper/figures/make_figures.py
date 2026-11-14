"""Paper figures (grayscale, hatching only; no colour). Recomputes every plotted number from the scored CSVs with the frozen analysis functions.

Usage (system python with matplotlib):  python 08_paper/figures/make_figures.py
Writes fig1..fig5 as PDF (for LaTeX) and PNG (for checking) into 08_paper/figures/.
"""

import importlib.util
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Rectangle  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
A = ROOT / "07_analysis"

plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"], "font.size": 8,
                     "axes.linewidth": 0.6, "pdf.fonttype": 42, "ps.fonttype": 42, "hatch.linewidth": 0.6})
COL_W, FULL_W = 3.45, 7.1
HATCH = {"C0": "", "C1": "\\\\\\\\", "C1r": "....", "C2": "xxxx", "C3": "////", "C4": ""}
FILL = {"C0": "white", "C1": "white", "C1r": "white", "C2": "white", "C3": "white", "C4": "0.25"}


def mod(name, file):
    spec = importlib.util.spec_from_file_location(name, A / file)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


S = {1: (mod("a1", "analyze_pilot.py"), A / "pilot_v1_runs.csv"), 2: (mod("a2", "analyze_study2.py"), A / "study2_runs.csv"),
     3: (mod("a3", "analyze_study3.py"), A / "study3_runs.csv")}
CELLS = {k: m.load(str(p)) for k, (m, p) in S.items()}


def share(k, cond, metric="any_violation", subset=None):
    m = S[k][0]
    vals = [v[cond] for (t, _), v in CELLS[k].items() if subset is None or subset(t)]
    return m.mean([m.METRICS[metric](r) for r in vals])


def save(fig, name):
    fig.savefig(OUT / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(OUT / f"{name}.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def box(ax, x, y, w, h, text, fill="white", fs=7, bold=False, lw=0.8, ls="-"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.0,rounding_size=0.06", fc=fill, ec="black", lw=lw, ls=ls, zorder=3))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", zorder=4, fontsize=fs, fontweight="bold" if bold else "normal", linespacing=1.15)


def arrow(ax, x1, y1, x2, y2, ls="-", style="-|>"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle=style, lw=0.8, color="black", linestyle=ls, shrinkA=0, shrinkB=0))


# ------------------------------------------------------------------ Fig 1: experimental pipeline
def fig1():
    fig, ax = plt.subplots(figsize=(FULL_W, 3.1))
    ax.set_xlim(0, 12.4)
    ax.set_ylim(0, 5.3)
    ax.axis("off")
    y = 3.6
    box(ax, 0.05, y, 1.9, 1.3, "Rule library\n11 executable\ncontracts (YAML)\nstage, check, severity", fs=6.5)
    box(ax, 0.05, y - 1.75, 1.9, 1.3, "Task set\nfeature requests,\nfixture repository,\nhidden tests", fs=6.5)
    box(ax, 2.55, y - 0.9, 1.9, 1.9, "Condition\nC0 no rules\nC1 rules in prompt\nC3 checks after\nC4 enforced during", fs=6.5, bold=False)
    box(ax, 5.05, y - 0.9, 2.1, 1.9, "Agent in sandbox\nmini-SWE-agent\nDocker, no network,\nrepo read-only,\none cheap LLM", fs=6.5)
    box(ax, 7.75, y - 0.9, 1.8, 1.9, "Run evidence\ncommands executed,\nedits applied,\nblocks, feedback", fs=6.5)
    box(ax, 10.15, y + 0.15, 2.15, 1.05, "Independent oracle\nAST, import graph,\nfile hashes, commands", fs=6.5, fill="0.9")
    box(ax, 10.15, y - 1.25, 2.15, 1.05, "Hidden tests\n(functional pass)", fs=6.5, fill="0.9")
    arrow(ax, 1.95, y + 0.65, 2.55, y + 0.35)
    arrow(ax, 1.95, y - 1.1, 2.55, y - 0.35)
    arrow(ax, 4.45, y + 0.05, 5.05, y + 0.05)
    arrow(ax, 7.15, y + 0.05, 7.75, y + 0.05)
    arrow(ax, 9.55, y + 0.4, 10.15, y + 0.65)
    arrow(ax, 9.55, y - 0.3, 10.15, y - 0.75)
    ax.text(11.22, y - 1.4, "violations and\nfunctional pass per run", ha="center", va="top", fontsize=6.5, style="italic")
    ax.text(6.1, y - 1.1, "C3 and C4 give the agent feedback, within a fixed budget;\nC4 also blocks disallowed actions before they run",
            ha="center", va="top", fontsize=6.3, style="italic")
    # study strip
    ax.plot([0.05, 12.3], [1.05, 1.05], color="black", lw=0.5)
    studies = [("Study 1 (exploratory)", "8 tasks, 6 conditions, 5 runs\n240 runs, Gemini 3.1 Flash-Lite"),
               ("Study 2 (confirmatory)", "14 tasks, 4 conditions, 2 runs\n112 runs, DeepSeek v4.1 Flash"),
               ("Study 3 (confirmatory, targeted)", "18 tasks, 3 conditions, 2 runs\n108 runs, DeepSeek v4.1 Flash")]
    for i, (h, t) in enumerate(studies):
        x0 = 0.05 + i * 4.15
        ax.add_patch(Rectangle((x0, 0.05), 3.95, 0.8, fc="white", ec="black", lw=0.6, ls=(0, (3, 2))))
        ax.text(x0 + 1.975, 0.68, h, ha="center", va="center", fontsize=6.8, fontweight="bold")
        ax.text(x0 + 1.975, 0.33, t, ha="center", va="center", fontsize=6.2, linespacing=1.1)
    ax.text(0.05, 1.15, "Each study freezes its plan, tasks, configuration and analysis script (hashed) before its first run", fontsize=6.3, style="italic", va="bottom")
    save(fig, "fig1_design")


# ------------------------------------------------------------------ Fig 2: where the rules enter in each condition
def fig2():
    fig, ax = plt.subplots(figsize=(FULL_W, 3.3))
    ax.set_xlim(-0.2, 13.6)
    ax.set_ylim(-0.9, 6.6)
    ax.axis("off")
    rows = [("C0", "no rules"), ("C1", "rules in the prompt"), ("C1r", "unrelated rules in prompt"),
            ("C2", "retrieved guidance"), ("C3", "checks after generation"), ("C4", "enforced during execution")]
    top, gap, x0 = 6.0, 1.1, 4.2
    for i, (c, desc) in enumerate(rows):
        y = top - i * gap
        ax.text(0.0, y, c, fontsize=8, fontweight="bold", va="center")
        ax.text(0.9, y, desc, fontsize=6.4, va="center", ha="left")
        ax.plot([x0 + 0.6, x0 + 9.0], [y, y], color="black", lw=0.6, zorder=1)
        box(ax, x0, y - 0.22, 0.65, 0.44, "task", fs=5.5, lw=0.6)
        xs = [x0 + 1.9, x0 + 3.2, x0 + 4.5, x0 + 5.8, x0 + 7.1]
        for x in xs:
            ax.add_patch(plt.Circle((x, y), 0.13, fc="white", ec="black", lw=0.7, zorder=3))
        box(ax, x0 + 8.55, y - 0.22, 0.95, 0.44, "submit", fs=5.5, lw=0.6)
        if c in ("C1", "C1r", "C2"):
            label = {"C1": "rules text", "C1r": "other rules", "C2": "retrieved"}[c]
            box(ax, x0 + 0.7, y + 0.1, 1.0, 0.38, label, fs=5.2, fill="0.85", lw=0.5, ls=(0, (2, 1)) if c == "C1r" else "-")
        if c == "C3":
            ax.add_patch(plt.Polygon([[x0 + 8.2, y + 0.26], [x0 + 8.38, y], [x0 + 8.2, y - 0.26], [x0 + 8.02, y]], fc="0.6", ec="black", lw=0.7, zorder=4))
            ax.annotate("", xy=(x0 + 6.0, y - 0.32), xytext=(x0 + 8.2, y - 0.32), arrowprops=dict(arrowstyle="-|>", lw=0.6, ls="--", color="black"))
            ax.text(x0 + 7.1, y - 0.5, "feedback, then revise", fontsize=5.5, ha="center", va="top")
        if c == "C4":
            for x in xs:
                ax.add_patch(plt.Polygon([[x - 0.42, y + 0.26], [x - 0.25, y], [x - 0.42, y - 0.26], [x - 0.59, y]], fc="0.6", ec="black", lw=0.6, zorder=4))
            ax.text(x0 + 4.0, y - 0.45, "a gate before every command or edit; blocked actions never run", fontsize=5.6, ha="center", va="top", style="italic")
    ly = -0.55
    ax.add_patch(plt.Circle((x0, ly), 0.13, fc="white", ec="black", lw=0.7))
    ax.text(x0 + 0.25, ly, "agent action (command or edit)", fontsize=6, va="center")
    ax.add_patch(plt.Polygon([[x0 + 4.3, ly + 0.2], [x0 + 4.45, ly], [x0 + 4.3, ly - 0.2], [x0 + 4.15, ly]], fc="0.6", ec="black", lw=0.6))
    ax.text(x0 + 4.65, ly, "executable check", fontsize=6, va="center")
    box(ax, x0 + 6.3, ly - 0.17, 0.5, 0.34, "", fill="0.85", lw=0.5)
    ax.text(x0 + 6.95, ly, "rule text shown to the model", fontsize=6, va="center")
    save(fig, "fig2_conditions")


# ------------------------------------------------------------------ Fig 3: violation share by condition and study
def fig3():
    studies = [(1, ["C0", "C1", "C1r", "C2", "C3", "C4"], "Study 1 (exploratory)"), (2, ["C0", "C1", "C3", "C4"], "Study 2"),
               (3, ["C0", "C1", "C4"], "Study 3 (targeted tasks)")]
    fig, axes = plt.subplots(1, 3, figsize=(FULL_W, 2.2), sharey=True, gridspec_kw={"width_ratios": [6, 4, 3]})
    for ax, (k, conds, title) in zip(axes, studies):
        vals = [share(k, c) for c in conds]
        n = len(CELLS[k])
        for i, (c, v) in enumerate(zip(conds, vals)):
            ax.bar(i, v, width=0.7, fc=FILL[c], ec="black", hatch=HATCH[c], lw=0.7)
            ax.text(i, v + 0.015, f"{round(v + 1e-9, 2):.2f}", ha="center", va="bottom", fontsize=6.5)
        ax.set_xticks(range(len(conds)))
        ax.set_xticklabels(conds)
        ax.set_title(f"{title}\n{n} (task, run) pairs", fontsize=7.2)
        ax.set_ylim(0, 0.68)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("Share of runs with at least\none oracle-detected violation")
    fig.tight_layout(w_pad=0.8)
    save(fig, "fig3_violations")


# ------------------------------------------------------------------ Fig 4: forest plot of the two contrasts
def fig4():
    rows = []
    for contrast, (a, b) in (("C4 vs C0", ("C4", "C0")), ("C4 vs C1", ("C4", "C1"))):
        for k in (1, 2, 3):
            m = S[k][0]
            by = m.diffs_by_task(CELLS[k], "any_violation", a, b)
            lo, hi = m.cluster_bootstrap(by)
            rows.append((f"{contrast}, Study {k}", m.point(by), lo, hi, k != 1))
    fig, ax = plt.subplots(figsize=(COL_W, 2.4))
    for i, (label, d, lo, hi, confirm) in enumerate(rows):
        y = len(rows) - 1 - i
        ax.plot([lo, hi], [y, y], color="black", lw=1.0)
        ax.plot([lo, lo], [y - 0.12, y + 0.12], color="black", lw=1.0)
        ax.plot([hi, hi], [y - 0.12, y + 0.12], color="black", lw=1.0)
        ax.plot(d, y, marker="s", ms=5, mfc="black" if confirm else "white", mec="black", mew=1.0)
    ax.axvline(0, color="black", lw=0.7, ls="--")
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in rows][::-1])
    ax.set_xlabel("Difference in share of runs with a violation\n(task-clustered 95% bootstrap interval)")
    ax.set_xlim(-0.9, 0.1)
    ax.spines[["top", "right"]].set_visible(False)
    ax.plot([], [], marker="s", ls="", mfc="black", mec="black", label="confirmatory")
    ax.plot([], [], marker="s", ls="", mfc="white", mec="black", label="exploratory")
    ax.legend(loc="lower left", fontsize=6.3, frameon=False, handletextpad=0.2)
    save(fig, "fig4_forest")


# ------------------------------------------------------------------ Fig 5: Study 3 by situation
def fig5():
    sit = [("Dynamic SQL", lambda t: 1 <= int(t.split("-")[1]) <= 6), ("Tests requested,\ntest file protected", lambda t: 7 <= int(t.split("-")[1]) <= 12),
           ("File trees,\nrecursive delete", lambda t: 13 <= int(t.split("-")[1]) <= 18)]
    conds = ["C0", "C1", "C4"]
    fig, ax = plt.subplots(figsize=(COL_W, 2.3))
    w = 0.26
    for j, c in enumerate(conds):
        for i, (name, f) in enumerate(sit):
            v = share(3, c, subset=f)
            ax.bar(i + (j - 1) * w, v, width=w * 0.92, fc=FILL[c], ec="black", hatch=HATCH[c], lw=0.7, label=c if i == 0 else None)
            ax.text(i + (j - 1) * w, v + 0.012, f"{round(v + 1e-9, 2):.2f}", ha="center", va="bottom", fontsize=6)
    ax.set_xticks(range(len(sit)))
    ax.set_xticklabels([s[0] for s in sit], fontsize=6.8)
    ax.set_ylabel("Share of runs with a violation")
    ax.set_ylim(0, 0.78)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(fontsize=6.5, frameon=False, ncol=3, loc="upper right")
    save(fig, "fig5_situations")


if __name__ == "__main__":
    for f in (fig1, fig2, fig3, fig4, fig5):
        f()
    print("figures written to", OUT)
