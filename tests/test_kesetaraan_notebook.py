"""Bandingkan algoritma aplikasi dengan kode asli di notebook rabin_karp_simialirity (1).ipynb.

Fungsi notebook (kelas preprosesingteks, hitung_rolling_hash, rabin_karp_search) diambil
langsung dari file .ipynb lalu dijalankan berdampingan dengan modul core/ pada:
- dokumen di sample_docs/ dan sample_docs_plagiat/
- pasangan dokumen yang ada (termasuk yang dikomentari) di sel notebook
untuk n = 1, 2, 3.
"""
import ast
import contextlib
import io
import itertools
import json
import re
from pathlib import Path

import pytest

from core.compare import bandingkan_pasangan
from core.merge import rapikan
from core.ngram import buat_ngram
from core.rolling_hash import buat_fingerprint, hitung_rolling_hash
from core.similarity import jaccard

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOK = ROOT / "rabin_karp_simialirity (1).ipynb"

pytestmark = pytest.mark.skipif(not NOTEBOOK.exists(), reason="file notebook tidak ada")


def _potong(src: str, awal: str, akhir: str = None) -> str:
    i = src.index(awal)
    j = src.index(akhir, i) if akhir else len(src)
    return src[i:j]


@pytest.fixture(scope="module")
def nb():
    """Namespace berisi fungsi asli dari notebook."""
    sel = ["".join(c["source"]) for c in json.loads(NOTEBOOK.read_text(encoding="utf-8"))["cells"]]
    kode = "\n".join(
        [
            sel[12],
            _potong(sel[13], "class preprosesingteks", 'if __name__ == "__main__":'),
            _potong(sel[14], "def hitung_rolling_hash", "token_dok1 ="),
            "import math\n" + _potong(sel[17], "def rabin_karp_search", "def rabin_karp_cosine"),
        ]
    )
    ns: dict = {}
    exec(kode, ns)
    ns["pre"] = ns["preprosesingteks"]()
    # semua pasangan dokumen di sel 13, termasuk yang dikomentari
    pasangan = re.findall(r'^\s*#?\s*(dokumen_[12])\s*=\s*(".*")\s*$', sel[13], flags=re.M)
    ns["teks_notebook"] = [ast.literal_eval(v) for _, v in pasangan]
    return ns


def _korpus(nb) -> dict:
    grup = {"notebook": nb["teks_notebook"]}
    for folder in ("sample_docs", "sample_docs_plagiat"):
        grup[folder] = [p.read_text(encoding="utf-8") for p in sorted((ROOT / folder).glob("*.txt"))]
    return grup


def test_token_sama(nb, pre):
    for grup, daftar in _korpus(nb).items():
        for teks in daftar:
            harapan = nb["pre"].proses(teks, ukuran_ngram=2)["token_diproses"]
            assert [t["tok"] for t in pre.proses(teks)["tokens"]] == harapan, grup
            # aplikasi memproses teks dengan batas paragraf dipertahankan; token harus tetap sama
            assert [t["tok"] for t in pre.proses(rapikan(teks))["tokens"]] == harapan, grup


@pytest.mark.parametrize("n", [1, 2, 3])
def test_ngram_dan_hash_sama(nb, pre, n):
    for daftar in _korpus(nb).values():
        for teks in daftar:
            token = nb["pre"].proses(teks, ukuran_ngram=n)["token_diproses"]
            gram_nb = nb["pre"].buat_ngram(token, n=n)
            gram_app = [g["gram"] for g in buat_ngram(pre.proses(teks)["tokens"], n)]
            assert gram_app == gram_nb
            assert [hitung_rolling_hash(g) for g in gram_app] == [nb["hitung_rolling_hash"](g) for g in gram_nb]


@pytest.mark.parametrize("n", [1, 2, 3])
def test_jaccard_sama(nb, pre, n):
    for daftar in _korpus(nb).values():
        hasil_pre = [pre.proses(t) for t in daftar]
        gram_nb = [nb["pre"].buat_ngram(nb["pre"].proses(t)["token_diproses"], n=n) for t in daftar]
        fps = [buat_fingerprint(buat_ngram(p["tokens"], n)) for p in hasil_pre]
        for i, j in itertools.combinations(range(len(daftar)), 2):
            with contextlib.redirect_stdout(io.StringIO()):
                j_nb = nb["rabin_karp_search"](gram_nb[i], gram_nb[j])
            r = bandingkan_pasangan(fps[i], fps[j])
            # Notebook menghitung irisan hash tanpa cek string, jadi collision (spurious hit) ikut
            # dihitung cocok. Aplikasi memverifikasi string. Selisihnya harus persis sebesar collision.
            assert jaccard(r["sama"] + r["spurious"], r["n_a"], r["n_b"]) == pytest.approx(j_nb, abs=1e-9)
            if n >= 2:
                assert r["spurious"] == 0
                assert r["jaccard"] == pytest.approx(j_nb, abs=1e-9)
