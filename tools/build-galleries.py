#!/usr/bin/env python3
"""
Build the photo and video galleries for the past meetups.

Usage (from the repository root):

    python3 tools/build-galleries.py

What it does, for every folder past/<year-city>/:

  1. Every new photo or video you dropped into  past/<year-city>/photos/
     is moved to                                past/<year-city>/originals/   (git-ignored, stays on your computer)
     and a web version is written back to       past/<year-city>/photos/
       - photos: max 2000 px, ~300-600 KB
       - videos: max 1280 px, H.264/AAC MP4, a few MB per minute
     plus a thumbnail in                        past/<year-city>/photos/thumbs/ (max 800 px)
     Web versions are rotated correctly and have their metadata
     (including GPS location) removed.

  2. The gallery in past/<year-city>/index.html is rewritten to show
     everything in photos/, sorted by file name (phone file names such
     as 20251114_131904.jpg therefore appear in the order they were taken).

Running it again is safe: files that are already processed are skipped.
To remove an item from the website, delete it from photos/ and its
thumbnail from photos/thumbs/, then run the script again.

Requirements (once):
    Pillow  ->  brew install pillow     (see README for alternatives)
    ffmpeg  ->  brew install ffmpeg     (only needed for videos)
"""

import html
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError:
    sys.exit("Pillow is missing. Install it with:  brew install pillow   (see README)")

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
VIDEO_MAX, VIDEO_CRF = 1280, 28
PHOTO_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}
VIDEO_EXTS = {".mp4", ".mov", ".m4v"}
START, END = "<!-- GALLERY:START -->", "<!-- GALLERY:END -->"
FFMPEG = shutil.which("ffmpeg")


def clean_stem(name: str) -> str:
    """'20251114_214430(1).JPG' -> '20251114_214430-1'"""
    stem = Path(name).stem.lower()
    return re.sub(r"[^a-z0-9_-]+", "-", stem).strip("-") or "item"


def video_thumb_name(stem: str) -> str:
    return f"{stem}-video.jpg"


def save_resized(src, dst: Path, max_side: int, quality: int) -> None:
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)          # apply the phone's rotation
        im = im.convert("RGB")
        im.thumbnail((max_side, max_side), Image.LANCZOS)
        dst.parent.mkdir(parents=True, exist_ok=True)
        im.save(dst, "JPEG", quality=quality, optimize=True, progressive=True)  # no EXIF -> no GPS


def run(cmd: list) -> None:
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def compress_video(src: Path, dst: Path, thumb: Path) -> None:
    m = VIDEO_MAX
    scale = f"scale='if(gte(iw,ih),min({m},iw),-2)':'if(gte(iw,ih),-2,min({m},ih))'"
    tmp = dst.with_name(dst.stem + ".tmp.mp4")
    run([FFMPEG, "-y", "-i", str(src), "-map_metadata", "-1", "-vf", scale,
         "-c:v", "libx264", "-preset", "veryfast", "-crf", str(VIDEO_CRF),
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k",
         "-movflags", "+faststart", str(tmp)])
    tmp.replace(dst)
    # Poster frame for the gallery (1 s in, or the first frame for very short clips)
    thumb.parent.mkdir(parents=True, exist_ok=True)
    frame = thumb.with_name(thumb.stem + ".frame.jpg")
    run([FFMPEG, "-y", "-ss", "1", "-i", str(dst), "-frames:v", "1", str(frame)])
    if not frame.exists():
        run([FFMPEG, "-y", "-i", str(dst), "-frames:v", "1", str(frame)])
    save_resized(frame, thumb, THUMB_MAX, THUMB_QUALITY)
    frame.unlink()


def process_folder(folder: Path) -> list:
    photos, thumbs, originals = folder / "photos", folder / "photos" / "thumbs", folder / "originals"
    photos.mkdir(exist_ok=True)
    added = 0

    for f in sorted(photos.iterdir()):
        ext = f.suffix.lower()
        if not f.is_file() or ext not in PHOTO_EXTS | VIDEO_EXTS or ".tmp." in f.name:
            continue
        stem = clean_stem(f.name)

        if ext in VIDEO_EXTS:
            target, thumb = photos / f"{stem}.mp4", thumbs / video_thumb_name(stem)
            if f == target and thumb.exists():
                continue
            if not FFMPEG:
                print(f"  ! skipped {f.name}: videos need ffmpeg  (brew install ffmpeg)")
                continue
            print(f"  compressing {f.name} ...")
            originals.mkdir(exist_ok=True)
            orig = originals / f.name
            shutil.move(str(f), orig)
            compress_video(orig, target, thumb)
        else:
            if ext in {".heic", ".heif"} and not HEIC:
                print(f"  ! skipped {f.name}: HEIC needs  pillow-heif")
                continue
            target, thumb = photos / f"{stem}.jpg", thumbs / f"{stem}.jpg"
            if f == target and thumb.exists():
                continue
            originals.mkdir(exist_ok=True)
            orig = originals / f.name
            shutil.move(str(f), orig)
            save_resized(orig, target, WEB_MAX, WEB_QUALITY)
            save_resized(orig, thumb, THUMB_MAX, THUMB_QUALITY)
        added += 1

    items = []
    for p in photos.iterdir():
        if p.suffix == ".jpg" and (thumbs / p.name).exists():
            items.append((p.name, p.name))
        elif p.suffix == ".mp4" and ".tmp." not in p.name and (thumbs / video_thumb_name(p.stem)).exists():
            items.append((p.name, video_thumb_name(p.stem)))
    items.sort()
    if added:
        print(f"  + {added} new item(s) processed")
    return items


def gallery_html(items: list, alt: str) -> str:
    if not items:
        return f'{START}\n    <p class="gallery-note">Photos coming soon.</p>\n    {END}'
    alt = html.escape(alt)
    lines = []
    for name, thumb in items:
        video = name.endswith(".mp4")
        cls = "gallery__item gallery__item--video" if video else "gallery__item"
        label = f"{alt} (video)" if video else alt
        lines.append(f'      <a class="{cls}" href="photos/{name}">'
                     f'<img src="photos/thumbs/{thumb}" alt="{label}" loading="lazy"></a>')
    return f'{START}\n    <div class="gallery">\n' + "\n".join(lines) + f'\n    </div>\n    {END}'


def update_page(folder: Path, items) -> None:
    page = folder / "index.html"
    text = page.read_text(encoding="utf-8")
    title = re.search(r"<title>(.*?) —", text)
    alt = title.group(1) if title else folder.name
    block = gallery_html(items, alt)

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
    if not FFMPEG:
        print("Note: ffmpeg not found, videos will be skipped (brew install ffmpeg).")
    for folder in sorted(p for p in PAST.iterdir() if p.is_dir()):
        if not (folder / "index.html").exists():
            continue
        print(folder.name)
        items = process_folder(folder)
        update_page(folder, items)
        videos = sum(1 for n, _ in items if n.endswith(".mp4"))
        print(f"  {len(items) - videos} photo(s), {videos} video(s) in gallery")


if __name__ == "__main__":
    main()
