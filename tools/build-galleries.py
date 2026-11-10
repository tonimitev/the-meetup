#!/usr/bin/env python3
"""
Build the photo galleries for the past meetups.

Usage (from the repository root):

    python3 tools/build-galleries.py

What it does, for every folder past/<year-city>/:

  1. Every new photo you dropped into  past/<year-city>/photos/
     is moved to                       past/<year-city>/originals/   (git-ignored, kept only on your computer)
     and a web-sized copy is written to past/<year-city>/photos/      (max 2000 px, ~300-600 KB)
     plus a thumbnail in               past/<year-city>/photos/thumbs/ (max 800 px)
     The web copies are rotated correctly and have their metadata
     (including GPS location) removed.

  2. The gallery in past/<year-city>/index.html is rewritten to show
     every photo in photos/, sorted by file name (phone photo names such
     as 20251114_131904.jpg therefore appear in the order they were taken).

Running it again is safe: photos that are already processed are skipped.
To remove a photo from the website, delete it from photos/ and photos/thumbs/
and run the script again.

Requires Pillow:  python3 -m pip install pillow
"""

import html
import re
import shutil
import sys
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError:
    sys.exit("Pillow is missing. Install it with:  python3 -m pip install pillow")

try:  # optional: iPhone HEIC photos
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIC = True
except ImportError:
    HEIC = False

ROOT = Path(__file__).resolve().parent.parent
PAST = ROOT / "past"
WEB_MAX, WEB_QUALITY = 2000, 82
THUMB_MAX, THUMB_QUALITY = 800, 78
EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}
START, END = "<!-- GALLERY:START -->", "<!-- GALLERY:END -->"


def clean_name(name: str) -> str:
    """'20251114_214430(1).JPG' -> '20251114_214430-1.jpg'"""
    stem = Path(name).stem.lower()
    stem = re.sub(r"[^a-z0-9_-]+", "-", stem).strip("-") or "photo"
    return stem + ".jpg"


def save_resized(src: Path, dst: Path, max_side: int, quality: int) -> None:
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)          # apply the phone's rotation
        im = im.convert("RGB")
        im.thumbnail((max_side, max_side), Image.LANCZOS)
        dst.parent.mkdir(parents=True, exist_ok=True)
        im.save(dst, "JPEG", quality=quality, optimize=True, progressive=True)  # no EXIF -> no GPS


def process_folder(folder: Path) -> list[str]:
    photos, thumbs, originals = folder / "photos", folder / "photos" / "thumbs", folder / "originals"
    photos.mkdir(exist_ok=True)
    added = 0

    for f in sorted(photos.iterdir()):
        if not f.is_file() or f.suffix.lower() not in EXTS:
            continue
        if f.suffix.lower() in {".heic", ".heif"} and not HEIC:
            print(f"  ! skipped {f.name}: HEIC needs  python3 -m pip install pillow-heif")
            continue
        target = photos / clean_name(f.name)
        is_processed = (thumbs / target.name).exists() and f == target
        if is_processed:
            continue
        # New photo: keep the original out of git, write web + thumb versions
        originals.mkdir(exist_ok=True)
        orig = originals / f.name
        shutil.move(str(f), orig)
        save_resized(orig, target, WEB_MAX, WEB_QUALITY)
        save_resized(orig, thumbs / target.name, THUMB_MAX, THUMB_QUALITY)
        added += 1

    names = sorted(p.name for p in photos.glob("*.jpg") if (thumbs / p.name).exists())
    if added:
        print(f"  + {added} new photo(s) processed")
    return names


def gallery_html(names: list[str], alt: str) -> str:
    if not names:
        return (f'{START}\n    <p class="gallery-note">Photos coming soon.</p>\n    {END}')
    alt = html.escape(alt)
    items = "\n".join(
        f'      <a class="gallery__item" href="photos/{n}">'
        f'<img src="photos/thumbs/{n}" alt="{alt}" loading="lazy"></a>'
        for n in names
    )
    return f'{START}\n    <div class="gallery">\n{items}\n    </div>\n    {END}'


def update_page(folder: Path, names: list[str]) -> None:
    page = folder / "index.html"
    text = page.read_text(encoding="utf-8")
    title = re.search(r"<title>(.*?) —", text)
    alt = title.group(1) if title else folder.name
    block = gallery_html(names, alt)

    if START in text:
        text = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda m: block, text, flags=re.S)
    else:
        # First run: replace the original placeholder (note + placeholder grid)
        pattern = r'<p class="gallery-note">.*?</p>\s*<div class="gallery gallery--placeholder">.*?\n    </div>'
        text, n = re.subn(pattern, lambda m: block, text, flags=re.S)
        if not n:
            print(f"  ! could not find the gallery in {page}, left unchanged")
            return
    page.write_text(text, encoding="utf-8")


def main() -> None:
    for folder in sorted(p for p in PAST.iterdir() if p.is_dir()):
        if not (folder / "index.html").exists():
            continue
        print(folder.name)
        names = process_folder(folder)
        update_page(folder, names)
        print(f"  {len(names)} photo(s) in gallery")


if __name__ == "__main__":
    main()
