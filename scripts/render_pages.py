"""Render PDF pages to PNG, optionally tiled into contact sheets, for visual review.

Usage:
    python -P render_pages.py <pdf> <out_dir> [--pages 1-5,9] [--dpi 60] [--sheet 3x2]

Without --sheet each page is saved as page-NNN.png. With --sheet CxR the pages
are tiled C columns by R rows into sheet-NN_pA-B.png, with each page number
drawn in its corner. Contact sheets are the quickest way to scan a long
document for overlapping figure labels, overflowing tables and bad page
breaks; re-render suspicious pages alone at --dpi 150 to read the details.

Needs PyMuPDF (and Pillow for --sheet). Run it with `python -P` rather than
`-I`, which would hide PyMuPDF if it is installed in the user site.
"""
import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

import pymupdf  # noqa: E402


def parse_pages(spec: str | None, count: int) -> list[int]:
    if not spec:
        return list(range(1, count + 1))
    pages = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            pages.extend(range(int(a), int(b) + 1))
        elif part:
            pages.append(int(part))
    return [p for p in pages if 1 <= p <= count]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf", type=Path)
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--pages", help="e.g. 1-5,9; all pages by default")
    ap.add_argument("--dpi", type=int, default=None, help="default: 60 for sheets, 110 for single pages")
    ap.add_argument("--sheet", help="columns x rows of a contact sheet, e.g. 3x2")
    args = ap.parse_args()

    doc = pymupdf.open(args.pdf)
    pages = parse_pages(args.pages, doc.page_count)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    dpi = args.dpi or (60 if args.sheet else 110)

    if not args.sheet:
        for p in pages:
            path = args.out_dir / f"page-{p:03d}.png"
            doc[p - 1].get_pixmap(dpi=dpi).save(path)
            print(path)
        return 0

    from PIL import Image, ImageDraw, ImageFont

    cols, rows = (int(x) for x in args.sheet.lower().split("x"))
    per = cols * rows
    try:
        font = ImageFont.load_default(size=18)
    except TypeError:  # Pillow < 10.1
        font = ImageFont.load_default()
    gap = 12
    for s in range(0, len(pages), per):
        batch = pages[s:s + per]
        ims = []
        for p in batch:
            pix = doc[p - 1].get_pixmap(dpi=dpi)
            ims.append(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
        w = max(im.width for im in ims)
        h = max(im.height for im in ims)
        sheet = Image.new("RGB", (cols * w + (cols - 1) * gap, rows * h + (rows - 1) * gap), (150, 150, 150))
        draw = ImageDraw.Draw(sheet)
        for k, (p, im) in enumerate(zip(batch, ims)):
            r, c = divmod(k, cols)
            x, y = c * (w + gap), r * (h + gap)
            sheet.paste(im, (x, y))
            draw.rectangle([x, y, x + 52, y + 26], fill=(20, 20, 20))
            draw.text((x + 6, y + 3), str(p), fill=(255, 255, 255), font=font)
        path = args.out_dir / f"sheet-{s // per + 1:02d}_p{batch[0]}-{batch[-1]}.png"
        sheet.save(path)
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
