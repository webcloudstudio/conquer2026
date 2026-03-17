#!/usr/bin/env python3
"""
Convert original 1987 Conquer nroff docs to dark-themed HTML.
Run from: new/docs/  (writes output to new/docs/original/)

Usage:
    python3 convert_nr.py
"""

import html
import os
import re

SRC_DIR = "../../original/Docs"
OUT_DIR = "original"

# Map from .RF key to output filename (within original/)
RF_MAP = {
    "Overview":    "overview.html",
    "Beginnings":  "beginnings.html",
    "Nations":     "nations.html",
    "Sectors":     "sectors.html",
    "Warfare":     "warfare.html",
    "Movement":    "movement.html",
    "Powers":      "powers.html",
    "Economics":   "economics.html",
    "God Powers":  "god-powers.html",
    "God-Powers":  "god-powers.html",
    "Functions":   "functions.html",
    "Display":     "display.html",
    "Quickies":    "quickies.html",
    "Helpfiles":   "helpfiles.html",
    "Customize":   "customize.html",
    "Xchanges":    "xchanges.html",
    "Version":     "xchanges.html",
}

# Input file → output file
FILES = [
    ("Overview.nr",   "overview.html",   "Overview"),
    ("Beginnings.nr", "beginnings.html", "Beginners Guide"),
    ("Nations.nr",    "nations.html",    "Races & Classes"),
    ("Sectors.nr",    "sectors.html",    "Sectors"),
    ("Warfare.nr",    "warfare.html",    "Warfare"),
    ("Movement.nr",   "movement.html",   "Movement"),
    ("Powers.nr",     "powers.html",     "Magic Powers"),
    ("Economics.nr",  "economics.html",  "Economics"),
    ("God-Powers.nr", "god-powers.html", "God Mode"),
    ("Functions.nr",  "functions.html",  "Command Reference"),
    ("Display.nr",    "display.html",    "Display Guide"),
    ("Quickies.nr",   "quickies.html",   "Charts & Summaries"),
    ("Helpfiles.nr",  "helpfiles.html",  "Help Files"),
    ("Customize.nr",  "customize.html",  "Customization"),
    ("Xchanges.nr",   "xchanges.html",   "Communication"),
]

SIDEBAR_LINKS = [
    ("overview.html",   "Overview"),
    ("beginnings.html", "Beginners Guide"),
    ("nations.html",    "Races &amp; Classes"),
    ("sectors.html",    "Sectors"),
    ("warfare.html",    "Warfare"),
    ("movement.html",   "Movement"),
    ("powers.html",     "Magic Powers"),
    ("economics.html",  "Economics"),
    ("god-powers.html", "God Mode"),
    ("functions.html",  "Command Reference"),
    ("display.html",    "Display Guide"),
    ("quickies.html",   "Charts &amp; Summaries"),
    ("helpfiles.html",  "Help Files"),
    ("customize.html",  "Customization"),
    ("xchanges.html",   "Communication"),
]


def escape(text: str) -> str:
    """HTML-escape text, also convert \\e to backslash."""
    text = text.replace("\\e", "\\")
    return html.escape(text)


def sidebar_html(active_file: str) -> str:
    items = []
    for fname, label in SIDEBAR_LINKS:
        cls = ' class="active"' if fname == active_file else ""
        items.append(f'    <li><a href="{fname}"{cls}>{label}</a></li>')
    return "\n".join(items)


def page_template(title: str, active_file: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)} — Conquer Original Docs</title>
<link rel="stylesheet" href="../style.css">
</head>
<body>
<nav class="sidebar">
  <div class="logo">⚔️ Original Docs (1987)</div>
  <ul>
    <li><a href="../index.html">← New Docs</a></li>
{sidebar_html(active_file)}
  </ul>
</nav>
<main>
{body}
</main>
</body>
</html>
"""


def convert_nr(src_path: str, out_file: str, nav_label: str) -> str:
    """Parse a .nr file and return HTML body content."""
    with open(src_path, encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    parts: list[str] = []
    in_pre = False
    pre_class = ""
    in_dl = False
    it_buf: list[str] = []  # buffer for current .IT item

    def flush_it():
        nonlocal it_buf
        if not it_buf:
            return
        content = " ".join(it_buf).strip()
        it_buf = []
        # Try to split on ' -- ' for dt/dd
        if " -- " in content:
            term, _, rest = content.partition(" -- ")
            parts.append(f"<dt>{escape(term.strip())}</dt><dd>{escape(rest.strip())}</dd>")
        else:
            parts.append(f"<dt>{escape(content)}</dt>")

    def flush_pre():
        nonlocal in_pre, pre_class
        parts.append(f"</pre>")
        in_pre = False
        pre_class = ""

    i = 0
    chapter_title = nav_label

    while i < len(lines):
        raw = lines[i].rstrip("\n")
        stripped = raw.strip()

        # --- Macros ---
        if stripped.startswith(".CH "):
            m = re.match(r'\.CH\s+"(.+)"', stripped)
            if m:
                chapter_title = m.group(1)
                parts.append(f"<h1>{escape(chapter_title)}</h1>")

        elif stripped.startswith(".CS "):
            flush_it()
            if in_dl:
                parts.append("</dl>")
                in_dl = False
            m = re.match(r'\.CS\s+"(.+)"', stripped)
            if m:
                parts.append(f'<h2>{escape(m.group(1))}</h2>')

        elif stripped == ".CE":
            flush_it()
            if in_dl:
                parts.append("</dl>")
                in_dl = False

        elif stripped == ".PP":
            if not in_pre:
                flush_it()
                parts.append("<p>")

        elif stripped == ".IT":
            if not in_dl:
                parts.append("<dl>")
                in_dl = True
            else:
                flush_it()

        elif stripped == ".UT":
            flush_it()
            if in_dl:
                parts.append("</dl>")
                in_dl = False

        elif stripped in (".NT", ".ST", ".TT"):
            if not in_pre:
                parts.append('<p class="indent">')

        elif stripped == ".SB":
            flush_it()
            parts.append('<pre class="screen">')
            in_pre = True
            pre_class = "screen"

        elif stripped == ".SE":
            if in_pre:
                flush_pre()

        elif stripped == ".TB":
            flush_it()
            parts.append('<pre class="table">')
            in_pre = True
            pre_class = "table"

        elif stripped == ".TE":
            if in_pre:
                flush_pre()

        elif stripped.startswith(".RF "):
            # .RF "key" "name"
            m = re.match(r'\.RF\s+"([^"]+)"\s+"([^"]+)"', stripped)
            if m:
                key = m.group(1)
                name = m.group(2)
                href = RF_MAP.get(key, "#")
                parts.append(
                    f'<p class="see-also">See also: <a href="{href}">{escape(name)}</a></p>'
                )
            # Some .RF lines have trailing plain text on the next line — handled as a paragraph

        elif stripped.startswith("."):
            # Unknown macro — skip silently
            pass

        else:
            # Regular text line
            if in_pre:
                # Preserve whitespace exactly; escape HTML
                parts.append(escape(raw))
            elif in_dl:
                # Content for current .IT item
                if stripped:
                    it_buf.append(stripped)
            else:
                # Normal paragraph text
                if stripped:
                    parts.append(escape(stripped) + " ")
                else:
                    # Blank line — close current paragraph
                    parts.append("</p><p>")

        i += 1

    # Close any open structures
    flush_it()
    if in_dl:
        parts.append("</dl>")
    if in_pre:
        parts.append("</pre>")

    # Join and clean up empty paragraphs
    body = "\n".join(parts)
    body = re.sub(r"<p>\s*</p>", "", body)
    body = re.sub(r"<p>\s*<p>", "<p>", body)
    body = re.sub(r"</p>\s*</p>", "</p>", body)

    return body


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    for src_file, out_file, label in FILES:
        src_path = os.path.join(SRC_DIR, src_file)
        if not os.path.exists(src_path):
            print(f"  SKIP (not found): {src_path}")
            continue

        body = convert_nr(src_path, out_file, label)
        full_html = page_template(label, out_file, body)

        out_path = os.path.join(OUT_DIR, out_file)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(full_html)
        print(f"  OK: {out_path}")

    print(f"\nDone. {len(FILES)} files processed.")


if __name__ == "__main__":
    main()
