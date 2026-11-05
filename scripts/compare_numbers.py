"""Compare the numbers in two text spans in reading order, e.g. a table in the
paper's LaTeX source against the same table retyped in the explainer.

Usage:
    python -I compare_numbers.py <file>[:<start>-<end>] <file>[:<start>-<end>]

Line ranges are 1-based and inclusive; choose them to cover the table rows (or
whatever text should carry the same numbers). Before extracting numbers the
script drops LaTeX comments and layout arguments: column specs, lengths and
spacing, \\cite/\\ref/\\label keys, colours, and the counts in \\multicolumn,
\\multirow and \\cmidrule; then it drops the remaining command names, so a
number written right after a command (45.2$\\pm$0.3, \\pm0.5) is still read.
Numbers are then compared with a diff, so one
missing or extra value does not misalign the rest; every difference is shown
with its line numbers in both files.

Exit status: 0 identical, 2 differences found, 1 usage error.
"""
import difflib
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

LAYOUT = [
    r"(?<!\\)%.*",
    r"\\begin\{(?:tabular\*?|tabularx|longtable|array)\}(?:\{[^{}]*\})?\{(?:[^{}]|\{[^{}]*\})*\}",
    r"\\(?:multicolumn|multirow)\{[^}]*\}\{[^}]*\}",
    r"\\(?:cmidrule|cline)(?:\([^)]*\))?\{[^}]*\}",
    r"\\(?:hspace|vspace|rule|setlength|addlinespace|arraystretch|resizebox|scalebox)\*?(?:\{[^{}]*\})+",
    r"\\renewcommand\{\\arraystretch\}\{[^}]*\}",
    r"\\\\\[[^\]]*\]",
    r"\\(?:cite\w*|ref|eqref|label|url|href|textcolor|color|cellcolor|rowcolor|definecolor)\{[^}]*\}",
    r"\[[^\]]*\]\{[^}]*\}",  # optional-argument forms such as \resizebox[..]{..}
    r"\d*\.?\d+(?:pt|em|ex|cm|mm|in)\b",
    r"[\d.]*\\(?:linewidth|textwidth|columnwidth|tabcolsep)",
    # Any remaining command name; otherwise "\pm0.3" would lose its 0.3 to the rule below.
    r"\\[A-Za-z]+\*?",
    r"\b[A-Za-z]+\d+[A-Za-z]*\b",  # identifiers such as ser1, row2
]
# A minus sign counts only when it is not a hyphen inside a name such as CIFAR-10.
NUMBER = re.compile(r"(?<![\w.])-?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?")


def load(spec: str) -> tuple[str, list[tuple[str, int]]]:
    m = re.match(r"^(.*?)(?::(\d+)-(\d+))?$", spec)
    path, a, b = Path(m.group(1)), m.group(2), m.group(3)
    drive = re.match(r"^/([a-zA-Z])/(.*)$", m.group(1))  # Git Bash style /c/Users/...
    if not path.exists() and drive:
        path = Path(f"{drive.group(1).upper()}:/{drive.group(2)}")
    if not path.is_file():
        print(f"File not found: {m.group(1)}")
        sys.exit(1)
    lines = path.read_text(encoding="utf-8", errors="replace").split("\n")
    start = int(a) if a else 1
    end = int(b) if b else len(lines)
    out = []
    for no in range(start, min(end, len(lines)) + 1):
        text = lines[no - 1].replace("−", "-").replace("{,}", ",").replace("$", "")
        for pat in LAYOUT:
            text = re.sub(pat, " ", text)
        out.extend((n.replace(",", ""), no) for n in NUMBER.findall(text))
    return f"{path.name}:{start}-{end}", out


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return 1
    name_a, nums_a = load(sys.argv[1])
    name_b, nums_b = load(sys.argv[2])
    print(f"A = {name_a}: {len(nums_a)} numbers")
    print(f"B = {name_b}: {len(nums_b)} numbers")
    va, vb = [n for n, _ in nums_a], [n for n, _ in nums_b]
    diffs = 0
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(a=va, b=vb, autojunk=False).get_opcodes():
        if op == "equal":
            continue
        diffs += 1
        left = " ".join(f"{n}(line {ln})" for n, ln in nums_a[i1:i2]) or "(none)"
        right = " ".join(f"{n}(line {ln})" for n, ln in nums_b[j1:j2]) or "(none)"
        print(f"  {op}: A {left}  ->  B {right}")
    print("Identical." if not diffs else f"{diffs} difference(s).")
    return 2 if diffs else 0


if __name__ == "__main__":
    sys.exit(main())
