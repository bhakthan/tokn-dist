"""Offline structure checker for a generated TaskFlow tree.

Reads local files only. Makes no network calls and writes nothing.
Usage: python check_taskflow.py <path-to-generated-taskflow-folder>
"""
import ast
import json
import sys
from pathlib import Path

EXPECTED = [
    "backend/app.py",
    "backend/models.py",
    "backend/database.py",
    "backend/routes/__init__.py",
    "backend/routes/tasks.py",
    "backend/routes/projects.py",
    "backend/requirements.txt",
    "frontend/index.html",
    "frontend/styles.css",
    "frontend/src/main.ts",
    "frontend/src/api.ts",
    "frontend/src/types.ts",
    "frontend/src/components/TaskList.ts",
    "frontend/src/components/TaskForm.ts",
    "frontend/src/components/ProjectSidebar.ts",
    "frontend/tsconfig.json",
    "README.md",
]


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    failures = []
    present = 0

    for rel in EXPECTED:
        if (root / rel).is_file():
            present += 1
        else:
            failures.append(f"missing file: {rel}")

    for py in sorted(root.glob("backend/**/*.py")):
        try:
            ast.parse(py.read_text(encoding="utf-8"), filename=str(py))
        except SyntaxError as exc:
            failures.append(f"python syntax error in {py.relative_to(root)}: {exc.msg} (line {exc.lineno})")

    tsconfig = root / "frontend" / "tsconfig.json"
    if tsconfig.is_file():
        try:
            json.loads(tsconfig.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            failures.append(f"frontend/tsconfig.json is not valid JSON: {exc}")

    index = root / "frontend" / "index.html"
    if index.is_file():
        html = index.read_text(encoding="utf-8")
        for needle in ('id="app"', 'id="sidebar"', 'id="content"', 'id="task-list"'):
            if needle not in html:
                failures.append(f"frontend/index.html lacks {needle}")

    for line in failures:
        print("FAIL", line)
    print(f"{present} of {len(EXPECTED)} expected files present")
    print("PASS" if not failures else f"FAILED ({len(failures)} problem(s))")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
