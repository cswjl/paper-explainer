"""Check that every numbered item of the original paper appears in the explainer.

Usage:
    python -P coverage.py <paper.pdf> <explainer_dir>

Reads the original PDF (the version the explainer is based on) and the
explainer's LaTeX sources (main.tex and every .tex file under sections/), and
lists what the explainer leaves out:

  - definitions, assumptions, theorems, lemmas, propositions, corollaries,
    claims and algorithms that the paper states (a line starting with a bold,
    italic or small-caps "Theorem 3.8", or with "Theorem 3.8." / "Theorem 3.8:")
    but the explainer never names ("Theorem 3.8" or "定理 3.8" …);
  - figures and tables with a caption in the paper ("Figure 3:", "Table 2.")
    that the explainer never calls Paper Figure 3 / Paper Table 2 (Chinese:
    原文图 3 / 原文表 2);
  - equation numbers printed at the end of a line in the paper, such as (7) or
    (A.2), with no \\ptag{…} in the explainer, and \\ptag numbers that the paper
    does not have.

It also lists numbers that the paper only mentions in running text and never
states. Usually the paper is citing another work ("Theorem 3.7 of Lee et al.");
otherwise it is a dangling reference in the paper, worth an entry in E2.
When no heading or caption of some kind is recognised at all (an unusual font),
the numbers mentioned in the text are checked instead, and the output says so.

The detection relies on the fonts and layout of the PDF, so read the page and
the context shown for each item before acting on it.

The paper is downloaded content: this script only reads it. Run it with
`python -P` rather than `-I`, which would hide PyMuPDF if it is installed in
the user site.
Exit status: 0 nothing missing, 2 something missing, 1 usage error.
"""
import argparse
import re
import sys
import unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# A result, figure or equation number: 3, 3.8, A.1, B.12, S2, 2.1.3
NUM_BODY = r"(?:[A-Z]{1,2}\.?)?\d+(?:\.\d+)*"
NUM = "(" + NUM_BODY + ")"
RESULTS = ["Definition", "Assumption", "Theorem", "Lemma", "Proposition", "Corollary", "Claim", "Algorithm"]
FLOATS = {"Figure": "Figure", "Fig.": "Figure", "Table": "Table"}
ORDER = RESULTS + ["Figure", "Table"]
PLURAL = {"Corollary": "Corollaries"}
# How the explainer names the paper's items: Theorem 3.8 / 定理 3.8, Paper Figure 3 / 原文图 3 …
ZH_KIND = {"定义": "Definition", "假设": "Assumption", "定理": "Theorem", "引理": "Lemma", "命题": "Proposition",
           "推论": "Corollary", "断言": "Claim", "算法": "Algorithm", "原文图": "Figure", "原文表": "Table"}
IN_EXPLAINER = re.compile(
    r"(" + "|".join(ZH_KIND) + "|" + "|".join(RESULTS)
    + r"|[Pp]aper [Ff]igure|[Pp]aper [Ff]ig\.|[Pp]aper [Tt]able)s?\s*~?\s*" + NUM)


def alternatives(words) -> str:
    return "|".join(re.escape(v) for w in words for v in (w, w.upper()))


# A full stop after the number counts as punctuation, the dot of "4.2" does not.
END = r"(?:\.(?!\d)|:)"
HEADING = re.compile(r"^(" + alternatives(RESULTS) + r")\s*" + NUM + r"(?=$|\s|\(|" + END + ")")
CAPTION = re.compile(r"^(" + alternatives(FLOATS) + r")\s*" + NUM + r"\s*(?:" + END + r"|\||$)")
MENTION = re.compile(r"\b(" + alternatives(RESULTS) + "|" + alternatives(FLOATS) + r")s?\s*" + NUM)
EQNO = re.compile(r"^\((" + NUM_BODY + r"[a-z]?)\)$")
STYLED_FONT = re.compile(r"bold|black|heavy|semibold|demi|medi|cmbx|sfbx|bx\d|ital|oblique|cmti|sfti|csc|caps", re.I)


def kind_of(word: str) -> str:
    """Kind of item named by an English word from the paper (any case)."""
    word = word.title() if word.isupper() else word
    return FLOATS.get(word, word)


def explainer_kind(word: str) -> str:
    if word in ZH_KIND:
        return ZH_KIND[word]
    if word.lower().startswith("paper"):
        return "Table" if "table" in word.lower() else "Figure"
    return word


def styled(span) -> bool:
    """Bold, italic or small caps: how theorem headings are usually set."""
    return bool(span["flags"] & (2 | 16)) or bool(STYLED_FONT.search(span.get("font", "")))


def line_text(spans) -> str:
    """Text of one PDF line. Spans often carry no space characters between words
    ("Algorithm", "1", "NAIL"), so a space is put wherever the spans have a gap."""
    out = spans[0]["text"]
    for prev, cur in zip(spans, spans[1:]):
        gap = cur["bbox"][0] - prev["bbox"][2]
        if gap > 0.15 * cur["size"] and not out.endswith(" ") and not cur["text"].startswith(" "):
            out += " "
        out += cur["text"]
    return unicodedata.normalize("NFKC", out).strip()


def natural(s: str):
    return [(0, int(t), "") if t.isdigit() else (1, 0, t) for t in re.findall(r"\d+|\D+", s)]


def plural(kind: str) -> str:
    return PLURAL.get(kind, kind + "s")


def scan_pdf(pdf: Path):
    """Items the paper states, items it mentions, and the equation numbers it prints."""
    import pymupdf

    doc = pymupdf.open(pdf)
    stated = {k: {} for k in ORDER}     # kind -> number -> (page, heading line)
    mentioned = {k: {} for k in ORDER}  # kind -> number -> (page, context)
    equations = {}                      # number -> page
    for pno, page in enumerate(doc, 1):
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                spans = [s for s in line["spans"] if s["text"].strip()]
                if not spans:
                    continue
                text = line_text(spans)
                m = HEADING.match(text)
                if m and (styled(spans[0]) or re.match(r"\s*" + END, text[m.end():])):
                    stated[kind_of(m.group(1))].setdefault(m.group(2), (pno, text[:70]))
                m = CAPTION.match(text)
                if m:
                    stated[kind_of(m.group(1))].setdefault(m.group(2), (pno, text[:70]))
                m = EQNO.match(unicodedata.normalize("NFKC", spans[-1]["text"]).strip())
                if m:
                    equations.setdefault(m.group(1), pno)
        flat = unicodedata.normalize("NFKC", page.get_text())
        flat = " ".join(re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", flat).split())  # rejoin "Theo-\nrem"
        for m in MENTION.finditer(flat):
            ctx = flat[max(0, m.start() - 70):m.end() + 50]
            mentioned[kind_of(m.group(1))].setdefault(m.group(2), (pno, ctx))
    return doc.page_count, stated, mentioned, equations


def scan_explainer(root: Path):
    files = [root / "main.tex"] + sorted((root / "sections").rglob("*.tex"))
    lines = []
    for f in files:
        if f.is_file():
            lines += [re.sub(r"(?<!\\)%.*", "", ln) for ln in f.read_text(encoding="utf-8").split("\n")]
    text = "\n".join(lines)
    named = {k: set() for k in ORDER}
    for word, n in IN_EXPLAINER.findall(text):
        named[explainer_kind(word)].add(n)
    return named, set(re.findall(r"\\ptag\{([^{}]+)\}", text))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf", type=Path, help="the paper's PDF (the version explained)")
    ap.add_argument("explainer_dir", type=Path, help="the explainer folder (with main.tex and sections/)")
    args = ap.parse_args()
    if not args.pdf.is_file():
        print(f"Not found: {args.pdf}")
        return 1
    if not (args.explainer_dir / "main.tex").is_file():
        print(f"Not found: {args.explainer_dir / 'main.tex'}")
        return 1

    pages, stated, mentioned, equations = scan_pdf(args.pdf)
    named, ptags = scan_explainer(args.explainer_dir)
    print(f"Paper: {args.pdf.name} ({pages} pages)")
    missing = 0
    for kind in ORDER:
        items, guessed = stated[kind], False
        if not items and mentioned[kind]:
            items, guessed = mentioned[kind], True
        if not items:
            continue
        lack = [n for n in sorted(items, key=natural) if n not in named[kind]]
        head = f"{plural(kind)}: {len(items)} in the paper"
        if guessed:
            head += " (no heading or caption recognised; checked against the numbers mentioned in the text)"
        if not lack:
            print(f"{head}, all in the explainer")
            continue
        missing += len(lack)
        print(f"{head}, {len(lack)} missing from the explainer:")
        for n in lack:
            page, where = items[n]
            print(f"    {kind} {n} (page {page}): {where}")

    no_tag = sorted(set(equations) - ptags, key=natural)
    extra = sorted(ptags - set(equations), key=natural)
    if no_tag:
        missing += len(no_tag)
        print(f"Numbered equations: {len(equations)} in the paper, {len(no_tag)} without \\ptag: "
              + ", ".join(f"({n}) page {equations[n]}" for n in no_tag))
    else:
        print(f"Numbered equations: {len(equations)} in the paper, all have \\ptag")
    if extra:
        missing += len(extra)
        print(f"\\ptag numbers not found in the paper: {', '.join(extra)} (a wrong number, or the paper prints "
              "this number in the same text run as the formula, which the script cannot see)")

    only = [(k, n, mentioned[k][n]) for k in ORDER if stated[k]
            for n in sorted(mentioned[k], key=natural) if n not in stated[k]]
    if only:
        print("\nNumbers the paper only mentions in running text, with no statement or caption found. "
              "Usually the paper is citing another work; otherwise it may be a dangling reference in the "
              "paper, worth an entry in E2:")
        for kind, n, (page, ctx) in only:
            print(f"    {kind} {n} (page {page}): …{ctx}…")

    print("\n" + ("Nothing missing." if not missing else f"{missing} item(s) to check."))
    return 2 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
