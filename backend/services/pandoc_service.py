import subprocess
from pathlib import Path

class PandocServiceError(Exception):
    pass


def docx_to_markdown(docx_path: str) -> str:
    path = Path(docx_path)

    if not path.exists():
        raise PandocServiceError(f"File not found: {docx_path}")

    if path.suffix.lower() != ".docx":
        raise PandocServiceError("Only .docx files are supported")

    try:
        result = subprocess.run(
            ["pandoc", str(path), "-t", "markdown"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout

    except subprocess.CalledProcessError as e:
        raise PandocServiceError(e.stderr.strip())
