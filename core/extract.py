"""FR-2: ekstraksi teks dari file .txt, .pdf, dan .docx."""
import io
import os

from docx import Document
from pypdf import PdfReader

FORMAT_DIDUKUNG = (".txt", ".pdf", ".docx")


def ekstrak_teks(nama_file: str, data: bytes) -> str:
    ext = os.path.splitext(nama_file)[1].lower()
    if ext == ".txt":
        try:
            return data.decode("utf-8-sig")
        except UnicodeDecodeError:
            return data.decode("latin-1")
    if ext == ".pdf":
        reader = PdfReader(io.BytesIO(data))
        return "\n".join((halaman.extract_text() or "") for halaman in reader.pages)
    if ext == ".docx":
        dokumen = Document(io.BytesIO(data))
        return "\n\n".join(p.text for p in dokumen.paragraphs)
    raise ValueError(f"format {ext or '(tanpa ekstensi)'} tidak didukung")
