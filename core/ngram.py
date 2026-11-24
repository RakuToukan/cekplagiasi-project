"""FR-6: n-gram kata, digeser satu kata setiap langkah."""
from typing import List


def buat_ngram(tokens: List[dict], n: int) -> List[dict]:
    """Setiap n-gram: {"gram": str, "orig_idx": [indeks kata asli penyusunnya]}.

    Sama seperti notebook: jika jumlah token < n, seluruh token menjadi satu n-gram.
    """
    if not tokens:
        return []
    if len(tokens) < n:
        potongan = [tokens]
    else:
        potongan = [tokens[i : i + n] for i in range(len(tokens) - n + 1)]
    return [
        {"gram": " ".join(t["tok"] for t in p), "orig_idx": [t["orig_idx"] for t in p]}
        for p in potongan
    ]
