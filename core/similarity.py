"""FR-9: Jaccard Coefficient (dalam persen).

J(A, B) = |A ∩ B| / |A ∪ B|, dengan A dan B himpunan fingerprint unik kedua dokumen.
"""


def jaccard(n_sama: int, n_a: int, n_b: int) -> float:
    gabungan = n_a + n_b - n_sama
    return 100 * n_sama / gabungan if gabungan else 0.0
