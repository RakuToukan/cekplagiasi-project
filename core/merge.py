"""FR-3 dan FR-4: menggabungkan n dokumen menjadi satu korpus, satu dokumen per baris.

Format setiap baris korpus: <nama_file>\t<teks satu baris>\n
"""
import re
from typing import List, Tuple

from .extract import ekstrak_teks

Dokumen = Tuple[str, str]  # (nama, teks)


def ratakan(teks: str) -> str:
    """Ganti semua enter, tab, dan spasi ganda menjadi satu spasi."""
    return re.sub(r"\s+", " ", teks).strip()


def rapikan(teks: str) -> str:
    """Rapikan spasi tetapi pertahankan batas paragraf (baris kosong) untuk tampilan.

    Hasil preprocessing teks ini sama dengan hasil `ratakan`, karena tokenisasi
    tidak bergantung pada jenis spasi.
    """
    teks = teks.replace("\r\n", "\n").replace("\r", "\n")
    paragraf = (ratakan(p) for p in re.split(r"\n\s*\n", teks))
    return "\n\n".join(p for p in paragraf if p)


def _nama_unik(nama: str, terpakai: set) -> str:
    nama = ratakan(nama) or "tanpa_nama"
    if nama not in terpakai:
        return nama
    k = 2
    while f"{nama} ({k})" in terpakai:
        k += 1
    return f"{nama} ({k})"


def bangun_korpus(
    files: List[Tuple[str, bytes]], satu_baris: bool = True
) -> Tuple[List[Dokumen], List[str]]:
    """Ekstrak setiap file. Mengembalikan (dokumen valid, log file yang dilewati).

    satu_baris=True : teks diratakan menjadi satu baris (format korpus).
    satu_baris=False: batas paragraf dipertahankan untuk pratinjau dokumen.
    """
    dokumen: List[Dokumen] = []
    log: List[str] = []
    terpakai: set = set()
    olah = ratakan if satu_baris else rapikan
    for nama, data in sorted(files, key=lambda f: f[0].lower()):
        try:
            teks = olah(ekstrak_teks(nama, data))
        except Exception as e:  # file rusak, terenkripsi, format salah
            log.append(f"{nama}: gagal dibaca ({e})")
            continue
        if not teks:
            log.append(f"{nama}: teks kosong (PDF hasil scan atau file kosong)")
            continue
        nama_final = _nama_unik(nama, terpakai)
        terpakai.add(nama_final)
        dokumen.append((nama_final, teks))
    return dokumen, log


def korpus_ke_teks(dokumen: List[Dokumen]) -> str:
    return "".join(f"{nama}\t{ratakan(teks)}\n" for nama, teks in dokumen)


def baca_korpus(isi: str) -> Tuple[List[Dokumen], List[str]]:
    dokumen: List[Dokumen] = []
    log: List[str] = []
    terpakai: set = set()
    for no, baris in enumerate(isi.splitlines(), 1):
        if not baris.strip():
            continue
        if "\t" not in baris:
            log.append(f"baris {no}: tidak ada pemisah tab, dilewati")
            continue
        nama, teks = baris.split("\t", 1)
        teks = ratakan(teks)
        if not teks:
            log.append(f"baris {no} ({nama}): teks kosong, dilewati")
            continue
        nama_final = _nama_unik(nama, terpakai)
        terpakai.add(nama_final)
        dokumen.append((nama_final, teks))
    return dokumen, log
