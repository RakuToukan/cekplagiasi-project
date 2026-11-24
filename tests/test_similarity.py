import pytest

from core.compare import bandingkan_pasangan, bandingkan_semua, matriks
from core.ngram import buat_ngram
from core.rolling_hash import buat_fingerprint
from core.similarity import jaccard


def fp_dari(pre, teks, n=2, b=3, mod=10**9):
    return buat_fingerprint(buat_ngram(pre.proses(teks)["tokens"], n), b, mod)


def test_rumus_jaccard():
    assert jaccard(72, 294, 242) == pytest.approx(100 * 72 / 464)
    assert jaccard(0, 0, 0) == 0


def test_hasil_sama_dengan_notebook(pre, contoh):
    """Notebook: 294 dan 242 n-gram, irisan 72, Jaccard 15.52%."""
    r = bandingkan_pasangan(fp_dari(pre, contoh[0]), fp_dari(pre, contoh[1]))
    assert (r["n_a"], r["n_b"], r["sama"], r["gabungan"]) == (294, 242, 72, 464)
    assert round(r["jaccard"], 2) == 15.52


def test_dokumen_identik_100(pre):
    teks = "Algoritma Rabin-Karp menggunakan fungsi hash untuk mencocokkan string pada dokumen."
    r = bandingkan_pasangan(fp_dari(pre, teks), fp_dari(pre, teks))
    assert r["jaccard"] == pytest.approx(100)


def test_dokumen_berbeda_0(pre):
    r = bandingkan_pasangan(
        fp_dari(pre, "Kucing hitam tidur di atas kasur empuk."),
        fp_dari(pre, "Pemerintah membangun jembatan baru di provinsi timur."),
    )
    assert r["jaccard"] == 0


def test_collision_tidak_dihitung(pre):
    """Dengan q=2 hampir semua hash bertabrakan; verifikasi string harus menyaringnya."""
    fa = fp_dari(pre, "kucing hitam tidur kasur", mod=2)
    fb = fp_dari(pre, "jembatan baru provinsi timur", mod=2)
    r = bandingkan_pasangan(fa, fb)
    assert r["sama"] == 0
    assert r["spurious"] > 0


def test_matriks_simetris_diagonal_kosong(pre, contoh):
    fps = [fp_dari(pre, t) for t in (contoh[0], contoh[1], contoh[0][:800])]
    m = matriks(["a", "b", "c"], bandingkan_semua(fps))
    assert m.isna().values.diagonal().all()
    assert (m.fillna(0).values == m.fillna(0).values.T).all()
