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

6. **Page-by-page scraping**
   * The "Start" button visits each URL in the left list and extracts
     `name`, `email`, `journal`, `topic`, verification flags and more.
   * If a PDF link is advertised the scraper attempts to pull text; when
     `USE_OCR=1` (default) an OCR pass via Tesseract is used as a fallback.
 * MX record checks can be disabled with `CHECK_MX=0`.
 * The right panel displays emails only while full records remain in
    memory for export.

7. **Data options & statistics**
  * Buttons in the right panel allow exporting all collected fields to
    CSV or Excel, copying the CSV text to the clipboard, or clearing the
    current session.
  * Stats underneath show counts for data items and pages visited,
    tracked for the current day and for the full session.  Daily counters
    reset automatically at midnight while session totals persist until
    cleared.

## Tests

Run the test-suite:
```bash
pytest -q
```

## Building a Windows executable

A PyInstaller spec (`ss_scraper.spec`) and helper script (`build_win.bat`)
are included.  On a Windows machine with Python and PyInstaller
installed, run:

```cmd
build_win.bat
```

The script produces a **single-file** `ss_scraper.exe` in the `dist/`
folder.  The spec automatically collects the required QtWebEngine
assets, including `QtWebEngineProcess.exe`, resources, translations, and
standard Qt plugins.

Tesseract/OCR support is optional; set `USE_OCR=1` when launching the
app if you have Tesseract installed.  The build does not bundle the
Tesseract binary.

## Troubleshooting

* **QtWebEngine missing assets** – ensure the spec and build script are
  used; they copy the `QtWebEngineProcess.exe`, `resources/`,
  `translations/`, and common plugins.
* **QtWebEngine in headless builds** – set
  `QT_QPA_PLATFORM=offscreen` when running tests or executing on a server
  without a display.
* **Tesseract** – OCR is skipped if the Tesseract binary is not found.
  Install it separately if you need OCR functionality.

## Etiquette

The scraper is a proof of concept.  Respect robots.txt and rate limits
when scraping public websites.
