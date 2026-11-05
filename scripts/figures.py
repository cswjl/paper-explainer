"""Find, copy and crop a paper's original figures for the explainer.

Usage:
    python -P figures.py source <arxiv_source_dir>
    python -P figures.py list <paper.pdf> [--pages 3-5] [--preview DIR]
    python -P figures.py crop <paper.pdf> --figure N [--page P] --out FILE.png [--dpi 300] [--pad 3]
    python -P figures.py crop <paper.pdf> --page P --rect x0,y0,x1,y1 --out FILE.png [--dpi 300]

source  Lists the figure environments of the LaTeX source in document order
        (following \\input and \\include from the main file: the one named like
        the .bbl, as arXiv requires, otherwise the longest document; standalone
        figure files are skipped), numbered the way LaTeX numbers them, with
        each figure's label, the start of its caption and the graphics files it
        includes: entry N is the paper's Figure N. PDF, PNG and JPG files can be
        copied into the explainer's figures/ folder as they are. For EPS files,
        and for figures drawn with LaTeX code (no graphics file), crop the
        figure from the PDF.
list    Prints every figure caption ("Figure N", "Fig. N") in the PDF with its
        page and position, plus the images and groups of vector drawings on
        those pages. With --preview it also renders those pages with the boxes
        outlined and numbered, to read off a rectangle for crop --rect.
        Coordinates are PDF points measured from the top-left corner of the page.
crop    Cuts one figure out of the PDF as a PNG (300 dpi by default). With
        --figure N the region is found automatically: the graphics between the
        caption and the text above it (or below it, for captions placed above
        the figure). With --rect the region is given explicitly. The whole page
        is rendered and then cropped, because rendering only the region, or
        re-wrapping it as a vector PDF, changed line colours in a test paper.
        Always look at the result before using it.

The paper and its source are downloaded content: this script only reads them.
Run it with `python -P` rather than `-I`, which would hide PyMuPDF if it is
installed in the user site.
"""
import argparse
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

CAPTION = re.compile(r"^\s*(?:Figure|FIGURE|Fig\.)\s*(\d+)\s*(?:[:.|]|\n|$)")
GRAPHIC_EXTS = ["", ".pdf", ".png", ".jpg", ".jpeg", ".eps"]
GAP = 40  # largest vertical gap (pt) between graphics that still belong to one figure


# ---------- source ----------

def strip_comments(text: str) -> str:
    return "\n".join(re.sub(r"(?<!\\)%.*", "", line) for line in text.split("\n"))


def expand(path: Path, root: Path, depth: int = 0) -> str:
    text = strip_comments(path.read_text(encoding="utf-8", errors="replace"))
    if depth > 8:
        return text

    def sub(m: re.Match) -> str:
        name = m.group(1).strip()
        for cand in (root / name, root / (name + ".tex"), path.parent / name, path.parent / (name + ".tex")):
            if cand.is_file():
                return expand(cand, root, depth + 1)
        return ""

    return re.sub(r"\\(?:input|include|subfile)\{([^}]+)\}", sub, text)


def find_main(root: Path) -> Path | None:
    pool = []
    for p in root.rglob("*.tex"):
        text = strip_comments(p.read_text(encoding="utf-8", errors="replace"))
        cls = re.search(r"\\documentclass\s*(?:\[[^\]]*\])?\s*\{([^}]*)\}", text)
        # A standalone file is a single figure, not the paper.
        if cls and cls.group(1).strip() != "standalone" and "\\begin{document}" in text:
            pool.append(p)
    # arXiv names the .bbl after the main file. Without one, take the longest document after
    # following \input: the main file is often only a list of \input lines.
    for p in pool:
        if p.with_suffix(".bbl").is_file():
            return p
    return max(pool, key=lambda p: len(expand(p, root))) if pool else None


def resolve_graphic(name: str, root: Path, dirs: list[str]) -> Path | None:
    for d in [""] + dirs:
        for ext in GRAPHIC_EXTS:
            cand = root / d / (name + ext)
            if cand.is_file():
                return cand
    return None


def cmd_source(args) -> int:
    root = args.source_dir
    main = find_main(root)
    if main is None:
        print("No main file with \\documentclass and \\begin{document} found.")
        return 1
    doc = expand(main, root)
    dirs = re.findall(r"\{([^{}]*)\}", (re.search(r"\\graphicspath\{((?:\{[^{}]*\})+)\}", doc) or [None, ""])[1])
    body = doc.split("\\begin{document}", 1)[-1]
    print(f"Main file: {main.relative_to(root)}")
    number = 0
    for env in re.finditer(r"\\begin\{(figure\*?|wrapfigure)\}(.*?)\\end\{\1\}", body, re.S):
        content = env.group(2)
        outer = re.sub(r"\\begin\{subfigure\}.*?\\end\{subfigure\}", "", content, flags=re.S)
        captions = re.findall(r"\\caption(?:\[[^\]]*\])?\{", outer)
        if not captions:
            print(f"(unnumbered {env.group(1)} environment)")
            continue
        start = outer.find(captions[0]) + len(captions[0])
        caption = re.sub(r"\s+", " ", outer[start:start + 160])
        first = number + 1
        number += len(captions)
        labels = ", ".join(re.findall(r"\\label\{([^}]+)\}", content)) or "(none)"
        print(f"\nFigure {first}{'–' + str(number) if number > first else ''}  [{env.group(1)}]  label: {labels}")
        print(f"  caption: {caption}…")
        files = re.findall(r"\\includegraphics\*?(?:\[[^\]]*\])?\{([^}]+)\}", content)
        for f in files:
            hit = resolve_graphic(f.strip(), root, dirs)
            if hit is None:
                print(f"  file: {f} (not found)")
                continue
            note = " (EPS: crop from the PDF instead)" if hit.suffix.lower() == ".eps" else ""
            print(f"  file: {hit.relative_to(root).as_posix()}  {hit.stat().st_size / 1024:.0f} KB{note}")
        if not files:
            drawn = re.search(r"\\begin\{(?:tikzpicture|axis)\}|\\input\{[^}]*\}", content)
            print("  file: none" + (" (drawn with LaTeX code: crop from the PDF)" if drawn else " (crop from the PDF)"))
    if number == 0:
        print("The source has no figure environment with a caption.")
    return 0


# ---------- PDF helpers ----------

def parse_pages(spec: str | None, count: int) -> list[int]:
    if not spec:
        return list(range(1, count + 1))
    pages = []
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-", 1)
            pages.extend(range(int(a), int(b) + 1))
        elif part.strip():
            pages.append(int(part))
    return [p for p in pages if 1 <= p <= count]


def page_items(page):
    """Caption blocks, text blocks, and graphics rectangles (images and drawing groups) of a page."""
    import pymupdf

    area = page.rect.width * page.rect.height
    texts, captions = [], []
    for b in page.get_text("blocks"):
        if b[6] != 0:
            continue
        r = pymupdf.Rect(b[:4])
        texts.append((r, b[4]))
        m = CAPTION.match(b[4])
        if m:
            captions.append((int(m.group(1)), r, " ".join(b[4].split())[:70]))
    graphics = []
    for info in page.get_image_info():
        r = pymupdf.Rect(info["bbox"]) & page.rect
        if r.width > 8 and r.height > 8 and r.width * r.height < 0.8 * area:
            graphics.append(("image", r))
    for r in page.cluster_drawings():
        r = pymupdf.Rect(r) & page.rect
        if (r.width > 8 or r.height > 8) and r.width * r.height < 0.8 * area:
            graphics.append(("drawing", r))
    return captions, texts, graphics


def auto_region(page, cap):
    """Rectangle of the figure whose caption block is `cap`, or None."""
    import pymupdf

    _, texts, graphics = page_items(page)
    tx0 = min(r.x0 for r, _ in texts)
    tx1 = max(r.x1 for r, _ in texts)
    if cap.width > 0.6 * (tx1 - tx0):
        band = (tx0 - 6, tx1 + 6)
    else:  # caption of a single column: stay in that column
        band = (cap.x0 - 15, cap.x1 + 15)
    in_band = [r for _, r in graphics if r.x1 > band[0] and r.x0 < band[1]]

    def grow(seeds, upward):
        if not seeds:
            return None
        seeds = sorted(seeds, key=lambda r: -r.y1 if upward else r.y0)
        first = seeds[0]
        if (cap.y0 - first.y1 if upward else first.y0 - cap.y1) > 60:
            return None
        region = pymupdf.Rect(first)
        changed = True
        while changed:
            changed = False
            for r in seeds:
                if region.contains(r):
                    continue
                near = (r.y1 >= region.y0 - GAP) if upward else (r.y0 <= region.y1 + GAP)
                if near:
                    region |= r
                    changed = True
        return region

    above = grow([r for r in in_band if r.y1 <= cap.y0 + 3], upward=True)
    if above is not None:
        top, bottom = above.y0, cap.y0 - 0.5
    else:
        below = grow([r for r in in_band if r.y0 >= cap.y1 - 3], upward=False)
        if below is None:
            return None
        top, bottom = cap.y1 + 0.5, below.y1
    # Short text right above the graphics (a plot title, a panel label) belongs to the figure,
    # but not the running header in the top margin.
    header_zone = 0.075 * page.rect.height
    for r, t in sorted(texts, key=lambda x: -x[0].y1):
        if r.y1 <= top and top - r.y1 < 8 and r.y0 > header_zone and t.count("\n") <= 2 \
                and r.width < 0.7 * (band[1] - band[0]) and r.x1 > band[0] and r.x0 < band[1]:
            top = r.y0
    span = pymupdf.Rect(band[0], top, band[1], bottom)
    parts = [r & span for _, r in graphics if r.intersects(span)]
    parts += [r & span for r, _ in texts if r.intersects(span) and r.y0 >= top - 2 and r.y1 <= bottom + 2]
    parts = [p for p in parts if not p.is_empty]
    if not parts:
        return None
    region = pymupdf.Rect(parts[0])
    for p in parts[1:]:
        region |= p
    return region


# ---------- list ----------

def cmd_list(args) -> int:
    import pymupdf

    doc = pymupdf.open(args.pdf)
    pages = parse_pages(args.pages, doc.page_count)
    shown = 0
    for p in pages:
        page = doc[p - 1]
        captions, _, graphics = page_items(page)
        if not args.pages and not captions:
            continue
        shown += 1
        print(f"\nPage {p} ({page.rect.width:.0f} x {page.rect.height:.0f} pt)")
        for n, r, text in captions:
            print(f"  caption Figure {n}  ({r.x0:.0f}, {r.y0:.0f}, {r.x1:.0f}, {r.y1:.0f})  {text}")
        for k, (kind, r) in enumerate(graphics, 1):
            print(f"  #{k} {'image' if kind == 'image' else 'vector'}  ({r.x0:.0f}, {r.y0:.0f}, {r.x1:.0f}, {r.y1:.0f})")
        if args.preview:
            out = Path(args.preview)
            out.mkdir(parents=True, exist_ok=True)
            tmp = pymupdf.open()
            tmp.insert_pdf(doc, from_page=p - 1, to_page=p - 1)
            tp = tmp[0]
            for n, r, _ in captions:
                tp.draw_rect(r, color=(0, 0.3, 1), width=1)
            for k, (kind, r) in enumerate(graphics, 1):
                color = (0.85, 0, 0) if kind == "image" else (0, 0.6, 0)
                tp.draw_rect(r, color=color, width=0.8)
                tp.insert_text((r.x0 + 1, r.y0 + 8), f"#{k}", fontsize=8, color=color)
            path = out / f"page-{p:03d}.png"
            tp.get_pixmap(dpi=110).save(path)
            print(f"  preview: {path}")
    if not shown:
        print("No caption starting with Figure/Fig. found; give pages with --pages and look at the previews.")
    return 0


# ---------- crop ----------

def save_region(page, rect, dpi: int, out: Path) -> None:
    # Render the whole page and cut the figure out of the bitmap. Rendering only the clipped
    # region, or re-wrapping the page as a vector PDF, changed the colours of some lines in
    # a test paper whose figure relies on drawing state set outside the figure.
    from PIL import Image

    pix = page.get_pixmap(dpi=dpi)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    s = dpi / 72
    box = (int(rect.x0 * s), int(rect.y0 * s), int(rect.x1 * s + 0.999), int(rect.y1 * s + 0.999))
    img.crop(box).save(out)


def cmd_crop(args) -> int:
    import pymupdf

    doc = pymupdf.open(args.pdf)
    if args.rect:
        if not args.page:
            print("--rect needs --page.")
            return 1
        x0, y0, x1, y1 = (float(v) for v in args.rect.split(","))
        pno, rect = args.page - 1, pymupdf.Rect(x0, y0, x1, y1)
    elif args.figure:
        hits = []
        for p in parse_pages(str(args.page) if args.page else None, doc.page_count):
            for n, r, _ in page_items(doc[p - 1])[0]:
                if n == args.figure:
                    hits.append((p, r))
        if not hits:
            print(f"No caption found for Figure {args.figure}; check how the captions are written with list, "
                  "or give --page and --rect.")
            return 1
        if len(hits) > 1:
            print(f"Figure {args.figure} has captions on pages {', '.join(str(p) for p, _ in hits)}; "
                  f"using page {hits[0][0]}. Add --page if that is wrong.")
        p, cap = hits[0]
        pno = p - 1
        rect = auto_region(doc[pno], cap)
        if rect is None:
            print(f"No graphics found for Figure {args.figure} on page {p}; look with list --preview, "
                  "then give --rect.")
            return 1
        rect = (rect + (-args.pad, -args.pad, args.pad, args.pad)) & doc[pno].rect
    else:
        print("Give --figure N, or --page P with --rect x0,y0,x1,y1.")
        return 1

    out = Path(args.out).with_suffix(".png")
    out.parent.mkdir(parents=True, exist_ok=True)
    save_region(doc[pno], rect, args.dpi, out)
    print(f"page {pno + 1}, region ({rect.x0:.1f}, {rect.y0:.1f}, {rect.x1:.1f}, {rect.y1:.1f}) -> {out}"
          f" ({out.stat().st_size / 1024:.0f} KB)")
    print("Open it with Read before using it: no axis labels, legends or subfigure titles cut off, "
          "no body text included.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("source", help="list the source files of every figure")
    s.add_argument("source_dir", type=Path)
    s.set_defaults(func=cmd_source)
    s = sub.add_parser("list", help="list figure captions and graphics regions in the PDF")
    s.add_argument("pdf", type=Path)
    s.add_argument("--pages")
    s.add_argument("--preview", help="render the pages with boxes drawn into this directory")
    s.set_defaults(func=cmd_list)
    s = sub.add_parser("crop", help="crop one figure from the PDF")
    s.add_argument("pdf", type=Path)
    s.add_argument("--figure", type=int)
    s.add_argument("--page", type=int)
    s.add_argument("--rect", help="x0,y0,x1,y1 (PDF points, origin at the top left)")
    s.add_argument("--out", required=True, help="output PNG file")
    s.add_argument("--dpi", type=int, default=300)
    s.add_argument("--pad", type=float, default=3)
    s.set_defaults(func=cmd_crop)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
