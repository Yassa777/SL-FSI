#!/usr/bin/env python3
"""
Generate PDF: Reserve Adequacy Complete Methodology

Converts the comprehensive markdown methodology document to a styled academic PDF
using WeasyPrint (markdown -> HTML -> CSS-styled PDF).

Run: python generate_methodology_pdf.py
     (or: .venv/bin/python generate_methodology_pdf.py)
"""

import re
from pathlib import Path
import markdown
from weasyprint import HTML

INPUT_MD = Path("DOCS/RESERVE_ADEQUACY_METHODOLOGY_COMPLETE.md")
OUTPUT_PDF = Path("DOCS/RESERVE_ADEQUACY_METHODOLOGY_COMPLETE.pdf")

# --- Academic-style CSS -----------------------------------------------------------

CSS = """
@page {
    size: A4;
    margin: 25mm 20mm 25mm 20mm;
    @bottom-center {
        content: counter(page);
        font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
        font-size: 9pt;
        color: #888;
    }
    @top-left {
        content: "Reserve Adequacy Analysis — Complete Methodology";
        font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
        font-size: 8pt;
        color: #999;
    }
    @top-right {
        content: "SL-FSI Project · January 2026";
        font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
        font-size: 8pt;
        color: #999;
    }
}

@page :first {
    @top-left { content: ""; }
    @top-right { content: ""; }
}

body {
    font-family: "Georgia", "Times New Roman", serif;
    font-size: 11pt;
    line-height: 1.55;
    color: #1a1a1a;
    text-align: justify;
    hyphens: auto;
}

/* Title block */
h1 {
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    font-size: 22pt;
    font-weight: 700;
    color: #003366;
    text-align: center;
    margin-top: 40mm;
    margin-bottom: 4mm;
    line-height: 1.25;
    page-break-before: avoid;
}

/* Subtitle lines (bold paragraphs right after h1) */
h1 + p, h1 + p + p, h1 + p + p + p {
    text-align: center;
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    color: #555;
}

h2 {
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    font-size: 15pt;
    font-weight: 700;
    color: #003366;
    margin-top: 18pt;
    margin-bottom: 8pt;
    border-bottom: 1.5pt solid #003366;
    padding-bottom: 3pt;
    page-break-after: avoid;
}

h3 {
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    font-size: 12pt;
    font-weight: 600;
    color: #333;
    margin-top: 14pt;
    margin-bottom: 6pt;
    page-break-after: avoid;
}

h4 {
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    font-size: 11pt;
    font-weight: 600;
    color: #444;
    margin-top: 10pt;
    margin-bottom: 4pt;
}

p {
    margin-bottom: 7pt;
    orphans: 3;
    widows: 3;
}

/* Tables */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 10pt 0 14pt 0;
    font-size: 9.5pt;
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    page-break-inside: avoid;
}

thead th {
    background-color: #003366;
    color: white;
    font-weight: 600;
    padding: 6pt 8pt;
    text-align: left;
    border: 0.5pt solid #003366;
}

tbody td {
    padding: 5pt 8pt;
    border: 0.5pt solid #ccc;
    vertical-align: top;
}

tbody tr:nth-child(even) {
    background-color: #f7f9fc;
}

/* Code blocks — wrap long lines instead of overflowing */
pre {
    background-color: #f5f5f0;
    border: 0.5pt solid #ddd;
    border-left: 3pt solid #003366;
    padding: 8pt 12pt;
    font-family: "Menlo", "Courier New", Courier, monospace;
    font-size: 8.5pt;
    line-height: 1.45;
    margin: 8pt 0 12pt 0;
    page-break-inside: avoid;
    white-space: pre-wrap;
    word-wrap: break-word;
    overflow-wrap: break-word;
}

code {
    font-family: "Menlo", "Courier New", Courier, monospace;
    font-size: 9pt;
    background-color: #f0f0ec;
    padding: 1pt 3pt;
    border-radius: 2pt;
}

pre code {
    background: none;
    padding: 0;
}

/* Block quotes (used for formulas / emphasis) */
blockquote {
    border-left: 3pt solid #6699cc;
    margin: 10pt 0 10pt 0;
    padding: 6pt 14pt;
    background-color: #f0f5fa;
    font-style: italic;
    color: #333;
}

/* Lists */
ul, ol {
    margin: 6pt 0 10pt 20pt;
}

li {
    margin-bottom: 3pt;
}

/* Horizontal rules */
hr {
    border: none;
    border-top: 1pt solid #ccc;
    margin: 16pt 0;
}

/* Strong / emphasis */
strong {
    color: #1a1a1a;
}

/* Formula display blocks */
.math-block {
    font-family: "Menlo", "Courier New", Courier, monospace;
    font-size: 10.5pt;
    color: #003366;
    background-color: #f0f5fa;
    padding: 10pt 14pt;
    margin: 10pt 0 14pt 0;
    border: 0.5pt solid #b0c4de;
    border-radius: 3pt;
    text-align: center;
    page-break-inside: avoid;
    line-height: 1.6;
}

/* Inline math */
.math-inline {
    font-family: "Menlo", "Courier New", Courier, monospace;
    font-size: 9.5pt;
    color: #003366;
}

/* Links */
a {
    color: #003366;
    text-decoration: none;
}
"""


# ---------------------------------------------------------------------------
# LaTeX → plain-text conversion (applied to raw markdown BEFORE parsing)
# ---------------------------------------------------------------------------

def _latex_to_plain(tex: str) -> str:
    """Convert a LaTeX expression to readable plain text."""
    s = tex.strip()

    # 1. Strip \text{} FIRST — removes nested braces so \frac regex can match
    for _ in range(5):
        prev = s
        s = re.sub(r'\\text\{([^{}]*)\}', r'\1', s)
        if s == prev:
            break

    # 2. \underbrace{expr}_{label} → expr (before \frac, since underbraces may nest)
    for _ in range(5):
        prev = s
        s = re.sub(r'\\underbrace\{([^{}]*)\}_\{[^{}]*\}', r'\1', s)
        if s == prev:
            break

    # 3. \frac{A}{B} → A / B  (now safe — inner \text{} already stripped)
    for _ in range(5):
        prev = s
        s = re.sub(
            r'\\frac\{([^{}]*)\}\{([^{}]*)\}',
            r'(\1) / (\2)',
            s,
        )
        if s == prev:
            break

    # 4. Simple command substitutions
    replacements = {
        r'\times': '×',
        r'\Delta': 'Δ',
        r'\varepsilon': 'ε',
        r'\cdot': '·',
        r'\leq': '≤',
        r'\geq': '≥',
        r'\approx': '≈',
        r'\infty': '∞',
        r'\alpha': 'α',
        r'\beta': 'β',
        r'\gamma': 'γ',
        r'\sigma': 'σ',
        r'\pi': 'π',
        r'\rho': 'ρ',
        r'\lambda': 'λ',
        r'\delta': 'δ',
        r'\sum': 'Σ',
    }
    for cmd, repl in replacements.items():
        s = s.replace(cmd, repl)

    # 5. Subscripts: _{XY} → _XY  and  _X → _X (already fine)
    s = re.sub(r'_\{([^{}]*)\}', r'_\1', s)

    # 6. Superscripts: ^{XY} → ^XY
    s = re.sub(r'\^\{([^{}]*)\}', r'^\1', s)

    # 7. Remove remaining braces and backslashes
    s = s.replace('{', '').replace('}', '')
    s = s.replace('\\', '')

    return s.strip()


def preprocess_latex(md_text: str) -> str:
    """
    Convert all LaTeX in the raw markdown to plain text BEFORE markdown parsing.
    Handles both block ($$...$$) and inline ($...$) math.
    """
    # Block math: $$...$$ → <div class="math-block">...</div>
    # (We inject raw HTML that markdown will pass through)
    def replace_block_math(match):
        plain = _latex_to_plain(match.group(1))
        return f'\n<div class="math-block">{plain}</div>\n'

    result = re.sub(r'\$\$(.*?)\$\$', replace_block_math, md_text, flags=re.DOTALL)

    # Inline math: $...$ → <span class="math-inline">...</span>
    # Be careful not to match dollar amounts like "$1,500M"
    def replace_inline_math(match):
        content = match.group(1)
        # Skip if it looks like a dollar amount (starts with digit)
        if re.match(r'^\d', content):
            return match.group(0)
        plain = _latex_to_plain(content)
        return f'<span class="math-inline">{plain}</span>'

    result = re.sub(r'(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)', replace_inline_math, result)

    return result


def fix_markdown_structure(md_text: str) -> str:
    """
    Fix structural markdown issues that cause parsing failures:
    - Ensure blank line before list items following a paragraph
    - Ensure blank line before table headers following a paragraph
    """
    lines = md_text.split('\n')
    fixed = []

    for i, line in enumerate(lines):
        # If this line starts a list item or table, ensure previous line is blank
        if i > 0 and fixed:
            prev = fixed[-1].strip()
            curr = line.strip()

            # List item after paragraph text (not after another list item or blank)
            if curr.startswith('- ') and prev and not prev.startswith('- ') and not prev.startswith('|'):
                fixed.append('')

            # Table header after paragraph text
            if curr.startswith('| ') and prev and not prev.startswith('|') and not prev == '':
                fixed.append('')

        fixed.append(line)

    return '\n'.join(fixed)


def main():
    # Read markdown
    md_text = INPUT_MD.read_text(encoding='utf-8')

    # Step 1: Convert all LaTeX to plain text / HTML spans BEFORE markdown processing
    md_text = preprocess_latex(md_text)

    # Step 2: Fix structural issues (blank lines before lists/tables)
    md_text = fix_markdown_structure(md_text)

    # Step 3: Convert markdown → HTML
    extensions = ['tables', 'fenced_code', 'toc', 'sane_lists']
    html_body = markdown.markdown(md_text, extensions=extensions)

    # Wrap in full HTML document
    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <style>{CSS}</style>
</head>
<body>
{html_body}
</body>
</html>
"""

    # Generate PDF
    OUTPUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html_doc).write_pdf(str(OUTPUT_PDF))
    print(f"PDF generated: {OUTPUT_PDF}")
    print(f"Size: {OUTPUT_PDF.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
