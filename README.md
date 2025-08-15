# Codex SS Scraper

Minimal MVP of a 3‑panel desktop scraper used for Codex tasks.  The
application verifies a license key before showing the UI and ships with
basic link collection utilities.

## Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
2. **Provide RSA public key**
   * Create `.env` with `PUBLIC_KEY_PEM` or place a PEM file at
     `keys/public_key.pem`.
3. **Run the application**
   ```bash
   python ss_ui.py
   ```
   On first launch a license dialog prompts for email and key.  A valid
   license is stored at `%APPDATA%/SSScraper/config.json` and reused on
   subsequent runs.  Delete this file to reset.  After verification the
   browser loads `https://www.google.com/`.

4. **Admin mode**
   * Set environment variable `ADMIN_MODE=1` to enable the Admin dialog.
   * Press `Ctrl+Alt+A` in the main window to manage licensed users stored
     in `data/auth.db`.  Back up this file to preserve user records.

5. **Link collection**
   * The "Scrape Links" button uses per-site plugins defined in
     `sites/plugins.py` with a generic fallback to extract article-style
     anchors.
   * URLs are normalized (fragments and tracking params removed),
     deduplicated, and a short scroll loop (≤8s) attempts to load more
     results politely.

## Tests

Run the test-suite:
```bash
pytest -q
```

## Building a Windows executable

A PyInstaller spec is provided.  From Windows run:
```cmd
build_win.bat
```
This generates a single-file executable in the `dist/` directory.  Qt
WebEngine resources are bundled automatically.  Tesseract is optional –
set `USE_OCR=1` to enable if installed.

## Troubleshooting

* **QtWebEngine** – In headless environments set
  `QT_QPA_PLATFORM=offscreen`.
* **Tesseract** – The OCR step is skipped if Tesseract is not available;
  install separately when needed.

## Etiquette

The scraper is a proof of concept.  Respect robots.txt and rate limits
when scraping public websites.
