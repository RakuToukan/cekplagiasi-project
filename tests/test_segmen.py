from core.ngram import buat_ngram
from core.rolling_hash import buat_fingerprint
from core.segmen import sumber_teratas, susun_segmen


def siapkan(pre, teks, mod=10**9):
    pres = [pre.proses(t) for t in teks]
    fps = [buat_fingerprint(buat_ngram(p["tokens"], 2), 3, mod) for p in pres]
    nama = [f"d{i}" for i in range(len(teks))]
    return nama, pres, fps


def test_segmen_dan_sumber_utama(pre):
    teks = [
        "Pendahuluan singkat. Algoritma Rabin-Karp memakai fungsi hash. Lalu sistem Mengembangkan Aplikasi baru.",
        "Algoritma Rabin-Karp memakai fungsi hash.",
        "Tim kami dikembangkan aplikasi untuk sekolah.",
    ]
    nama, pres, fps = siapkan(pre, teks)
    seg = susun_segmen(0, nama, teks, pres, fps)
    assert [s["teks_x"] for s in seg] == ["Algoritma Rabin-Karp memakai fungsi hash.", "Mengembangkan Aplikasi"]
    assert seg[0]["sumber"] == "d1"
    assert seg[1]["sumber"] == "d2"
    assert seg[1]["teks_sumber"] == "dikembangkan aplikasi"


def test_nomor_dokumen_sumber(pre):
    teks = [
        "Pendahuluan singkat. Algoritma Rabin-Karp memakai fungsi hash. Lalu sistem Mengembangkan Aplikasi baru.",
        "Algoritma Rabin-Karp memakai fungsi hash.",
        "Tim kami dikembangkan aplikasi untuk sekolah.",
        "Sungguh algoritma Rabin-Karp memakai fungsi hash.",
    ]
    nama, pres, fps = siapkan(pre, teks)
    seg = susun_segmen(0, nama, teks, pres, fps)
    assert [s["nomor_dok"] for s in seg] == [[2, 4], [3]]

    # semua sumber yang cocok ikut didaftar, termasuk yang tumpang tindih (dokumen 2 dan 4)
    sumber = sumber_teratas(seg)
    assert [(a["nomor"], a["kata"]) for a in sumber] == [(2, 5), (4, 5), (3, 2)]


def test_tanpa_kecocokan(pre):
    teks = ["Kucing hitam tidur di kasur.", "Pemerintah membangun jembatan baru."]
    nama, pres, fps = siapkan(pre, teks)
    assert susun_segmen(0, nama, teks, pres, fps) == []


def test_collision_bukan_segmen(pre):
    teks = ["kucing hitam tidur kasur", "jembatan baru provinsi timur"]
    nama, pres, fps = siapkan(pre, teks, mod=2)
    assert susun_segmen(0, nama, teks, pres, fps) == []


def test_identik_penuh(pre, contoh):
    teks = [contoh[0], contoh[0]]
    nama, pres, fps = siapkan(pre, teks)
    seg = susun_segmen(0, nama, teks, pres, fps)
    assert sum(s["kata"] for s in seg) / len(pres[0]["words"]) > 0.99
