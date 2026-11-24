from core import highlight as hl
from core.compare import ambil_pasangan, bandingkan_semua
from core.ngram import buat_ngram
from core.rolling_hash import buat_fingerprint


def siapkan(pre, teks_list, n=2, mod=10**9):
    pres = [pre.proses(t) for t in teks_list]
    fps = [buat_fingerprint(buat_ngram(p["tokens"], n), 3, mod) for p in pres]
    return pres, fps, bandingkan_semua(fps)


def label_x(pres, fps, hasil, x, y):
    r = ambil_pasangan(hasil, x, y)
    return hl.label_pasangan(hl.cakupan_kata(len(pres[x]["words"]), fps[x], r["idx_x"]))


def test_imbuhan_dan_kapital_tetap_ter_highlight(pre):
    a = "Tim kami Mengembangkan Sistem deteksi plagiat."
    b = "Sebuah aplikasi dikembangkan sistem baru."
    pres, fps, hasil = siapkan(pre, [a, b])
    html_a = hl.render(a, pres[0]["words"], label_x(pres, fps, hasil, 0, 1))
    html_b = hl.render(b, pres[1]["words"], label_x(pres, fps, hasil, 1, 0))
    assert ">Mengembangkan Sistem</mark>" in html_a
    assert ">dikembangkan sistem</mark>" in html_b


def test_kata_henti_di_tengah_ikut_ter_highlight(pre):
    a = "Sistem ini mengembangkan deteksi."
    b = "Sistem mengembangkan."
    pres, fps, hasil = siapkan(pre, [a, b])
    html_a = hl.render(a, pres[0]["words"], label_x(pres, fps, hasil, 0, 1))
    assert ">Sistem ini mengembangkan</mark>" in html_a


def test_identik_cakupan_penuh(pre, contoh):
    pres, fps, hasil = siapkan(pre, [contoh[0], contoh[0]])
    tandai, total, persen = hl.statistik(label_x(pres, fps, hasil, 0, 1))
    assert persen > 99


def test_tanpa_kecocokan_tanpa_highlight(pre):
    a, b = "Kucing hitam tidur di kasur.", "Pemerintah membangun jembatan baru."
    pres, fps, hasil = siapkan(pre, [a, b])
    assert "<mark" not in hl.render(a, pres[0]["words"], label_x(pres, fps, hasil, 0, 1))


def test_karakter_html_di_escape(pre):
    a = "<script>alert(1)</script> algoritma rabin karp & hash"
    b = "algoritma rabin karp"
    pres, fps, hasil = siapkan(pre, [a, b])
    keluaran = hl.render(a, pres[0]["words"], label_x(pres, fps, hasil, 0, 1))
    assert "<script>" not in keluaran
    assert "&lt;script&gt;" in keluaran and "&amp;" in keluaran


def test_spurious_hit_tidak_ter_highlight(pre):
    a, b = "kucing hitam tidur kasur", "jembatan baru provinsi timur"
    pres, fps, hasil = siapkan(pre, [a, b], mod=2)
    assert hasil[(0, 1)]["spurious"] > 0
    assert "<mark" not in hl.render(a, pres[0]["words"], label_x(pres, fps, hasil, 0, 1))
