from core.rolling_hash import buat_fingerprint, hitung_rolling_hash


def hash_notebook(teks, b=3, mod=10**9):
    """Salinan hitung_rolling_hash dari notebook."""
    h = 0
    for i, ch in enumerate(teks):
        h = (h + ord(ch) * (b ** (len(teks) - 1 - i))) % mod
    return h


def test_sama_dengan_notebook():
    for teks in ["plagiarisme jiplak", "uu nomor", "a", "knuthmorrispratt smithwaterman"]:
        for b, mod in [(3, 10**9), (3, 109), (31, 1_000_000_007)]:
            assert hitung_rolling_hash(teks, b, mod) == hash_notebook(teks, b, mod)


def test_nilai_hash_dari_output_notebook():
    assert hitung_rolling_hash("plagiarisme jiplak") == 245844071
    assert hitung_rolling_hash("uu nomor") == 362283


def test_fingerprint_hitung_frekuensi():
    ngrams = [{"gram": g, "orig_idx": [0]} for g in ["a b", "b c", "a b"]]
    fp = buat_fingerprint(ngrams)
    h = hitung_rolling_hash("a b")
    assert fp["fingerprint"][h] == 2
    assert fp["hash_index"][h] == [0, 2]
