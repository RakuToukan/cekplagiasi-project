"""FR-8: pencocokan Rabin-Karp antar fingerprint.

Hash yang sama di kedua dokumen diverifikasi ulang dengan membandingkan string
n-gram. Hash sama tetapi string berbeda (collision) dihitung sebagai spurious hit
dan tidak dianggap cocok.
"""


def cocokkan(fp_a: dict, fp_b: dict) -> dict:
    hash_valid = set()
    gram_sama = set()
    idx_a, idx_b = [], []
    spurious = 0
    for h in fp_a["hash_index"].keys() & fp_b["hash_index"].keys():
        posisi_a = fp_a["hash_index"][h]
        posisi_b = fp_b["hash_index"][h]
        gram_a = {fp_a["ngrams"][i]["gram"] for i in posisi_a}
        gram_b = {fp_b["ngrams"][i]["gram"] for i in posisi_b}
        cocok = gram_a & gram_b
        if not cocok:
            spurious += 1
            continue
        hash_valid.add(h)
        gram_sama |= cocok
        idx_a.extend(i for i in posisi_a if fp_a["ngrams"][i]["gram"] in cocok)
        idx_b.extend(i for i in posisi_b if fp_b["ngrams"][i]["gram"] in cocok)
    return {
        "hash_valid": hash_valid,
        "gram_sama": sorted(gram_sama),
        "idx_a": sorted(idx_a),
        "idx_b": sorted(idx_b),
        "spurious": spurious,
    }
