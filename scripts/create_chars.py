from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import re
import unicodedata

INPUT_HTML = "input.html"
OUTPUT_DIR = Path("table_pdfs")
OUTPUT_DIR.mkdir(exist_ok=True)


def create_username(name, surname, max_length=30, separator="_"):
    name = name.lower().strip()
    surname = surname.lower().strip()

    name = unicodedata.normalize("NFKD", name).encode("ASCII", "ignore").decode("utf-8")
    surname = unicodedata.normalize("NFKD", surname).encode("ASCII", "ignore").decode("utf-8")

    name = re.sub(r"[^a-z0-9_]", "", name)
    surname = re.sub(r"[^a-z0-9_]", "", surname)

    name = name.strip("_")
    surname = surname.strip("_")

    if separator == "_":
        username = f"{name}_{surname}"
    elif separator == "-":
        username = f"{name}-{surname}"
    else:
        username = f"{name}{surname}"

    username = re.sub(r"[_\-]+", separator, username)

    if len(username) > max_length:
        username = username[:max_length]
        username = username.rstrip("_-")

    if not username:
        username = "user"

    return username


def get_cell_text_without_hint(cell):
    clone = BeautifulSoup(str(cell), "html.parser")

    for hint in clone.select(".table-hint"):
        hint.decompose()

    return clone.get_text("\n", strip=True)


def markdownish_paragraphs(text):
    """
    Single line break: treated like a space.
    Empty line: treated like a paragraph break.
    """
    text = text.strip()

    paragraphs = re.split(r"\n\s*\n+", text)

    cleaned = []
    for paragraph in paragraphs:
        paragraph = re.sub(r"[ \t]*\n[ \t]*", " ", paragraph)
        paragraph = re.sub(r" {2,}", " ", paragraph)
        paragraph = paragraph.strip()

        if paragraph:
            cleaned.append(paragraph)

    return cleaned


def normalize_large_text_cells(soup, table):
    """
    Handles cells like Hintergrund / Notizen.

    Removes inline white-space: pre-line behavior and converts the text into
    paragraph blocks, so single line breaks do not create hard visual breaks.
    """
    for cell in table.find_all("td"):
        style = cell.get("style", "")

        if "white-space" not in style:
            continue

        hint = cell.select_one(".table-hint")
        hint_text = hint.get_text(" ", strip=True) if hint else None

        text = get_cell_text_without_hint(cell)
        paragraphs = markdownish_paragraphs(text)

        cell.clear()

        for paragraph in paragraphs:
            p = soup.new_tag("p")
            p.string = paragraph
            cell.append(p)

        if hint_text:
            hint_span = soup.new_tag("span")
            hint_span["class"] = "table-hint"
            hint_span.string = hint_text
            cell.append(hint_span)

        # Remove inline white-space: pre-line
        del cell["style"]


def filename_from_table(table, index):
    first_row = table.find("tr")
    if not first_row:
        return f"table_{index:03d}"

    cells = first_row.find_all("td")

    if len(cells) < 2:
        return f"table_{index:03d}"

    surname = get_cell_text_without_hint(cells[0])
    name = get_cell_text_without_hint(cells[1])

    return create_username(name=name, surname=surname)


html = Path(INPUT_HTML).read_text(encoding="utf-8")
soup = BeautifulSoup(html, "html.parser")

tables = soup.find_all("table")

used_filenames = {}

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()

    for i, original_table in enumerate(tables, start=1):
        # Work on a copy, so the original parsed document remains untouched
        table_soup = BeautifulSoup(str(original_table), "html.parser")
        table = table_soup.find("table")

        normalize_large_text_cells(table_soup, table)

        base_filename = filename_from_table(table, i)

        # Avoid overwriting files if two people produce the same username
        count = used_filenames.get(base_filename, 0) + 1
        used_filenames[base_filename] = count

        if count == 1:
            output_filename = f"{base_filename}.pdf"
        else:
            output_filename = f"{base_filename}_{count}.pdf"

        table_html = f"""
        <!doctype html>
        <html>
        <head>
          <meta charset="utf-8">
          <style>
            body {{
              font-family: Arial, sans-serif;
              font-size: 11px;
              margin: 20px;
            }}

            table {{
              width: 100%;
              border-collapse: collapse;
              text-align: left;
            }}

            td, th {{
              border: 1px solid #666;
              padding: 6px;
              vertical-align: top;
            }}

            tr {{
              break-inside: avoid;
              page-break-inside: avoid;
            }}

            p {{
              margin: 0 0 0.8em 0;
            }}

            p:last-child {{
              margin-bottom: 0;
            }}

            .table-hint {{
              display: block;
              margin-top: 4px;
              font-size: 8px;
              color: #666;
              text-transform: uppercase;
            }}

            td[style*="white-space"] {{
              white-space: normal !important;
            }}
          </style>
        </head>
        <body>
          {str(table)}
        </body>
        </html>
        """

        page.set_content(table_html, wait_until="networkidle")
        page.pdf(
            path=str(OUTPUT_DIR / output_filename),
            format="A4",
            print_background=True,
            margin={
                "top": "15mm",
                "right": "12mm",
                "bottom": "15mm",
                "left": "12mm",
            },
        )

    browser.close()
