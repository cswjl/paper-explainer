"""List an arXiv source tree's bibliography and where each entry is cited.

Usage:
    python -I bib_list.py <source_dir> [--bbl FILE]

Reads the .bbl file (the only one under <source_dir>, or the one given with --bbl)
and every .tex file under <source_dir>. Both BibTeX (\\bibitem) and biblatex
(\\entry) .bbl files are understood. For each entry it prints the number,
citation key, label and the reference text with LaTeX markup lightly cleaned,
followed by the (sub)sections whose text cites it. Use the output to write the
explainer's reference appendix (E3, or 附 3 in Chinese) and to check that every reference is
accounted for.

The source tree is downloaded content: this script only reads it as text.
"""
import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# \cite, \citet, \citep, \nocite, biblatex's \parencite, \textcite, \autocite, \footcite …,
# and the capitalised forms used at the start of a sentence (\Citet, \Citep, \Cite …)
CITE = re.compile(r"\\[A-Za-z]*[cC]ite[A-Za-z]*\*?(?:\[[^\]]*\]){0,2}\{([^}]*)\}")
HEAD = re.compile(r"\\(section|subsection)\*?\{((?:[^{}]|\{[^{}]*\})*)\}")


def clean(s: str) -> str:
    s = re.sub(r"\\newblock", " | ", s)
    s = re.sub(r"\\penalty0|\\natexlab\{[^}]*\}|\\urlprefix", "", s)
    s = re.sub(r"\\(?:em|it|bf|sc)\b", "", s)
    s = re.sub(r"\\(?:emph|textit|textbf|textsc|url|href)\{([^}]*)\}", r"\1", s)
    s = s.replace("\\&", "&").replace("~", " ").replace("\\ ", " ")
    s = re.sub(r"[{}]", "", s)
    return re.sub(r"\s+", " ", s).strip(" |")


def parse_bibitems(bbl: str) -> list[tuple[str, str, str]]:
    body = bbl.split("\\begin{thebibliography}", 1)[-1].split("\\end{thebibliography}", 1)[0]
    items = []
    for chunk in re.split(r"\\bibitem\b", body)[1:]:
        s = chunk.lstrip()
        label = ""
        if s.startswith("["):
            depth = 0
            for i, c in enumerate(s):
                if c == "{":
                    depth += 1
                elif c == "}":
                    depth -= 1
                elif c == "]" and depth == 0:
                    label, s = s[1:i], s[i + 1:].lstrip()
                    break
        m = re.match(r"\{([^}]*)\}", s)
        key = m.group(1).strip() if m else "?"
        text = s[m.end():] if m else s
        items.append((key, clean(label), clean(text)))
    return items


def parse_biblatex(bbl: str) -> list[tuple[str, str, str]]:
    items = []
    for m in re.finditer(r"\\entry\{([^}]*)\}\{([^}]*)\}.*?\\endentry", bbl, re.S):
        body = m.group(0)

        def field(name: str) -> str:
            f = re.search(r"\\field\{" + name + r"\}\{((?:[^{}]|\{[^{}]*\})*)\}", body)
            return clean(f.group(1)) if f else ""

        authors = re.findall(r"\bfamily=\{([^}]*)\}", body)
        year = field("year") or field("labelyear")
        venue = field("journaltitle") or field("booktitle") or field("eventtitle") or field("eprinttype")
        label = f"{authors[0] if authors else '?'}{' et al.' if len(authors) > 1 else ''} ({year})"
        text = " | ".join(x for x in (", ".join(clean(a) for a in authors), field("title"), f"{venue} {year}".strip()) if x)
        items.append((m.group(1).strip(), label, text))
    return items


def find_cites(root: Path) -> dict[str, Counter]:
    where: dict[str, Counter] = defaultdict(Counter)
    for tex in sorted(root.rglob("*.tex")):
        text = "\n".join(re.sub(r"(?<!\\)%.*", "", ln)
                         for ln in tex.read_text(encoding="utf-8", errors="replace").split("\n"))
        current = tex.name
        events = sorted([(m.start(), "h", m) for m in HEAD.finditer(text)] +
                        [(m.start(), "c", m) for m in CITE.finditer(text)], key=lambda e: e[0])
        for _, kind, m in events:
            if kind == "h":
                title = clean(m.group(2))
                current = f"{tex.name} §{title}" if m.group(1) == "section" else f"{tex.name} §… {title}"
                continue
            for key in m.group(1).split(","):
                key = key.strip()
                if key and key != "*":
                    where[key][current] += 1
    return where


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source_dir", type=Path)
    ap.add_argument("--bbl", type=Path)
    args = ap.parse_args()

    found = sorted(args.source_dir.rglob("*.bbl"))
    bbl = args.bbl
    if bbl is None:
        if not found:
            print("No .bbl file found. With only a .bib, compile the reference list by hand from the PDF.")
            return 1
        if len(found) > 1:
            print("Several .bbl files found; pick one with --bbl:")
            for f in found:
                print(f"  {f}")
            return 1
        bbl = found[0]
    raw = bbl.read_text(encoding="utf-8", errors="replace")
    items = parse_biblatex(raw) if "\\entry{" in raw else parse_bibitems(raw)
    if not items:
        print(f"No entries parsed from {bbl}; the format may be unsupported. "
              "Compile the reference list by hand from the PDF.")
        return 1
    where = find_cites(args.source_dir)
    print(f"{bbl.name}: {len(items)} entries")
    for n, (key, label, text) in enumerate(items, 1):
        print(f"{n:3d}. [{key}] {label} :: {text}")
        if where.get(key):
            places = "; ".join(f"{p}" + (f" x{c}" if c > 1 else "") for p, c in where[key].items())
            print(f"     cited in: {places}")
        else:
            print("     cited in: (no \\cite in the text; perhaps only \\nocite, or in a figure or table)")
    cited_only = sorted(set(where) - {k for k, _, _ in items})
    if cited_only:
        print(f"Keys cited but not in the .bbl: {', '.join(cited_only)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
