"""FR-10: perbandingan all-vs-all. Setiap dokumen bergantian menjadi X.

Jaccard simetris, jadi setiap pasangan i < j cukup dihitung sekali
(n(n-1)/2 pasangan).
"""
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from .rabin_karp import cocokkan
from .similarity import jaccard


def bandingkan_pasangan(fp_a: dict, fp_b: dict) -> dict:
    hasil = cocokkan(fp_a, fp_b)
    n_a = len(fp_a["fingerprint"])
    n_b = len(fp_b["fingerprint"])
    n_sama = len(hasil["hash_valid"])
    hasil.update(
        n_a=n_a,
        n_b=n_b,
        sama=n_sama,
        gabungan=n_a + n_b - n_sama,
        jaccard=jaccard(n_sama, n_a, n_b),
    )
    return hasil


def bandingkan_semua(fps: List[dict]) -> Dict[Tuple[int, int], dict]:
    n = len(fps)
    return {(i, j): bandingkan_pasangan(fps[i], fps[j]) for i in range(n) for j in range(i + 1, n)}


def ambil_pasangan(hasil: Dict[Tuple[int, int], dict], x: int, y: int) -> dict:
    """Hasil dari sudut pandang X: idx_x milik X, idx_y milik Y."""
    if x < y:
        r = hasil[(x, y)]
        return {**r, "idx_x": r["idx_a"], "idx_y": r["idx_b"], "n_x": r["n_a"], "n_y": r["n_b"]}
    r = hasil[(y, x)]
    return {**r, "idx_x": r["idx_b"], "idx_y": r["idx_a"], "n_x": r["n_b"], "n_y": r["n_a"]}


def tabel_pasangan(nama: List[str], hasil: dict, n: int, b: int, mod: int) -> pd.DataFrame:
    """Satu baris per (X, pembanding), kedua arah ditulis."""
    baris = []
    for (i, j), r in hasil.items():
        for x, y in ((i, j), (j, i)):
            baris.append(
                {
                    "x": nama[x],
                    "pembanding": nama[y],
                    "n": n,
                    "b": b,
                    "mod": mod,
                    "sama": r["sama"],
                    "gabungan": r["gabungan"],
                    "jaccard": round(r["jaccard"], 2),
                    "spurious_hit": r["spurious"],
                }
            )
    return pd.DataFrame(baris)


def matriks(nama: List[str], hasil: dict) -> pd.DataFrame:
    m = np.full((len(nama), len(nama)), np.nan)
    for (i, j), r in hasil.items():
        m[i, j] = m[j, i] = round(r["jaccard"], 2)
    return pd.DataFrame(m, index=nama, columns=nama)
