# Goals
- Improve the landing page for a fictional offline note app so it is readable, accessible, well structured, and concise.
- Keep the same product story and the same call to action.

# Constraints
- Only edit the files listed under Files.
- Do not add external scripts, stylesheets, or fonts.
- Keep the page as one HTML file and one CSS file.

# Files
- landing/index.html
- landing/style.css

# Dimensions
- readability: 0.30
- accessibility: 0.30
- structure: 0.25
- concision: 0.15

# Gates
- has_title: the page has a non-empty <title>
- has_h1: the page has exactly one <h1>
- lang_set: the <html> element declares a lang attribute
- img_alt: every <img> has an alt attribute
- contrast_ok: body text contrast against the background is at least 4.5:1
- no_external: no <link> or <script> loads from an http(s) URL
- cta_present: the page has an element with the class "cta"

# Strict Gates
true

# Eval
eval/score_landing.py

# Budget
- max_experiments: 6
- time_budget_minutes: 20
