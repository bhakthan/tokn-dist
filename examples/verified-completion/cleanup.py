"""Remove only a marked verified-completion run directory created under the system temp root."""

import shutil
import sys
import tempfile
from pathlib import Path

MARKER = ".tokn-verified-completion-run"
MARKER_VALUE = "Disposable verified-completion workspace; created by fixtures.py\n"
PREFIX = "tokn-verified-completion-"


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: python cleanup.py <marked-workspace>")
    supplied = Path(sys.argv[1])
    if supplied.is_symlink():
        raise SystemExit("refusing to remove a symlink")
    workspace = supplied.resolve(strict=True)
    temp_root = Path(tempfile.gettempdir()).resolve()
    if workspace.parent != temp_root or not workspace.name.startswith(PREFIX):
        raise SystemExit(f"refusing to remove a path outside a dedicated temp workspace: {workspace}")
    marker = workspace / MARKER
    if marker.is_symlink() or not marker.is_file() or marker.read_text(encoding="utf-8") != MARKER_VALUE:
        raise SystemExit(f"refusing to remove an unmarked or unrecognized workspace: {workspace}")
    shutil.rmtree(workspace)
    print(f"removed marked workspace: {workspace}")


if __name__ == "__main__":
    main()
