"""Menyusun bagian cocok (segmen) sebuah dokumen terhadap dokumen lain di dataset.

1. Untuk setiap dokumen lain Y, cari deretan n-gram berurutan yang cocok di X dan Y
   (diagonal). Kecocokan dicari lewat hash Rabin-Karp lalu diverifikasi string-nya.
2. Setiap deretan dipetakan ke rentang kata asli di X dan di Y.
3. Rentang di X yang tumpang tindih atau bersebelahan digabung menjadi satu segmen.
   Sumber utama segmen = deretan terpanjang di dalamnya.
"""
from typing import List


def deret_cocok(fp_x: dict, fp_y: dict) -> List[tuple]:
    """Deretan n-gram berurutan yang cocok: (i_awal, i_akhir, j_awal, j_akhir)."""
    panjang = {}
    for i, ng in enumerate(fp_x["ngrams"]):
        for j in fp_y["hash_index"].get(ng["hash"], ()):
            if fp_y["ngrams"][j]["gram"] != ng["gram"]:
                continue  # spurious hit: hash sama, string beda
            panjang[(i, j)] = panjang.get((i - 1, j - 1), 0) + 1
    return [
        (i - n + 1, i, j - n + 1, j)
        for (i, j), n in panjang.items()
        if (i + 1, j + 1) not in panjang
    ]


def _rentang_kata(fp: dict, awal: int, akhir: int) -> tuple:
    return min(fp["ngrams"][awal]["orig_idx"]), max(fp["ngrams"][akhir]["orig_idx"])


def _potong(teks: str, words: list, lo: int, hi: int) -> str:
    return teks[words[lo]["start"] : words[hi]["end"]]


def susun_segmen(ix: int, nama: list, teks: list, pres: list, fps: list) -> List[dict]:
    words_x = pres[ix]["words"]
    kandidat = []
    for iy in range(len(fps)):
        if iy == ix:
            continue
        for i0, i1, j0, j1 in deret_cocok(fps[ix], fps[iy]):
            x_lo, x_hi = _rentang_kata(fps[ix], i0, i1)
            y_lo, y_hi = _rentang_kata(fps[iy], j0, j1)
            kandidat.append(
                {"x_lo": x_lo, "x_hi": x_hi, "y": iy, "y_lo": y_lo, "y_hi": y_hi, "kata": x_hi - x_lo + 1}
            )

    kandidat.sort(key=lambda k: (k["x_lo"], -k["kata"]))
    gabung = []
    for k in kandidat:
        if gabung and k["x_lo"] <= gabung[-1]["hi"] + 1:
            gabung[-1]["hi"] = max(gabung[-1]["hi"], k["x_hi"])
            gabung[-1]["kandidat"].append(k)
        else:
            gabung.append({"lo": k["x_lo"], "hi": k["x_hi"], "kandidat": [k]})

    segmen = []
    for no, g in enumerate(gabung, 1):
        utama = max(g["kandidat"], key=lambda k: k["kata"])
        words_y = pres[utama["y"]]["words"]
        segmen.append(
            {
                "no": no,
                "lo": g["lo"],
                "hi": g["hi"],
                "kata": g["hi"] - g["lo"] + 1,
                "sumber": nama[utama["y"]],
                "sumber_lain": sorted({nama[k["y"]] for k in g["kandidat"]} - {nama[utama["y"]]}),
                # nomor dokumen sumber (urutan di dataset, mulai 1), sumber utama di depan
                "nomor_dok": [utama["y"] + 1] + sorted({k["y"] + 1 for k in g["kandidat"]} - {utama["y"] + 1}),
                "teks_x": _potong(teks[ix], words_x, g["lo"], g["hi"]),
                "teks_sumber": _potong(teks[utama["y"]], words_y, utama["y_lo"], utama["y_hi"]),
                "kandidat": g["kandidat"],
            }
        )
    return segmen


def sumber_teratas(segmen: List[dict]) -> List[dict]:
    """Semua dokumen sumber yang cocok dengan dokumen ini, beserta jumlah kata yang cocok.

    Satu bagian bisa cocok dengan beberapa sumber sekaligus, jadi setiap sumber dihitung penuh.
    """
    per_sumber = {}
    for s in segmen:
        for k in s["kandidat"]:
            per_sumber.setdefault(k["y"], set()).update(range(k["x_lo"], k["x_hi"] + 1))
    hasil = [{"y": y, "nomor": y + 1, "kata": len(kata)} for y, kata in per_sumber.items()]
    return sorted(hasil, key=lambda a: (-a["kata"], a["y"]))
