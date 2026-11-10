# The Meetup

Static website for our annual meetup of magicians from around the world.
Plain HTML/CSS/JS, no build step, ready for GitHub Pages.

## Structure

```
index.html                     Home: hero, story, Edinburgh 2026, planned events, past meetups
assets/css/style.css           All styles
assets/js/main.js              Photo slots, scroll effects, gallery lightbox
images/hero/                   hero.jpg              → hero background
images/2026-edinburgh/         edinburgh.jpg         → upcoming event photo
                               the-grimoire.jpg      → The Grimoire card
                               activity-welcome.jpg  → Welcome Evening card
                               activity-sessions.jpg → Close-up Sessions card
                               activity-city.jpg     → Exploring Edinburgh card
past/<year-city>/index.html    Gallery page for each past meetup
past/<year-city>/cover.jpg     Cover shown on the home page card
past/<year-city>/photos/       Sorted photos for that gallery
```

Any image slot shows a placeholder until a file with the matching name exists.

## Adding photos

1. Copy the photos for an event into `past/<year-city>/photos/` (straight from the phone is fine).
2. From the repository root run:

   ```
   python3 tools/build-galleries.py
   ```

   This moves the full-size originals to `past/<year-city>/originals/` (git-ignored, they stay on your computer),
   writes web-sized copies (max 2000px, location data removed) to `photos/` plus thumbnails to `photos/thumbs/`,
   and rewrites the gallery in that city's `index.html`. Photos are shown sorted by file name.
3. Commit and push.

To remove a photo, delete it from `photos/` and `photos/thumbs/` and run the script again.
Optional: replace `past/<year-city>/cover.jpg` with one of your own photos for the home page card.

### Installing Pillow (needed once)

The script needs the Pillow image library. On a Mac with Homebrew Python, `pip install` is blocked
("externally-managed-environment"), so install it through Homebrew:

```
brew install pillow
```

If the script still reports that Pillow is missing, use a virtual environment inside the project instead
(`.venv/` is git-ignored):

```
python3 -m venv .venv
.venv/bin/pip install pillow
.venv/bin/python tools/build-galleries.py
```

With the virtual environment, always run the script as `.venv/bin/python tools/build-galleries.py`.
Avoid `pip install --break-system-packages`, it can break the Homebrew Python installation.

## Local preview

```
python3 -m http.server 8000
```

Then open http://localhost:8000.

## Deploy

GitHub → Settings → Pages → Source: *Deploy from a branch* → `main` / root.
