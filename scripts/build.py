"""Compile a paper explainer (main.tex + sections/) with XeLaTeX and report problems.

Usage:
    python build.py <explainer_dir> [--build-dir DIR] [--runs 3] [--out NAME.pdf]

The sources (main.tex, other top-level .tex/.sty/.bib files, sections/, figures/)
are copied into the build directory, so auxiliary files never land in the
explainer folder. After compiling, the script reports the page count, overfull
boxes with their source file and lines, content that runs off the page (floats
taller than the page, unbreakable boxes taller than the text area), undefined
references, citations and links (\\hyperref, which \\peq uses), multiply defined
labels, headings whose math or commands garble the PDF bookmarks (use
\\texorpdfstring), and missing glyphs. With --out the PDF is copied into the
explainer folder under that name.

Exit status: 0 clean, 2 compiled but has problems to fix, 1 compilation failed.
"""
import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

SOURCE_SUFFIXES = {".tex", ".sty", ".cls", ".bib", ".bst"}
SOURCE_DIRS = ("sections", "figures")

# "(path" opens a file and the matching ")" closes it; other parentheses in the log are balanced.
PAREN = re.compile(r"\(([^\s()]*/[^\s()]*)|\(|\)")
OVERFULL = re.compile(r"^Overfull \\([hv])box \(([\d.]+)pt too (?:wide|high)\) (.*?) at lines? (\d+)(?:--(\d+))?")
BOX_WARNING = re.compile(r"^(?:Over|Under)full \\[hv]box")
WHERE = {"in paragraph": "paragraph", "in alignment": "table or alignment", "detected": "formula or box"}
# "Hyper reference" is hyperref's warning for \hyperref[label]{…}, which \peq uses.
UNDEFINED = re.compile(r"LaTeX Warning: (Reference|Citation|Hyper reference) [`'](.+?)' on page (\d+) undefined on input line (\d+)")
FLOAT_TALL = re.compile(r"LaTeX Warning: Float too large for page by ([\d.]+)pt on input line (\d+)")
PAGE_OVERFULL = re.compile(r"^Overfull \\vbox \(([\d.]+)pt too high\) has occurred while \\output is active")
MULTIPLY = re.compile(r"LaTeX Warning: Label [`'](.+?)' multiply defined")
MISSING = re.compile(r"Missing character: There is no (.+?) in font ([^:!]+)")
PAGES = re.compile(r"Output written on .*?\((\d+) pages?")
ERROR = re.compile(r"^(\./[^:]+:\d+: |! )")


def copy_sources(src: Path, build: Path) -> None:
    build.mkdir(parents=True, exist_ok=True)
    for name in SOURCE_DIRS:
        shutil.rmtree(build / name, ignore_errors=True)
        if (src / name).is_dir():
            shutil.copytree(src / name, build / name)
    for f in src.iterdir():
        if f.is_file() and f.suffix.lower() in SOURCE_SUFFIXES:
            shutil.copy2(f, build / f.name)


def run_xelatex(build: Path, runs: int) -> int:
    """Run xelatex `runs` times; return 0 on success or the failing run number."""
    # Unwrapped log lines keep every warning on one line, which the parser relies on.
    env = dict(os.environ, max_print_line="10000", error_line="254", half_error_line="238")
    cmd = ["xelatex", "-interaction=nonstopmode", "-halt-on-error", "-file-line-error", "main.tex"]
    for i in range(1, runs + 1):
        with open(build / f"run{i}.out", "wb") as out:
            r = subprocess.run(cmd, cwd=build, stdout=out, stderr=subprocess.STDOUT, env=env)
        if r.returncode != 0:
            return i
    return 0


def show_errors(lines: list[str]) -> None:
    shown = 0
    for i, line in enumerate(lines):
        if ERROR.match(line):
            print("\n".join(lines[i:i + 4]))
            print("---")
            shown += 1
            if shown == 5:
                break
    if not shown:
        print("\n".join(lines[-25:]))


def report(lines: list[str]) -> int:
    stack: list[str | None] = []  # files being read; None marks an ordinary parenthesis

    def track(text: str) -> None:
        for m in PAREN.finditer(text):
            if m.group(0) == ")":
                if stack:
                    stack.pop()
            else:
                stack.append(m.group(1))

    def current() -> str:
        own = [f for f in stack if f and f.startswith("./")]
        return own[-1][2:] if own else "main.tex"

    overfull, offpage, undefined, multiply, missing, bookmarks = [], [], [], set(), {}, set()
    pages = "?"
    rerun = False
    skipping = False  # box warnings are followed by a dump of the box contents up to a blank line
    bookmark_file = None
    for line in lines:
        if skipping:
            skipping = bool(line.strip())
            continue
        m = OVERFULL.match(line)
        if m:
            kind, amount, where, a, b = m.groups()
            span = f"{a}-{b}" if b else a
            size = "wide" if kind == "h" else "high"
            overfull.append(f"{current()}:{span}  {kind}box {amount}pt too {size} ({WHERE.get(where, where)})")
        m = PAGE_OVERFULL.match(line)
        if m:
            offpage.append(f"around {current()}  content {m.group(1)}pt past the bottom of the page "
                           "(an unbreakable box or formula is too tall)")
        m = FLOAT_TALL.search(line)
        if m:
            offpage.append(f"{current()}:{m.group(2)}  float {m.group(1)}pt taller than the page")
        if BOX_WARNING.match(line):
            skipping = True
            continue
        for pat in (UNDEFINED, MULTIPLY, MISSING):
            m = pat.search(line)
            if m:
                break
        track(line[:m.start()] if m else line)
        if m and m.re is UNDEFINED:
            what, key, page, inp = m.groups()
            kind = {"Reference": "reference", "Citation": "citation", "Hyper reference": "link"}[what]
            undefined.append(f"{kind} {key} (page {page}, near line {inp} of {current()})")
        elif m and m.re is MULTIPLY:
            multiply.add(m.group(1))
        elif m and m.re is MISSING:
            missing[m.group(1)] = m.group(2)
        if m:
            track(line[m.start():])
        if "Token not allowed in a PDF string" in line:
            bookmark_file = current()
        elif bookmark_file and line.startswith("(hyperref)"):
            ln = re.search(r"input line (\d+)", line)
            if ln:
                bookmarks.add(f"{bookmark_file}:{ln.group(1)}")
                bookmark_file = None
        m = PAGES.search(line)
        if m:
            pages = m.group(1)
        if "Rerun to get" in line or "Label(s) may have changed" in line:
            rerun = True

    print(f"Pages: {pages}")
    problems = 0
    for title, items in (("Overfull lines", overfull), ("Off the page", offpage),
                         ("Undefined references", undefined),
                         ("Duplicate labels", sorted(multiply)),
                         ("Math or commands in headings (use \\texorpdfstring)",
                          sorted(bookmarks, key=lambda s: (s.rsplit(":", 1)[0], int(s.rsplit(":", 1)[1])))),
                         ("Missing glyphs", [f"{c} (font {f})" for c, f in missing.items()])):
        if items:
            problems += len(items)
            print(f"{title}: {len(items)}")
            for it in items:
                print(f"  {it}")
        else:
            print(f"{title}: none")
    if rerun:
        print("Note: cross-references have not settled yet; compile once more (--runs 4).")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("explainer_dir", type=Path)
    ap.add_argument("--build-dir", type=Path, help="build directory (default: under the system temp directory)")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--out", help="copy the PDF into the explainer folder under this name")
    args = ap.parse_args()

    src = args.explainer_dir.resolve()
    if not (src / "main.tex").is_file():
        print(f"Not found: {src / 'main.tex'}")
        return 1
    build = args.build_dir
    if build is None:
        tag = hashlib.md5(str(src).encode("utf-8")).hexdigest()[:10]
        build = Path(tempfile.gettempdir()) / "paper-explainer-build" / tag
    build = build.resolve()
    copy_sources(src, build)
    print(f"Build directory: {build}")

    failed = run_xelatex(build, args.runs)
    log_path = build / "main.log"
    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines() if log_path.exists() else []
    if failed:
        print(f"xelatex failed on run {failed}:")
        show_errors(lines)
        return 1

    problems = report(lines)
    pdf = build / "main.pdf"
    if args.out:
        name = args.out if args.out.lower().endswith(".pdf") else args.out + ".pdf"
        shutil.copy2(pdf, src / name)
        print(f"PDF copied to: {src / name}")
    else:
        print(f"PDF: {pdf}")
    return 2 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
