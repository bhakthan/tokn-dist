#!/usr/bin/env bash
# fetch-photos.sh - download the three demo photos from Wikimedia Commons into photos/.
# The photos are not committed. Each one is checked to be 1280 px wide, and the
# licence and author are printed from the file's own metadata.
# Usage: ./fetch-photos.sh
# Needs: curl and python3 (3.8+). Both are checked before anything is downloaded.
set -euo pipefail
cd "$(dirname "$0")"

fail() { printf '[!] %s\n' "$1" >&2; exit 1; }
note() { printf '[*] %s\n' "$1"; }

problems=()
command -v curl >/dev/null 2>&1 || problems+=("Missing: curl (downloads the photos). Install: brew install curl (macOS) or sudo apt install curl (Debian/Ubuntu).")
command -v python3 >/dev/null 2>&1 || problems+=("Missing: python3 (reads the Commons metadata and checks the image size). Install: brew install python (macOS), sudo apt install python3 (Debian/Ubuntu), or winget install Python.Python.3.12 (Windows).")
if [ "${#problems[@]}" -gt 0 ]; then
  printf 'Preflight found %d problem(s):\n\n' "${#problems[@]}" >&2
  for p in ${problems[@]+"${problems[@]}"}; do printf -- '- %s\n\n' "$p" >&2; done
  exit 1
fi

UA="tokn-dist-examples/insurance-loss-inspection (demo photo download; read-only)"
mkdir -p photos

# Reads the Commons API response on stdin and prints: thumburl, width, licence, author, page.
PARSE_PY='
import json, sys
data = json.load(sys.stdin)
page = next(iter(data["query"]["pages"].values()))
info = (page.get("imageinfo") or [{}])[0]
meta = info.get("extmetadata", {})
def val(key):
    return (meta.get(key) or {}).get("value", "unknown")
import re
author = re.sub(r"<[^>]+>", "", val("Artist")).strip() or "unknown"
print("\t".join([info.get("thumburl", ""), str(info.get("thumbwidth", "")),
                  val("LicenseShortName"), author, info.get("descriptionurl", "")]))
'

# Reads a JPEG's pixel size from its start-of-frame marker, using only the standard library.
JPEG_SIZE_PY='
import sys
d = open(sys.argv[1], "rb").read()
i = 2
while i < len(d) - 9:
    if d[i] != 0xFF:
        i += 1
        continue
    m = d[i + 1]
    if m in (0xC0, 0xC1, 0xC2):
        print(int.from_bytes(d[i + 7:i + 9], "big"), int.from_bytes(d[i + 5:i + 7], "big"))
        sys.exit(0)
    i += 2 + int.from_bytes(d[i + 2:i + 4], "big")
sys.exit(1)
'

fetch_one() {
  local title="$1" file="$2"
  local api json parsed thumb width licence author page dest size
  api="https://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo&iiprop=url|extmetadata&iiurlwidth=1280&format=json&titles=$(python3 -c 'import sys,urllib.parse;print(urllib.parse.quote(sys.argv[1]))' "$title")"
  json="$(curl -fsS -A "$UA" "$api")" || fail "Could not reach the Wikimedia Commons API for $title. Check your network and retry."
  parsed="$(printf '%s' "$json" | python3 -c "$PARSE_PY")" || fail "Commons returned no usable data for $title."
  IFS=$'\t' read -r thumb width licence author page <<<"$parsed"
  [ -n "$thumb" ] || fail "Commons returned no thumbnail URL for $title."
  if [ "$width" != "1280" ]; then fail "$title is ${width:-?} px wide, expected 1280. The file may have changed on Commons."; fi

  dest="photos/$file"
  curl -fsSL -A "$UA" -o "$dest" "$thumb" || fail "Download failed for $file."
  size="$(python3 -c "$JPEG_SIZE_PY" "$dest")" || fail "$file is not a readable JPEG."
  set -- $size
  if [ "$1" != "1280" ]; then fail "$file decodes to ${1}x${2}, expected 1280 px wide."; fi
  note "$file: ${1}x${2}, licence $licence, author $author"
  note "  $page"
}

fetch_one "File:2017 Toyota Rav4 XLE Hybrid AWD-I (36942379162).jpg" "suv-front.jpg"
fetch_one "File:2010-03-08 Shattered side mirror on BMW.jpg" "side-mirror.jpg"
fetch_one "File:20171118 damaged Hyundai Grand starex-1.jpg" "van-side.jpg"

note "Done. Photos are in photos/. Attribution is in ATTRIBUTION.md."
