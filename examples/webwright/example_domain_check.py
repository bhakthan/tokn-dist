"""Reference artifact: the kind of script the webwright pattern produces.

Reads the heading and first link on https://example.com, writes result.json,
page.png and run.log next to this file. Nothing is written outside this folder.

Rerun:  python example_domain_check.py
"""

import json
import logging
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "https://example.com"
OUT_DIR = Path(__file__).resolve().parent / "out"
OUT_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    filename=OUT_DIR / "run.log",
    filemode="w",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("webwright")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            log.info("navigating to %s", URL)
            page.goto(URL, wait_until="domcontentloaded", timeout=30_000)
            page.wait_for_selector("h1", timeout=10_000)
            log.info("main heading rendered")

            heading = page.locator("h1").first.inner_text().strip()
            first_link = page.locator("a").first.inner_text().strip()
            log.info("heading=%r first_link=%r", heading, first_link)

            (OUT_DIR / "result.json").write_text(
                json.dumps({"heading": heading, "first_link": first_link}, indent=2),
                encoding="utf-8",
            )
            page.screenshot(path=OUT_DIR / "page.png", full_page=True)
            log.info("wrote result.json and page.png")
        finally:
            browser.close()

    print((OUT_DIR / "result.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
