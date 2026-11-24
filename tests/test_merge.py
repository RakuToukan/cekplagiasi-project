from core.merge import baca_korpus, bangun_korpus, korpus_ke_teks


def test_tiga_dokumen_tiga_baris():
    files = [
        ("C.txt", b"Paragraf satu.\n\nParagraf dua\tdengan tab."),
        ("A.txt", b"Dokumen A\r\nbaris kedua"),
        ("B.txt", "Dokumen B ünïcode".encode("utf-8")),
    ]
    docs, log = bangun_korpus(files)
    korpus = korpus_ke_teks(docs)
    baris = korpus.splitlines()
    assert log == []
    assert len(baris) == 3
    assert [b.split("\t")[0] for b in baris] == ["A.txt", "B.txt", "C.txt"]
    assert baris[2] == "C.txt\tParagraf satu. Paragraf dua dengan tab."
    assert all(b.count("\t") == 1 for b in baris)


def test_dokumen_kosong_dilewati():
    docs, log = bangun_korpus([("A.txt", b"isi"), ("kosong.txt", b"  \n "), ("x.pdf", b"bukan pdf")])
    assert [d[0] for d in docs] == ["A.txt"]
    assert len(log) == 2


def test_nama_duplikat():
    docs, _ = bangun_korpus([("A.txt", b"satu"), ("A.txt", b"dua")])
    assert [d[0] for d in docs] == ["A.txt", "A.txt (2)"]


def test_baca_korpus_bolak_balik():
    docs, _ = bangun_korpus([("A.txt", b"satu dua"), ("B.txt", b"tiga\nempat")])
    hasil, log = baca_korpus(korpus_ke_teks(docs) + "baris tanpa tab\n\n")
    assert hasil == docs
    assert len(log) == 1
