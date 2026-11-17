# Task: rebuild the page in target.png

`target.png` (1280x720) shows a landing page. Write `index.html` (one file, inline CSS)
that reproduces it as closely as you can.

Rules
- Create or edit only `index.html` and files under `out/`.
- Work from the target image only.

Workflow
- Render with vis_render (kind=html, source=index.html, width=1280, height=720, step=<n>;
  it writes out/render_<n>.png).
- Compare with vis_diff against target.png, fix the high-severity items first, use
  vis_inspect or vis_align to confirm details, and repeat.
- Stop when vis_diff reports no high-severity discrepancies or you are near the step limit.
