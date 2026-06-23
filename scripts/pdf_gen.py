from pathlib import Path
import mimetypes
import subprocess
import shutil
import tempfile

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from pylatexenc.latexencode import unicode_to_latex


TEMPLATE_DIR = Path("templates/latex/")

def latex_escape(value: object) -> str:
    """Escape user/content data for safe LaTeX text insertion."""
    return unicode_to_latex(str(value))


env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    block_start_string="((%",
    block_end_string="%))",
    variable_start_string="((*",
    variable_end_string="*))",
    comment_start_string="((#",
    comment_end_string="#))",
    undefined=StrictUndefined,
    autoescape=False,
)

env.filters["latex_escape"] = latex_escape

def send_pdf(
    mailer,
    to_addr: str,
    pdf_path: str | Path,
    subject: str = "Your PDF",
    text_body: str = "Please find the PDF attached.",
    html_body: str | None = None,
):
    pdf_path = Path(pdf_path)

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a .pdf file, got: {pdf_path}")

    mailer.send(
        to_addr=to_addr,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
        attachments=[pdf_path],
    )


def render_pdf(
    template_name: str, 
    context: dict, 
    filename: str,
    mailer,
    to_addr: str,
    subject: str = "Your PDF",
    text_body: str = "Please find the PDF attached.",
    html_body: str | None = None,
) -> Path:
    template = env.get_template(template_name)
    tex_source = template.render(**context)

    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)

        # Copy local LaTeX dependencies next to document.tex
        for pattern in ["*.sty", "*.cls", "*.tex", "*.jpg", "*.jpeg", "*.png", "*.pdf"]:
            for path in TEMPLATE_DIR.glob(pattern):
                # Do not copy the main template over our rendered document
                if path.name != template_name:
                    shutil.copy2(path, tmpdir / path.name)

        tex_file = tmpdir / "document.tex"
        tex_file.write_text(tex_source, encoding="utf-8")

        cmd = [
            "latexmk",
            "-pdf",
            "-pdflatex=pdflatex -interaction=nonstopmode -halt-on-error %O %S",
            "-outdir=" + str(tmpdir),
            str(tex_file),
        ]

        result = subprocess.run(
            cmd,
            cwd=tmpdir,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=60,
        )

        if result.returncode != 0:
            log_file = tmpdir / "document.log"
            log = log_file.read_text(errors="replace") if log_file.exists() else result.stdout
            raise RuntimeError(f"LaTeX failed:\n{log[-4000:]}")

        generated_pdf = tmpdir / "document.pdf"

        if not generated_pdf.exists():
            raise FileNotFoundError(
                f"Expected PDF was not generated: {generated_pdf}\n"
                f"LaTeX output:\n{result.stdout[-4000:]}"
            )

        # Rename/copy PDF inside temp dir so the mail attachment has a nice filename
        attachment_pdf = tmpdir / filename
        shutil.copy2(generated_pdf, attachment_pdf)

        send_pdf(
            mailer=mailer, 
            to_addr=to_addr,
            pdf_path=attachment_pdf, 
            subject=subject, 
            text_body=text_body,
            html_body=html_body
        )
