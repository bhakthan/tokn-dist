"""Synthetic design evaluator for the autodesign landing-page walkthrough.

Stdlib only. Reads landing/index.html and landing/style.css next to this
folder and prints one JSON object on stdout in the autodesign evaluator
contract: {"dimensions": {...}, "gates": {...}, "metadata": {...}}.

The scoring rules are deliberately simple and readable. They are a teaching
harness, not a design-quality standard.
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML_PATH = os.path.join(ROOT, "landing", "index.html")
CSS_PATH = os.path.join(ROOT, "landing", "style.css")


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def hex_to_rgb(value):
    value = value.lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    if not re.fullmatch(r"[0-9a-fA-F]{6}", value):
        return None
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def relative_luminance(rgb):
    def channel(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg, bg):
    l1, l2 = relative_luminance(fg), relative_luminance(bg)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def body_rule(css):
    match = re.search(r"body\s*\{([^}]*)\}", css)
    return match.group(1) if match else ""


def css_value(block, prop):
    match = re.search(rf"\b{prop}\s*:\s*([^;]+);", block)
    return match.group(1).strip() if match else None


def clamp(value):
    return max(0, min(100, value))


def main():
    html = read(HTML_PATH)
    css = read(CSS_PATH)
    block = body_rule(css)

    fg = hex_to_rgb(css_value(block, "color") or "")
    bg = hex_to_rgb(css_value(block, "background") or "")
    ratio = contrast_ratio(fg, bg) if fg and bg else 1.0
    line_height = css_value(block, "line-height")
    line_height = float(line_height) if line_height and re.fullmatch(r"[0-9.]+", line_height) else 1.0

    h1_count = len(re.findall(r"<h1[\s>]", html))
    section_count = len(re.findall(r"<section[\s>]", html))
    has_title = bool(re.search(r"<title>\s*\S", html))
    lang_set = bool(re.search(r"<html[^>]*\blang=", html))
    imgs = re.findall(r"<img\b[^>]*>", html)
    img_alt = all(re.search(r"\balt=", tag) for tag in imgs)
    external = re.findall(r"<(?:link|script)\b[^>]*\b(?:href|src)=[\"']https?://", html)
    no_external = not external
    cta_present = bool(re.search(r"class=[\"'][^\"']*\bcta\b", html))
    paragraphs = re.findall(r"<p>(.*?)</p>", html, flags=re.S)
    words = sum(len(re.sub(r"<[^>]+>", " ", p).split()) for p in paragraphs)

    if ratio >= 7:
        readability = 100
    elif ratio >= 4.5:
        readability = 75
    elif ratio >= 3:
        readability = 40
    else:
        readability = 10
    if line_height < 1.4:
        readability -= 15

    accessibility = 100
    if not lang_set:
        accessibility -= 30
    if not img_alt:
        accessibility -= 30
    if ratio < 4.5:
        accessibility -= 40

    structure = 100
    if h1_count != 1:
        structure -= 35
    if section_count < 2:
        structure -= 25
    if not has_title:
        structure -= 25

    concision = 100 if 40 <= words <= 120 else 60

    dimensions = {
        "readability": clamp(readability),
        "accessibility": clamp(accessibility),
        "structure": clamp(structure),
        "concision": clamp(concision),
    }
    gates = {
        "has_title": has_title,
        "has_h1": h1_count == 1,
        "lang_set": lang_set,
        "img_alt": img_alt,
        "contrast_ok": ratio >= 4.5,
        "no_external": no_external,
        "cta_present": cta_present,
    }
    metadata = {
        "contrast_ratio": round(ratio, 2),
        "line_height": line_height,
        "h1_count": h1_count,
        "section_count": section_count,
        "body_words": words,
    }
    json.dump({"dimensions": dimensions, "gates": gates, "metadata": metadata}, sys.stdout)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
