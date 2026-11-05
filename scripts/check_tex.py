"""Check an explainer's LaTeX sources against the style guide.

Usage:
    python check_tex.py <explainer_dir> [--lang zh|en]

The explainer's language comes from the \\zhtrue / \\zhfalse switch in main.tex
(explainers made before the switch existed count as Chinese when they use ctexart
without scheme=plain), unless --lang is given. It decides how length is counted,
which filler phrases are looked for, and whether Chinese punctuation is checked.

Problems (fix these):
  - a theorem or proposition box in Part I with no \\plainsay between it and the next
    box or heading (a short proof may come first)
  - display math in the formula-free walkthrough (the section labelled sec:plain)
  - template placeholders left: \\FILL{…} (or the older 【待填 / [[FILL)
  - a required section missing: sec:plain, sec:overview, app:versions, app:errata, app:refs
  - a paper equation cited as plain text (Eq. (7), equation 7, 式 (7), 式 (A.3)) instead of
    a link (Eq.~\\peq{7}, 式~\\peq{7}); headings, box titles and quoted text are exempt
  - \\tag{paper N} or \\tag{原文 N} written directly instead of \\ptag{N}, which also creates
    the link target
  - \\peq{N} with no matching \\ptag{N}, i.e. a link to an equation the explainer never
    shows; N may be any equation number of the paper, such as 7, 3.2, A.1 or 12a
  - Chinese explainers only: half-width punctuation or parentheses touching Chinese characters
Notes (judge for yourself; most of them are about length):
  - length per file (English words or Chinese characters), and a walkthrough longer than
    about two pages
  - more than three toy examples (check boxes titled "Toy example …" or "小例子…"), and
    Part I files crowded with check boxes or note boxes
  - \\plainsay lines longer than one sentence
  - summary boxes after the front matter, which the style guide leaves out
  - stock filler phrases ("in other words", "it is worth noting", 换句话说, 值得注意的是 …)
  - inline math in the walkthrough

Part I is everything between the first and second \\part in main.tex.
Exit status: 0 no problems, 2 problems found, 1 usage error.
"""
import argparse
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

CJK = "[\u3400-\u9fff\uf900-\ufaff]"
CJK_CHAR = re.compile(CJK)
BRACED = r"(?:[^{}]|\{[^{}]*\})*"  # argument text allowing one level of nested braces
THMBOX = re.compile(r"\\begin\{thmbox\}\{(" + BRACED + r")\}")
NEXT_BLOCK = re.compile(r"\\begin\{(?:thmbox|defbox)\}|\\(?:sub)*section\*?\{")
NEEDS_PLAINSAY = re.compile(r"Theorem|Proposition|定理|命题")  # Part I box titles that need a \plainsay
PLACEHOLDER = re.compile(r"\\FILL\{|【待填|\[\[FILL")
# Equation references: the paper's equations are shown with \ptag{N} and cited with \peq{N}.
EQ_TEXT_REF = re.compile(
    r"\b(?:[Ee]qs?|[Ee]quations?)\.?[ \t~]*\(?\s*(?:[A-Z]\.?)?\d"  # Eq. (7), Eqs. 5, equation (A.3)
    r"|式[ \t~]*\(?\s*(?:[A-Z]\.?)?\d"                              # 式 (7), 式 7, 式 (A.3)
)
# Quoted text is the paper's own wording (e.g. an erratum quoting a wrong "Eq. (11)"), so it is exempt.
QUOTED = re.compile(r"“[^“”]{0,400}”|``.{0,400}?''|\"[^\"\n]{0,200}\"", re.S)
# Equation numbers are taken as written: 7, 3.2, A.1, 12a ...
PEQ = re.compile(r"\\peq\{([^{}]+)\}")
PTAG = re.compile(r"\\ptag\{([^{}]+)\}")
RAW_TAG = re.compile(r"\\tag\{(?:paper|原文)")
EXAMPLE = re.compile(r"\\begin\{checkbox\}\[((?:[Tt]oy example|小例子)[^\]]*)\]")
TITLES = re.compile(
    r"\\(?:sub)*section\*?\{" + BRACED + r"\}"
    r"|\\begin\{(?:thmbox|defbox)\}\{" + BRACED + r"\}"
    r"|\\begin\{(?:checkbox|notebox|sumbox)\}\[[^\]]*\]"
)
REQUIRED = {
    "sec:plain": "Section 1, the whole paper without formulas",
    "sec:overview": "all results at a glance",
    "app:versions": "E1, version differences",
    "app:errata": "E2, errors and consistency checks",
    "app:refs": "E3, references and their roles",
}
EXAMPLES_MAX = 3    # toy-example boxes in the whole explainer
BOXES_PER_FILE = 2  # check boxes, or note boxes, in one Part I file
EN_FILLERS = [
    "it is worth noting", "it is worth mentioning", "it should be noted", "it is important to note",
    "in other words", "that is to say", "to summarize", "in summary", "to sum up", "simply put",
    "in short", "it is easy to see", "it is not hard to see", "it is clear that", "clearly", "obviously",
    "as is well known", "it is well known", "we can see", "below we", "below, we", "next we", "next, we",
    "in this section", "this section covers", "this section shows",
    "as mentioned", "as discussed above", "as noted above", "as stated earlier", "as we saw",
]
ZH_FILLERS = [
    "值得注意的是", "需要注意的是", "需要指出的是", "换句话说", "也就是说", "总结一下",
    "简单来说", "简而言之", "不难看出", "不难发现", "容易看出", "显然", "众所周知",
    "可以看到", "下面我们", "接下来我们", "这一节我们", "本节将", "这一节讲", "这一节把",
    "如前所述", "前面说过", "前面讲过", "正如前面",
]
# Thresholds behind the length notes: about two pages of walkthrough, one sentence of plain words.
LANG = {
    "en": {"unit": "words", "plain_max": 1100, "plainsay_max": 40, "fillers": EN_FILLERS},
    "zh": {"unit": "Chinese characters", "plain_max": 1800, "plainsay_max": 60, "fillers": ZH_FILLERS},
}
# Regions whose punctuation follows other rules: math, TikZ/pgfplots code, command arguments.
SKIP_REGIONS = [
    r"\$\$.*?\$\$",
    r"(?<!\\)\$.*?(?<!\\)\$",
    r"(?<!\\)\\\[.*?(?<!\\)\\\]",  # display math, but not the line break \\[2pt]
    r"\\\(.*?\\\)",
    r"\\begin\{(equation|align|gather|multline|eqnarray|tikzpicture|axis|groupplot)\*?\}.*?\\end\{\1\*?\}",
    # Equation numbers deliberately use half-width parentheses: 式~(\ref{eq:x})、式 (原文 6).
    r"\(\s*\\(?:ref|eqref)\{[^}]*\}\s*\)",
    r"\(原文[^()]*\)",
    r"\\(?:ref|eqref|label|cite\w*|url|href|input|include|usepackage|usetikzlibrary)\{[^}]*\}",
]
PUNCT = [
    (re.compile(CJK + r"[,;:!?]"), "half-width punctuation after Chinese"),
    (re.compile(r"[,;:!?]" + CJK), "half-width punctuation before Chinese"),
    (re.compile(CJK + r"\.(?=\s|$)"), "half-width full stop after Chinese"),
    (re.compile(CJK + r"\(|\(" + CJK), "half-width ( touching Chinese"),
    (re.compile(CJK + r"\)|\)" + CJK), "half-width ) touching Chinese"),
]


def strip_comments(text: str) -> str:
    return "\n".join(re.sub(r"(?<!\\)%.*", "", line) for line in text.split("\n"))


def blank_regions(text: str) -> str:
    """Replace skipped regions with spaces, keeping newlines so line numbers stay valid."""
    for pat in SKIP_REGIONS:
        text = re.sub(pat, lambda m: re.sub(r"[^\n]", " ", m.group(0)), text, flags=re.S)
    return text


def detect_lang(main_text: str) -> str:
    """zh or en, from the \\zhtrue/\\zhfalse switch, else from the document class."""
    m = re.search(r"\\zh(true|false)\b", main_text)
    if m:
        return "zh" if m.group(1) == "true" else "en"
    cls = re.search(r"\\documentclass\s*(\[[^\]]*\])?\s*\{([^}]*)\}", main_text)
    if cls and cls.group(2).strip().startswith("ctex") and "scheme=plain" not in (cls.group(1) or ""):
        return "zh"
    return "en"


def length(text: str, lang: str) -> int:
    """Chinese characters, or English words outside math, labels and command names."""
    if lang == "zh":
        return len(CJK_CHAR.findall(text))
    plain = re.sub(r"\\[A-Za-z@]+\*?", " ", blank_regions(text))
    return len(re.findall(r"[A-Za-z]+(?:['’][A-Za-z]+)*", plain))


def braced_arg(text: str, start: int) -> str:
    """Contents of the brace group opening at text[start]; escaped braces are skipped."""
    depth, i = 0, start
    while i < len(text):
        c = text[i]
        if c == "\\":
            i += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1:i]
        i += 1
    return text[start + 1:]


def input_order(root: Path) -> list[tuple[int, Path]]:
    """(part number, file) for every \\input in main.tex; files before the first \\part get 0."""
    main = strip_comments((root / "main.tex").read_text(encoding="utf-8"))
    part, files = 0, []
    for m in re.finditer(r"\\part\*?\{|\\(?:input|include)\{([^}]+)\}", main):
        if m.group(1) is None:
            part += 1
            continue
        p = root / m.group(1)
        if p.suffix != ".tex":
            p = p.with_name(p.name + ".tex")
        files.append((part, p))
    return files


def line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def listing(items: list[str], limit: int = 6) -> str:
    return ", ".join(items[:limit]) + (" …" if len(items) > limit else "")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("explainer_dir", type=Path)
    ap.add_argument("--lang", choices=["zh", "en"], help="override the language read from main.tex")
    args = ap.parse_args()
    root = args.explainer_dir.resolve()
    if not (root / "main.tex").is_file():
        print(f"Not found: {root / 'main.tex'}")
        return 1
    lang = args.lang or detect_lang(strip_comments((root / "main.tex").read_text(encoding="utf-8")))
    cfg = LANG[lang]
    filler_res = [(p, re.compile(re.escape(p)) if lang == "zh" else re.compile(r"\b" + re.escape(p) + r"\b", re.I))
                  for p in cfg["fillers"]]
    files = input_order(root)
    problems, walk_notes = [], []
    labels = set()
    sizes = []          # (file, length)
    examples = []       # "file:line title" of each toy example
    crowded = []        # Part I files with many check or note boxes
    long_plainsay = []  # "file:line (N words)"
    sumboxes = []       # summary boxes after the front matter
    fillers = {}        # phrase -> ["file:line", ...]
    ptags = set()       # paper equation numbers shown with \ptag
    peqs = []           # (number, "file:line") of every \peq link

    for part, path in [(None, root / "main.tex")] + files:
        if not path.exists():
            problems.append(f"[file] main.tex inputs {path.relative_to(root)}, which does not exist")
            continue
        rel = path.relative_to(root).as_posix()
        text = strip_comments(path.read_text(encoding="utf-8"))
        lines = text.split("\n")
        labels.update(re.findall(r"\\label\{([^}]+)\}", text))

        todo = sorted({line_of(text, m.start()) for m in PLACEHOLDER.finditer(text)})
        if todo:
            problems.append(f"[placeholder] {rel} line {', '.join(map(str, todo))}: template placeholders left")

        if part is None:
            continue

        size = length(text, lang)
        sizes.append((rel, size))

        # Equation references: links, link targets, and plain-text citations outside titles.
        ptags.update(PTAG.findall(text))
        peqs += [(m.group(1), f"{rel}:{line_of(text, m.start())}") for m in PEQ.finditer(text)]
        for m in RAW_TAG.finditer(text):
            problems.append(f"[equation] {rel}:{line_of(text, m.start())} \\tag{{…}} written directly; "
                            "use \\ptag{N}, which also creates the link target")
        blank = lambda m: re.sub(r"[^\n]", " ", m.group(0))  # noqa: E731
        body = QUOTED.sub(blank, TITLES.sub(blank, text))
        for m in EQ_TEXT_REF.finditer(body):
            ln = line_of(body, m.start())
            col = m.start() - (body.rfind("\n", 0, m.start()) + 1)
            ctx = lines[ln - 1][max(0, col - 6):col + 14].strip()
            problems.append(f"[equation] {rel}:{ln} paper equation cited without a link: …{ctx}…; "
                            "write Eq.~\\peq{N} (Chinese: 式~\\peq{N})")

        # Part I theorems and propositions need a plain-words line: \plainsay must come after
        # the box and before the next box or heading (a short proof may sit in between).
        if part == 1:
            for m in THMBOX.finditer(text):
                title = m.group(1)
                if not NEEDS_PLAINSAY.match(title):
                    continue
                close = text.find("\\end{thmbox}", m.end())
                if close < 0:
                    continue
                nxt = NEXT_BLOCK.search(text, close)
                if "\\plainsay" not in text[close:nxt.start() if nxt else len(text)]:
                    problems.append(f"[plain words] {rel}:{line_of(text, m.start())} \"{title}\" has no \\plainsay after it")

        for m in re.finditer(r"\\plainsay\s*\{", text):
            n = length(braced_arg(text, m.end() - 1), lang)
            if n > cfg["plainsay_max"]:
                long_plainsay.append(f"{rel}:{line_of(text, m.start())} ({n} {cfg['unit']})")

        # The formula-free walkthrough.
        if "\\label{sec:plain}" in text:
            display = len(re.findall(r"(?<!\\)\\\[|\\begin\{(?:equation|align|gather|multline|eqnarray)|\$\$", text))
            if display:
                problems.append(f"[Section 1] {rel} has {display} display formula(s); the walkthrough should have none")
            inline = len(re.findall(r"(?<!\\)\$", re.sub(r"\$\$", "", text))) // 2
            walk_notes.append(f"[Section 1] {rel} has {inline} inline formula(s); naming key quantities is fine, "
                              "derivations are not")
            if size > cfg["plain_max"]:
                walk_notes.append(f"[Section 1] {rel} has about {size} {cfg['unit']}, more than two pages "
                                  f"(about {cfg['plain_max']}); keep only what the story needs")

        for m in EXAMPLE.finditer(text):
            examples.append(f"{rel}:{line_of(text, m.start())} {m.group(1)}")

        if part == 1:
            checks = len(re.findall(r"\\begin\{checkbox\}", text))
            remarks = len(re.findall(r"\\begin\{notebox\}", text))
            if checks > BOXES_PER_FILE or remarks > BOXES_PER_FILE:
                crowded.append(f"{rel} ({checks} check or example boxes, {remarks} note boxes)")

        if part >= 1:
            sumboxes += [f"{rel}:{line_of(text, m.start())}" for m in re.finditer(r"\\begin\{sumbox\}", text)]

        for phrase, pat in filler_res:
            for m in pat.finditer(text):
                fillers.setdefault(phrase, []).append(f"{rel}:{line_of(text, m.start())}")

        # Half-width punctuation next to Chinese.
        if lang == "zh":
            plain = blank_regions(text)
            for pat, what in PUNCT:
                for m in pat.finditer(plain):
                    ln = line_of(plain, m.start())
                    snippet = lines[ln - 1].strip()
                    col = m.start() - (plain.rfind("\n", 0, m.start()) + 1)
                    ctx = lines[ln - 1][max(0, col - 8):col + 10].strip()
                    problems.append(f"[punctuation] {rel}:{ln} {what}: …{ctx or snippet[:20]}…")

    for key, what in REQUIRED.items():
        if key not in labels:
            problems.append(f"[sections] missing \\label{{{key}}} ({what})")
    for n, loc in peqs:
        if n not in ptags:
            problems.append(f"[equation] {loc} \\peq{{{n}}} has no \\ptag{{{n}}}: the paper's equation ({n}) "
                            "is never displayed")

    total = sum(n for _, n in sizes)
    longest = sorted(sizes, key=lambda s: -s[1])[:5]
    notes = [f"[length] about {total} {cfg['unit']} in total; longest files: "
             + ", ".join(f"{f} {n}" for f, n in longest)]
    notes += walk_notes
    if len(examples) > EXAMPLES_MAX:
        notes.append(f"[toy examples] {len(examples)}, usually at most {EXAMPLES_MAX}: "
                     "keep only those where concrete numbers help most")
    else:
        notes.append(f"[toy examples] {len(examples)}" + (" (they are optional)" if not examples else ""))
    notes += [f"    {e}" for e in examples]
    if crowded:
        notes.append(f"[crowded] as a rule at most {BOXES_PER_FILE} check boxes and {BOXES_PER_FILE} note boxes "
                     "per file: " + "; ".join(crowded))
    if long_plainsay:
        notes.append(f"[plain words] longer than {cfg['plainsay_max']} {cfg['unit']}; one sentence on the "
                     "meaning is enough: " + listing(long_plainsay))
    if sumboxes:
        notes.append(f"[summary] {len(sumboxes)} summary box(es) in the body (no per-section summaries; "
                     "only very long sections get one): " + listing(sumboxes))
    if fillers:
        notes.append(f"[filler] {sum(len(v) for v in fillers.values())} in total; delete or rewrite:")
        for phrase, locs in sorted(fillers.items(), key=lambda kv: -len(kv[1])):
            notes.append(f"    \"{phrase}\" x{len(locs)}: {listing(locs, 4)}")

    print(f"Language: {lang}")
    print(f"Problems: {len(problems)}" + (" (fix these)" if problems else ""))
    for p in problems:
        print(f"  {p}")
    print("Notes:")
    for n in notes:
        print(f"  {n}")
    return 2 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
