from pathlib import Path
import subprocess
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


def render_pdf(template_name: str, context: dict, output_pdf: Path) -> Path:
    template = env.get_template(template_name)
    tex_source = template.render(**context)

    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
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

        return tmpdir / "document.pdf"

