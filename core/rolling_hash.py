"""FR-7: Rolling Hash dan fingerprint dokumen.

H = (c1*b^(k-1) + c2*b^(k-2) + ... + ck) mod q

Dihitung dengan metode Horner (h = h*b + c), hasilnya sama persis dengan
`hitung_rolling_hash` di notebook, tetapi tanpa menghitung pangkat b dari awal
untuk setiap karakter.
"""
from collections import Counter
from typing import Dict, List

MOD_NOTEBOOK = 10**9


def hitung_rolling_hash(teks: str, b: int = 3, mod: int = MOD_NOTEBOOK) -> int:
    h = 0
    for ch in teks:
        h = (h * b + ord(ch)) % mod
    return h


def rincian_hash(teks: str, b: int = 3, mod: int = MOD_NOTEBOOK) -> List[dict]:
    """Langkah perhitungan per karakter, untuk tampilan demo."""
    k = len(teks)
    baris = []
    h = 0
    for i, ch in enumerate(teks):
        h = (h * b + ord(ch)) % mod
        baris.append(
            {
                "karakter": ch,
                "ASCII": ord(ch),
                "pangkat": k - 1 - i,
                "ASCII x b^pangkat": ord(ch) * b ** (k - 1 - i),
                "hash berjalan": h,
            }
        )
    return baris


def buat_fingerprint(ngrams: List[dict], b: int = 3, mod: int = MOD_NOTEBOOK) -> dict:
    """ngrams     : n-gram dengan tambahan key "hash"
    fingerprint: Counter {hash: frekuensi}
    hash_index : {hash: [posisi di ngrams]}
    """
    hasil = []
    hash_index: Dict[int, List[int]] = {}
    for pos, ng in enumerate(ngrams):
        h = hitung_rolling_hash(ng["gram"], b, mod)
        hasil.append({**ng, "hash": h})
        hash_index.setdefault(h, []).append(pos)
    return {
        "ngrams": hasil,
        "fingerprint": Counter({h: len(p) for h, p in hash_index.items()}),
        "hash_index": hash_index,
    }
