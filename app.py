"""TimPa (Teks Similarity Plagiasi): aplikasi Streamlit deteksi kemiripan dokumen.

Backend: preprocessing Sastrawi, n-gram kata, Rolling Hash, pencocokan Rabin-Karp,
lalu Jaccard Coefficient. Parameter backend tetap (n=2, b=3, q=10^9) dan
tidak ditampilkan di UI.

Jalankan: streamlit run app.py
"""
import html
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

import streamlit as st

from core.compare import ambil_pasangan, bandingkan_semua
from core.laporan import CSS_DOKUMEN, chip, daftar_sumber, kartu_segmen, laporan_html, legenda, render_dokumen
from core.merge import bangun_korpus
from core.ngram import buat_ngram
from core.preprocess import PreprosesingTeks
from core.rolling_hash import MOD_NOTEBOOK, buat_fingerprint
from core.segmen import sumber_teratas, susun_segmen

N_GRAM, BASIS, MODULUS = 2, 3, MOD_NOTEBOOK
WIB = timezone(timedelta(hours=7))
CONTOH = [
    ("Coba dokumen contoh", Path(__file__).parent / "sample_docs", "Dokumen contoh"),
    ("Coba contoh semua plagiat (4 dokumen)", Path(__file__).parent / "sample_docs_plagiat", "Contoh semua plagiat"),
]
KOLOM_TABEL = [4.2, 2.6, 2.6, 1.6]

st.set_page_config(page_title="TimPa · Cek Plagiasi", page_icon="📄", layout="wide")


# ================================================================ backend

@st.cache_resource(show_spinner=False)
def ambil_preprocessor() -> PreprosesingTeks:
    return PreprosesingTeks()


@st.cache_data(show_spinner=False, max_entries=32)
def analisis(docs: tuple) -> list:
    """Setiap dokumen bergantian menjadi dokumen uji X terhadap semua dokumen lain."""
    nama = [d[0] for d in docs]
    teks = [d[1] for d in docs]
    pre = ambil_preprocessor()
    pres = [pre.proses(t) for t in teks]
    fps = [buat_fingerprint(buat_ngram(p["tokens"], N_GRAM), BASIS, MODULUS) for p in pres]
    hasil = bandingkan_semua(fps)

    per_x = []
    for ix in range(len(docs)):
        skor = []
        for iy in range(len(docs)):
            if iy == ix:
                continue
            r = ambil_pasangan(hasil, ix, iy)
            skor.append({k: r[k] for k in ("jaccard", "sama", "gabungan")} | {"nama": nama[iy]})
        skor.sort(key=lambda r: -r["jaccard"])
        segmen = susun_segmen(ix, nama, teks, pres, fps)
        jaccard_ke = {r["nama"]: r["jaccard"] for r in skor}
        sumber = [
            a | {"nama": nama[a["y"]], "jaccard": jaccard_ke[nama[a["y"]]]}
            for a in sumber_teratas(segmen, len(pres[ix]["words"]))
        ]
        per_x.append(
            {
                "nama": nama[ix],
                "teks": teks[ix],
                "words": pres[ix]["words"],
                "skor": skor,
                "segmen": segmen,
                "sumber": sumber,
                "similarity": skor[0]["jaccard"] if skor else 0.0,
                "kata_cocok": sum(s["kata"] for s in segmen),
            }
        )
    return per_x


# ================================================================ util

def esc(teks) -> str:
    return html.escape(str(teks), quote=True)


def angka(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def tingkat(persen: float) -> tuple:
    """Klasifikasi: ringan < 30%, sedang 30-70%, berat > 70%."""
    if persen < 30:
        return "rendah", "Kemiripan Rendah", "Aman"
    if persen <= 70:
        return "sedang", "Kemiripan Sedang", "Perlu Ditinjau"
    return "tinggi", "Kemiripan Tinggi", "Berisiko"


def judul_dokumen(nama: str) -> str:
    return Path(nama).stem


def _svg_mask(isi: str, lebar: str = "1.8") -> str:
    """SVG sebagai data URI untuk CSS mask. st.html membuang tag <svg>, jadi ikon digambar lewat CSS."""
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' "
        f"stroke-width='{lebar}' stroke-linecap='round' stroke-linejoin='round'>{isi}</svg>"
    )
    return "url(\"data:image/svg+xml;utf8," + quote(svg) + "\")"


CSS_IKON = f"""
.ico {{ display: inline-block; width: 20px; height: 20px; background: currentColor; flex: none;
  -webkit-mask: var(--m) center / contain no-repeat; mask: var(--m) center / contain no-repeat; }}
.i-dok {{ --m: {_svg_mask("<path d='M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z'/><path d='M14 3v5h5'/><path d='M9 13h6M9 17h6M9 9h1'/>")}; }}
.i-perisai {{ --m: {_svg_mask("<path d='M12 3l7 3v6c0 4.5-3 8-7 9-4-1-7-4.5-7-9V6z'/><path d='M9 12l2 2 4-4'/>", "2")}; }}
.i-info {{ --m: {_svg_mask("<circle cx='12' cy='12' r='9'/><path d='M12 11v5M12 8h.01'/>", "2")}; }}
"""
IKON_DOK = '<i class="ico i-dok"></i>'
IKON_PERISAI = '<i class="ico i-perisai"></i>'
IKON_INFO = '<i class="ico i-info"></i>'


# ================================================================ gaya

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
:root { --primary:#0e6fa3; --primary-2:#1f6fe5; --navy:#12304a; --ink:#16283a; --muted:#5b6b7b;
  --line:#e3e9ef; --bg:#f4f7fa; --soft:#e8f2f9;
  --hijau:#1f9d55; --hijau-bg:#e3f6ea; --kuning:#c98200; --kuning-bg:#fff3d6; --merah:#d93b3b; --merah-bg:#fde7e7; }
.stApp { background: var(--bg); color: var(--ink); }
[data-testid="stMain"], [data-testid="stAppViewContainer"] { overflow-x: clip; }
.stApp, .stApp p, .stApp div, .stApp label, .stApp input, .stApp button,
.stApp span:not([data-testid="stIconMaterial"]) { font-family: 'Plus Jakarta Sans', system-ui, sans-serif; }
header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"], footer, #MainMenu { display: none !important; }
.block-container, [data-testid="stMainBlockContainer"] { max-width: 1320px; padding: 0 2rem 2.5rem !important; }
@media (max-width: 640px) { .block-container, [data-testid="stMainBlockContainer"] { padding: 0 1rem 2rem !important; } }

/* topbar penuh selebar layar */
.st-key-topbar { position: relative; isolation: isolate; padding: 12px 0; margin-bottom: 18px; }
.st-key-topbar::before { content: ""; position: absolute; top: 0; bottom: 0; left: calc(50% - 50vw);
  right: calc(50% - 50vw); background: #fff;
  border-bottom: 1px solid var(--line); z-index: -1; }
.brand { display: flex; align-items: center; gap: 14px; }
.brand-ikon { width: 40px; height: 40px; border-radius: 10px; background: var(--primary); color: #fff;
  display: grid; place-items: center; flex: none; }
.brand-ikon .ico { width: 22px; height: 22px; }
.brand b { display: block; font-size: 16px; color: var(--ink); line-height: 1.2; }
.brand small { color: var(--muted); font-size: 12px; }
[class*="st-key-nav_"] button p { color: #3a4a5a; font-weight: 500; font-size: 15px; }
[class*="st-key-nav_"] button:hover p { color: var(--primary); }

/* hero */
.eyebrow { color: var(--primary); font-size: 11.5px; font-weight: 700; letter-spacing: .04em; }
.hero h1 { font-size: clamp(26px, 3.2vw, 34px); font-weight: 800; color: var(--ink); margin: 8px 0 4px; padding: 0; letter-spacing: -.01em; }
.hero p { color: var(--muted); font-size: 15px; margin: 0; }
.pill { display: inline-flex; align-items: center; gap: 8px; background: #fff; border: 1px solid var(--line);
  border-radius: 999px; padding: 9px 16px; font-size: 13px; font-weight: 600; color: var(--ink); float: right; }
.pill .ico { width: 16px; height: 16px; color: var(--primary); }
@media (max-width: 640px) { .pill { float: none; } }

/* kartu */
.st-key-card_form, .st-key-card_tabel, .kartu { background: #fff; border: 1px solid var(--line); border-radius: 18px; }
.st-key-card_form { padding: 24px 28px 22px; }
.st-key-card_tabel { padding: 24px 28px 8px; }
.kartu { padding: 22px 24px; }
.kartu.tipis { padding: 14px 20px; margin-bottom: 4px; }
.kartu-judul { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }
.kartu-judul h3 { font-size: 19px; font-weight: 700; margin: 0; padding: 0; color: var(--ink); }
.kartu-judul p { color: var(--muted); font-size: 13.5px; margin: 4px 0 0; }
.chip { background: var(--soft); color: var(--primary); border-radius: 999px; padding: 5px 14px;
  font-size: 12.5px; font-weight: 600; white-space: nowrap; }
.label { font-weight: 600; font-size: 14.5px; color: var(--ink); }
.label span { color: var(--muted); font-weight: 400; font-size: 12.5px; margin-left: 8px; }
.hint, .catatan-kecil { color: var(--muted); font-size: 12px; }

/* uploader dan input */
[data-testid="stFileUploaderDropzone"] { border: 1.5px dashed #9cc7de; background: #f8fbfd; border-radius: 12px; padding: 26px; }
.stTextInput input { border-radius: 10px; }
.stButton button, .stDownloadButton button { border-radius: 10px; font-weight: 700; }
.st-key-btn_cek button { min-height: 44px; }
[class*="st-key-btn_contoh"] button p, [class*="st-key-lihat_"] button p { color: var(--primary); font-weight: 600; }

/* panel gelap */
.panel { background: var(--navy); color: #fff; border-radius: 18px; padding: 28px; height: 100%; }
.panel .ikon { width: 42px; height: 42px; border-radius: 10px; background: rgba(255,255,255,.1);
  display: grid; place-items: center; color: #cfe6f5; }
.panel .ikon .ico { width: 22px; height: 22px; }
.panel h3 { color: #fff; font-size: 21px; font-weight: 700; margin: 22px 0 8px; padding: 0; }
.panel > p { color: #c3d2de; font-size: 13.5px; line-height: 1.55; margin: 0 0 22px; }
.langkah { display: flex; gap: 14px; margin-bottom: 18px; }
.langkah i { flex: none; width: 26px; height: 26px; border-radius: 50%; background: rgba(255,255,255,.12);
  display: grid; place-items: center; font-style: normal; font-size: 12px; color: #dbe8f2; }
.langkah b { display: block; font-size: 14px; color: #fff; margin-bottom: 4px; }
.langkah span { font-size: 12px; color: #b5c6d4; line-height: 1.5; }

/* tabel hasil */
.th { color: #3a4a5a; font-size: 13px; font-weight: 600; }
[class*="st-key-row_"] { border-top: 1px solid var(--line); padding: 8px 0 4px; }
.sel-judul { display: flex; align-items: center; gap: 14px; }
.sel-judul .ikon { width: 40px; height: 40px; border-radius: 10px; background: var(--soft); color: var(--primary);
  display: grid; place-items: center; flex: none; }
.sel-judul .ikon .ico { width: 20px; height: 20px; }
.sel-judul b { display: block; font-size: 15px; color: var(--ink); word-break: break-word; }
.sel-judul small { color: var(--muted); font-size: 12px; }
.sel-waktu { color: #4a5a6a; font-size: 14px; }
.sim { display: flex; align-items: center; gap: 12px; }
.sim-badge { border-radius: 999px; padding: 5px 14px; font-weight: 700; font-size: 13px; min-width: 56px; text-align: center; }
.sim-bar { flex: 1; max-width: 100px; height: 5px; background: #e3ebf0; border-radius: 9px; overflow: hidden; }
.sim-bar i { display: block; height: 100%; border-radius: 9px; }
.rendah .sim-badge, .badge-rendah { background: var(--hijau-bg); color: var(--hijau); }
.sedang .sim-badge, .badge-sedang { background: var(--kuning-bg); color: var(--kuning); }
.tinggi .sim-badge, .badge-tinggi { background: var(--merah-bg); color: var(--merah); }
.rendah .sim-bar i { background: var(--hijau); } .sedang .sim-bar i { background: var(--kuning); }
.tinggi .sim-bar i { background: var(--merah); }
.kosong { text-align: center; color: var(--muted); font-size: 14px; padding: 26px 0 30px; border-top: 1px solid var(--line); }

.kaki { display: flex; justify-content: space-between; gap: 12px; color: var(--muted); font-size: 12px; margin-top: 6px; }
.kaki span { display: inline-flex; align-items: center; gap: 8px; }
.kaki .ico { width: 15px; height: 15px; flex: none; }

/* halaman rincian */
.remah { color: var(--muted); font-size: 13px; margin-bottom: 6px; }
.judul-rinci { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.judul-rinci h1 { font-size: clamp(22px, 2.6vw, 28px); font-weight: 800; margin: 0; padding: 0; color: var(--ink); word-break: break-word; }
.badge { border-radius: 999px; padding: 4px 12px; font-weight: 700; font-size: 12.5px; }
.meta { color: var(--muted); font-size: 13.5px; margin-top: 8px; }
.meta b { color: var(--ink); }
.ringkas { display: grid; grid-template-columns: minmax(260px, 1.15fr) 2.85fr; gap: 24px; align-items: center; }
.ringkas-kiri { display: flex; gap: 20px; align-items: center; padding-right: 24px; border-right: 1px solid var(--line); }
.cincin { --c: var(--hijau); width: 92px; height: 92px; border-radius: 50%; flex: none; display: grid; place-items: center;
  background: conic-gradient(var(--c) calc(var(--p) * 1%), #e6edf2 0); }
.cincin.sedang { --c: var(--kuning); } .cincin.tinggi { --c: var(--merah); }
.cincin > div { width: 74px; height: 74px; border-radius: 50%; background: #fff; display: flex; flex-direction: column;
  align-items: center; justify-content: center; }
.cincin b { font-size: 21px; font-weight: 800; color: var(--c); line-height: 1; }
.cincin span { font-size: 8.5px; font-weight: 700; color: var(--c); letter-spacing: .04em; margin-top: 3px; }
.ringkas-kiri h4 { font-size: 16px; font-weight: 700; margin: 0 0 6px; padding: 0; color: var(--ink); }
.ringkas-kiri p { color: var(--muted); font-size: 13px; line-height: 1.55; margin: 0; }
.statistik { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }
.stat { border: 1px solid var(--line); border-radius: 12px; padding: 14px 16px; }
.stat small { color: var(--muted); font-size: 12.5px; }
.stat b { display: block; font-size: 22px; font-weight: 800; color: var(--ink); margin: 4px 0; }
.stat span { color: var(--muted); font-size: 11.5px; word-break: break-word; }
@media (max-width: 1100px) { .ringkas { grid-template-columns: 1fr; } .ringkas-kiri { border-right: 0; padding-right: 0; } }
@media (max-width: 760px) { .statistik { grid-template-columns: repeat(2, 1fr); } }
.kartu.isi { padding: 0; overflow: hidden; }
.kepala { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px;
  padding: 16px 22px; border-bottom: 1px solid var(--line); background: #fbfcfd; }
.kepala b { font-size: 14.5px; color: var(--ink); }
.kepala small { display: block; color: var(--muted); font-size: 12.5px; margin-top: 2px; }
.kepala .kanan { color: var(--muted); font-size: 12.5px; white-space: nowrap; }
.gulir { max-height: 760px; overflow-y: auto; padding: 22px 26px; }
.skor-tabel { width: 100%; border-collapse: collapse; font-size: 12.5px; margin-bottom: 16px; }
.skor-tabel th { text-align: left; color: var(--muted); font-weight: 600; padding: 6px 4px; border-bottom: 1px solid var(--line); }
.skor-tabel td { padding: 7px 4px; border-bottom: 1px solid var(--line); color: var(--ink); word-break: break-word; }
.skor-tabel td.n { text-align: right; white-space: nowrap; font-weight: 600; }
.subjudul { font-size: 12px; font-weight: 700; letter-spacing: .04em; color: var(--muted); margin: 4px 0 10px; }
.badge-netral { background: #eef2f5; color: var(--muted); }
.kepala .badge { margin-left: 8px; font-size: 11.5px; padding: 3px 10px; }
.judul-bagian { margin-top: 10px; }
.judul-bagian h3 { font-size: 19px; font-weight: 700; color: var(--ink); margin: 0; padding: 0; }
.judul-bagian p { color: var(--muted); font-size: 13.5px; margin: 4px 0 0; }
.stTabs [data-baseweb="tab"] p { font-weight: 600; }
.catatan { background: #eef5fd; border: 1px solid #cfe1f6; border-radius: 12px; padding: 14px 18px;
  color: #1f4f8a; font-size: 13px; line-height: 1.55; margin-top: 6px; }
.catatan b { color: #1a4a86; }

/* halaman statis */
.statis h2 { font-size: 22px; font-weight: 800; margin: 0 0 6px; padding: 0; }
.statis h4 { font-size: 15.5px; font-weight: 700; margin: 20px 0 6px; padding: 0; }
.statis p, .statis li { color: #34475a; font-size: 14.5px; line-height: 1.7; }
.tim { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-top: 10px; }
.tim div { border: 1px solid var(--line); border-radius: 12px; padding: 14px 16px; }
.tim b { display: block; font-size: 14px; } .tim span { color: var(--muted); font-size: 12.5px; }
"""


# ================================================================ state & navigasi

ss = st.session_state
ss.setdefault("riwayat", [])
ss.setdefault("view", "cek")
ss.setdefault("pilihan", None)
ss.setdefault("kunci_upload", 0)
ss.setdefault("pesan", None)


def pindah(view: str):
    ss.view = view


def buka(id_batch: int, ix: int):
    ss.pilihan = (id_batch, ix)
    ss.view = "detail"


def cari_batch(id_batch: int):
    return next((b for b in ss.riwayat if b["id"] == id_batch), None)


def jalankan_cek(files: list, judul: str):
    docs, log = bangun_korpus(files, satu_baris=False)
    if len(docs) < 2:
        ss.pesan = ("error", "Butuh minimal dua dokumen yang bisa dibaca. " + " ".join(log))
        return
    with st.spinner("Memeriksa kemiripan dokumen..."):
        analisis(tuple(docs))
    ss.riwayat.insert(
        0,
        {
            "id": (ss.riwayat[0]["id"] + 1) if ss.riwayat else 1,
            "judul": judul.strip(),
            "waktu": datetime.now(WIB).strftime("%d/%m/%Y; %H:%M"),
            "docs": tuple(docs),
        },
    )
    ss.kunci_upload += 1
    if log:
        ss.pesan = ("warning", f"{len(docs)} dokumen diperiksa. Dilewati: " + "; ".join(log))
    else:
        ss.pesan = ("success", f"{len(docs)} dokumen selesai diperiksa. Hasil ada di tabel di bawah.")


# ================================================================ komponen

def topbar():
    aktif = "cek" if ss.view == "detail" else ss.view
    st.html(f"<style>{CSS}{CSS_IKON}{CSS_DOKUMEN}.st-key-nav_{aktif} button p {{ color: var(--primary) !important; "
            "font-weight: 700 !important; }}</style>")
    with st.container(key="topbar"):
        c1, c2, c3 = st.columns([3.3, 3.5, 2.2], vertical_alignment="center")
        c1.html(
            f'<div class="brand"><div class="brand-ikon">{IKON_DOK}</div>'
            "<div><b>TimPa (Teks Similarity Plagiasi)</b><small>Ruang Kerja Akademik</small></div></div>"
        )
        with c2:
            n1, n2, n3 = st.columns(3)
            n1.button("Cek Plagiasi", key="nav_cek", type="tertiary", on_click=pindah, args=("cek",))
            n2.button("Panduan", key="nav_panduan", type="tertiary", on_click=pindah, args=("panduan",))
            n3.button("Tentang Kami", key="nav_tentang", type="tertiary", on_click=pindah, args=("tentang",))
        if ss.view == "detail":
            c3.button("← Kembali ke Ruang Cek", key="btn_kembali", on_click=pindah, args=("cek",), width="stretch")


def kaki_halaman():
    st.html(
        f'<div class="kaki"><span>{IKON_INFO}Persentase similarity menunjukkan kemiripan teks, '
        "bukan penentu plagiasi secara mutlak.</span><span>Cek Plagiasi</span></div>"
    )


def sel_similarity(persen: float) -> str:
    lvl = tingkat(persen)[0]
    return (
        f'<div class="sim {lvl}"><span class="sim-badge">{persen:.0f}%</span>'
        f'<span class="sim-bar"><i style="width:{min(persen, 100):.1f}%"></i></span></div>'
    )


# ================================================================ halaman: cek plagiasi

def halaman_cek():
    kiri, kanan = st.columns([2.75, 1], vertical_alignment="bottom")
    kiri.html(
        '<div class="hero"><div class="eyebrow">RUANG KERJA AKADEMIK</div>'
        "<h1>Periksa kemiripan, jaga orisinalitas.</h1>"
        "<p>Bandingkan dokumen dengan dataset Anda dalam satu tempat.</p></div>"
    )
    kanan.html(f'<div class="pill">{IKON_PERISAI}Pemeriksaan dokumen</div>')

    form, panel = st.columns([2.75, 1], gap="medium")
    with form:
        with st.container(key="card_form"):
            st.html(
                '<div class="kartu-judul"><div><h3>Formulir Cek Plagiasi</h3>'
                "<p>Unggah minimal dua dokumen. Setiap dokumen dibandingkan dengan dokumen lainnya.</p></div>"
                '<span class="chip">01 / Unggah</span></div>'
            )
            st.html('<div class="label">Dataset</div>')
            files = st.file_uploader(
                "Dataset", type=["txt", "pdf", "docx"], accept_multiple_files=True,
                key=f"unggah_{ss.kunci_upload}", label_visibility="collapsed",
            )
            st.html('<div class="hint">PDF, TXT, DOCX &bull; minimal 2 dokumen &bull; maks. 10 MB per file</div>')
            st.html('<div class="label">Judul Submisi <span>Opsional</span></div>')
            judul = st.text_input(
                "Judul Submisi", key=f"judul_{ss.kunci_upload}", label_visibility="collapsed",
                placeholder="Jika kosong maka mengikuti judul dokumen uji",
            )
            a, b = st.columns([1.7, 1], vertical_alignment="center")
            a.html('<div class="catatan-kecil">Pastikan minimal dua file telah dipilih sebelum melanjutkan.</div>')
            if b.button("Cek Plagiasi  →", type="primary", key="btn_cek", width="stretch"):
                if not files or len(files) < 2:
                    ss.pesan = ("error", "Pilih minimal dua dokumen terlebih dahulu.")
                else:
                    jalankan_cek([(f.name, f.getvalue()) for f in files], judul)
                st.rerun()
            tombol = [(lbl, sorted(f.glob("*.txt")), jdl) for lbl, f, jdl in CONTOH if f.exists()]
            for kol, (lbl, berkas, jdl) in zip(st.columns(len(tombol) or 1), tombol):
                if berkas and kol.button(lbl, type="tertiary", key=f"btn_contoh_{jdl}"):
                    jalankan_cek([(p.name, p.read_bytes()) for p in berkas], jdl)
                    st.rerun()
            if ss.pesan:
                jenis, isi = ss.pesan
                getattr(st, jenis)(isi)
                ss.pesan = None

    with panel:
        st.html(
            f'<div class="panel"><div class="ikon">{IKON_DOK}</div><h3>Dari dokumen ke insight.</h3>'
            "<p>Tiga langkah untuk memahami kemiripan tulisan Anda.</p>"
            '<div class="langkah"><i>1</i><div><b>Unggah dokumen</b><span>Pilih dua dokumen atau lebih '
            "sebagai dataset. Setiap dokumen bergantian menjadi dokumen uji.</span></div></div>"
            '<div class="langkah"><i>2</i><div><b>Mulai pengecekan</b><span>Tambahkan judul submisi, '
            "lalu klik Cek Plagiasi.</span></div></div>"
            '<div class="langkah"><i>3</i><div><b>Tinjau hasilnya</b><span>Lihat persentase similarity '
            "dan buka rincian bagian yang cocok.</span></div></div></div>"
        )

    tabel_hasil()
    kaki_halaman()


def tabel_hasil():
    jumlah = sum(len(b["docs"]) for b in ss.riwayat)
    with st.container(key="card_tabel"):
        st.html(
            '<div class="kartu-judul"><div><h3>Tabel Hasil Pengecekan '
            f'<span class="chip" style="margin-left:10px;vertical-align:3px">{jumlah} hasil</span></h3>'
            "<p>Riwayat pemeriksaan dokumen Anda.</p></div></div>"
        )
        if not ss.riwayat:
            st.html('<div class="kosong">Belum ada pemeriksaan. Unggah dokumen di formulir di atas.</div>')
            return
        kepala = st.columns(KOLOM_TABEL)
        for kol, teks in zip(kepala, ["Judul Submisi", "Tanggal/Waktu", "Similarity Tertinggi", "Aksi"]):
            kol.html(f'<div class="th">{teks}</div>')
        for batch in ss.riwayat:
            for ix, hx in enumerate(analisis(batch["docs"])):
                with st.container(key=f"row_{batch['id']}_{ix}"):
                    c = st.columns(KOLOM_TABEL, vertical_alignment="center")
                    sub = f"Submisi: {esc(batch['judul'])}" if batch["judul"] else esc(hx["nama"])
                    c[0].html(
                        f'<div class="sel-judul"><div class="ikon">{IKON_DOK}</div>'
                        f'<div><b>{esc(judul_dokumen(hx["nama"]))}</b><small>{sub}</small></div></div>'
                    )
                    c[1].html(f'<div class="sel-waktu">{esc(batch["waktu"])}</div>')
                    c[2].html(sel_similarity(hx["similarity"]))
                    c[3].button("Lihat Hasil  →", key=f"lihat_{batch['id']}_{ix}", type="tertiary",
                                on_click=buka, args=(batch["id"], ix))


# ================================================================ halaman: rincian hasil

def kartu_pembanding(hy: dict) -> str:
    """Dokumen pembanding utuh dengan bagian yang cocok dengan dokumen mana pun di dataset.

    Angka pada highlight adalah nomor dokumen sumber kecocokan (lihat legenda).
    """
    total_y = len(hy["words"])
    persen = 100 * hy["kata_cocok"] / total_y if total_y else 0.0
    if hy["segmen"]:
        lvl_y, label_y, _ = tingkat(hy["similarity"])
        badge = f'<span class="badge badge-{lvl_y}">{label_y}</span>'
    else:
        badge = '<span class="badge badge-netral">Tidak terdeteksi plagiat</span>'
    return (
        f'<div class="kartu isi"><div class="kepala"><div><b>{esc(hy["nama"])}</b> {badge}'
        f"<small>{info_dokumen(hy)}</small></div>"
        f'<span class="kanan">{len(hy["segmen"])} bagian</span></div>'
        f'<div class="gulir">{render_dokumen(hy["teks"], hy["words"], hy["segmen"], tautan=False)}</div></div>'
    )


def info_dokumen(hy: dict) -> str:
    total_y = len(hy["words"])
    persen = 100 * hy["kata_cocok"] / total_y if total_y else 0.0
    terdekat = f' dengan {esc(hy["skor"][0]["nama"])}' if hy["skor"] else ""
    return (
        f'Similarity tertinggi {hy["similarity"]:.2f}%{terdekat} &bull; '
        f'{angka(hy["kata_cocok"])} dari {angka(total_y)} kata cocok ({persen:.1f}%)'
    )


def tampil_pembanding(hy: dict, nomor: int):
    """Satu tab: pratinjau dokumen (kiri) dan rincian bagian cocok dengan dokumen lain (kanan)."""
    awalan = f"d{nomor}-"
    segmen_y = hy["segmen"]
    total_y = len(hy["words"])
    persen = 100 * hy["kata_cocok"] / total_y if total_y else 0.0
    if segmen_y:
        lvl_y, label_y, _ = tingkat(hy["similarity"])
        badge = f'<span class="badge badge-{lvl_y}">{label_y}</span>'
    else:
        badge = '<span class="badge badge-netral">Tidak terdeteksi plagiat</span>'
    kiri, kanan = st.columns([1.12, 0.88], gap="medium")
    kiri.html(
        f'<div class="kartu isi"><div class="kepala"><div><b>Pratinjau Dokumen Pembanding &mdash; '
        f'{esc(hy["nama"])}</b> {badge}'
        "<small>Angka = nomor dokumen yang cocok. Klik teks yang ditandai untuk melihat rinciannya.</small></div>"
        f'<span class="kanan">{angka(total_y)} kata</span></div>'
        f'<div class="gulir">{render_dokumen(hy["teks"], hy["words"], segmen_y, awalan_id=awalan)}</div></div>'
    )
    kartu = "".join(
        kartu_segmen(s, awalan_id=awalan) for s in sorted(segmen_y, key=lambda s: (-s["kata"], s["no"]))
    )
    kanan.html(
        f'<div class="kartu isi"><div class="kepala"><div><b>Rincian Bagian Cocok</b>'
        f"<small>{info_dokumen(hy)}</small></div></div><div class=\"gulir\">"
        f'<div class="subjudul">SUMBER TERINDIKASI PLAGIAT ({len(hy["sumber"])})</div>'
        '<div class="hint">Semua dokumen yang memiliki bagian cocok dengan dokumen ini. Persentase = kata yang '
        "cocok dengan sumber tersebut / total kata. Satu bagian bisa cocok dengan beberapa sumber, jadi "
        "jumlah persentase bisa melebihi 100%.</div>"
        f"{daftar_sumber(hy['sumber'])}"
        f'<div class="subjudul" style="margin-top:20px">BAGIAN COCOK ({len(segmen_y)})</div>'
        f'{kartu or "<p class=hint>Tidak ada bagian yang cocok dengan dokumen lain.</p>"}</div></div>'
    )


def halaman_detail():
    batch = cari_batch(ss.pilihan[0]) if ss.pilihan else None
    if batch is None:
        ss.view = "cek"
        st.rerun()
    per_x = analisis(batch["docs"])
    hx = per_x[ss.pilihan[1]]
    segmen, skor = hx["segmen"], hx["skor"]
    lvl, label, status = tingkat(hx["similarity"])
    total = len(hx["words"])
    persen_cocok = 100 * hx["kata_cocok"] / total if total else 0.0
    n_identik = sum(s["jenis"] == "identik" for s in segmen)
    judul = batch["judul"] or judul_dokumen(hx["nama"])
    pembanding = [r["nama"] for r in skor]
    teks_pembanding = pembanding[0] if len(pembanding) == 1 else f"{len(pembanding)} dokumen"
    ext = Path(hx["nama"]).suffix.lstrip(".").upper() or "TXT"
    indeks = {p["nama"]: i for i, p in enumerate(per_x)}
    nama_semua = [p["nama"] for p in per_x]
    html_legenda = legenda(nama_semua)

    kiri, kanan = st.columns([3, 1], vertical_alignment="bottom")
    kiri.html(
        '<div class="remah">Ruang Kerja Akademik / Tabel Hasil Pengecekan / Rincian Hasil</div>'
        f'<div class="judul-rinci"><h1>{esc(judul)}</h1>'
        f'<span class="badge badge-{lvl}">{label} ({status})</span></div>'
        f'<div class="meta">Diperiksa: <b>{esc(batch["waktu"])}</b> &bull; Dokumen: <b>{esc(hx["nama"])}</b>'
        f' &bull; Dibandingkan dengan: <b title="{esc(", ".join(pembanding))}">{esc(teks_pembanding)}</b></div>'
    )
    laporan = laporan_html(
        f"Laporan Cek Plagiasi: {judul}",
        [("Dokumen", hx["nama"]), ("Diperiksa", batch["waktu"]), ("Dibandingkan dengan", ", ".join(pembanding))],
        [
            ("Similarity (Jaccard tertinggi)", f"{hx['similarity']:.2f}% ({label})"),
            ("Total kata diperiksa", angka(total)),
            ("Kata terdeteksi cocok", f"{angka(hx['kata_cocok'])} ({persen_cocok:.1f}%)"),
            ("Bagian cocok", f"{len(segmen)} segmen ({n_identik} identik, {len(segmen) - n_identik} parafrase)"),
        ],
        skor,
        render_dokumen(hx["teks"], hx["words"], segmen, tautan=False),
        segmen,
        "".join(kartu_pembanding(hy) for hy in per_x),
        html_legenda,
        daftar_sumber(hx["sumber"]),
    )
    kanan.download_button(
        "Unduh Laporan", laporan.encode("utf-8"), f"laporan_{judul_dokumen(hx['nama'])}.html", "text/html",
        type="primary", width="stretch", help="File HTML. Buka di browser lalu Ctrl+P untuk simpan sebagai PDF.",
    )

    terbaik = skor[0] if skor else None
    deskripsi = (
        f"Kemiripan tertinggi dengan {esc(terbaik['nama'])} (Jaccard {terbaik['jaccard']:.2f}%). "
        f"{angka(hx['kata_cocok'])} kata cocok tersebar di {len(segmen)} segmen."
        if terbaik else "Tidak ada dokumen pembanding."
    )
    st.html(
        f'<div class="kartu"><div class="ringkas"><div class="ringkas-kiri">'
        f'<div class="cincin {lvl}" style="--p:{min(hx["similarity"], 100):.1f}"><div>'
        f'<b>{hx["similarity"]:.0f}%</b><span>SIMILARITY</span></div></div>'
        f"<div><h4>Tingkat {label}</h4><p>{deskripsi}</p></div></div>"
        '<div class="statistik">'
        f'<div class="stat"><small>Total Kata Diperiksa</small><b>{angka(total)}</b><span>{ext}</span></div>'
        f'<div class="stat"><small>Kata Terdeteksi Cocok</small><b>{angka(hx["kata_cocok"])}</b>'
        f"<span>{persen_cocok:.1f}% dari total teks</span></div>"
        f'<div class="stat"><small>Bagian Cocok</small><b>{len(segmen)} Segmen</b>'
        f"<span>{n_identik} identik, {len(segmen) - n_identik} parafrase</span></div>"
        f'<div class="stat"><small>Fingerprint Sama</small><b>{terbaik["sama"] if terbaik else 0}</b>'
        f'<span>dari {terbaik["gabungan"] if terbaik else 0} fingerprint gabungan</span></div>'
        "</div></div></div>"
    )

    baris_skor = "".join(
        f'<tr><td>{chip(indeks[r["nama"]] + 1)}{esc(r["nama"])}</td>'
        f'<td class="n">{r["sama"]} / {r["gabungan"]}</td><td class="n">{r["jaccard"]:.2f}%</td></tr>'
        for r in skor
    )
    st.html(
        f'<div class="kartu tipis">{html_legenda}<div class="hint" style="margin-top:6px">'
        "Angka pada highlight menunjukkan dokumen yang cocok dengan bagian tersebut. "
        "Merah: teks identik. Kuning: parafrase dekat.</div>"
        f'<div class="subjudul" style="margin-top:16px">SKOR {esc(hx["nama"]).upper()} TERHADAP DOKUMEN LAIN</div>'
        '<table class="skor-tabel"><tr><th>Dokumen pembanding</th><th style="text-align:right">Sama / Gabungan</th>'
        f'<th style="text-align:right">Jaccard</th></tr>{baris_skor}</table></div>'
    )

    st.html(
        '<div class="judul-bagian"><h3>Pratinjau Dokumen Pembanding</h3><p>Semua dokumen di dataset ditampilkan '
        "satu per tab. Setiap dokumen bergiliran dibandingkan dengan dokumen sisanya; bagian yang cocok "
        "ditandai dengan nomor dokumen sumbernya.</p></div>"
    )
    label_tab = [f"{i + 1}. {p['nama']} · {p['similarity']:.1f}%" for i, p in enumerate(per_x)]
    tabs = st.tabs(label_tab, default=label_tab[ss.pilihan[1]])
    for i, (tab, hy) in enumerate(zip(tabs, per_x)):
        with tab:
            tampil_pembanding(hy, i + 1)
    st.html(
        '<div class="catatan"><b>Catatan Akademik: Persentase similarity menunjukkan kemiripan teks, bukan '
        "penentu plagiasi secara mutlak. Tinjau setiap segmen yang ditandai sebelum memberikan penilaian akhir.</b>"
        "<br>Similarity = Jaccard Coefficient tertinggi terhadap dokumen pembanding. Merah: teks identik. "
        "Kuning: sama setelah huruf kecil, hapus kata henti, dan potong imbuhan (parafrase dekat).</div>"
    )


# ================================================================ halaman statis

def halaman_panduan():
    st.html(
        '<div class="kartu statis"><h2>Panduan</h2>'
        "<p>Cara memeriksa kemiripan dokumen dengan TimPa.</p>"
        "<h4>1. Unggah dataset</h4><p>Pilih minimal dua dokumen berformat PDF, TXT, atau DOCX. "
        "PDF hasil scan (gambar) tidak bisa dibaca karena tidak memiliki teks.</p>"
        "<h4>2. Cek plagiasi</h4><p>Isi judul submisi bila perlu, lalu klik <b>Cek Plagiasi</b>. "
        "Setiap dokumen bergantian menjadi dokumen uji dan dibandingkan dengan semua dokumen lain.</p>"
        "<h4>3. Baca hasil</h4><p>Tabel hasil menampilkan satu baris per dokumen uji. Klik <b>Lihat Hasil</b> "
        "untuk membuka pratinjau dokumen dengan bagian yang cocok diberi nomor dan warna.</p>"
        "<h4>Arti tingkat kemiripan</h4><ul>"
        "<li><b>Rendah</b> (di bawah 30%): aman.</li>"
        "<li><b>Sedang</b> (30% sampai 70%): perlu ditinjau.</li>"
        "<li><b>Tinggi</b> (di atas 70%): berisiko plagiasi.</li></ul>"
        "<h4>Arti warna segmen</h4><ul>"
        "<li><b>Merah, Kecocokan Identik</b>: teks sama persis dengan dokumen pembanding (huruf besar dan tanda baca diabaikan).</li>"
        "<li><b>Kuning, Parafrase Dekat</b>: susunan kata dasarnya sama, tetapi imbuhan, kata henti, atau ejaan berbeda.</li></ul>"
        "<h4>Cara kerja singkat</h4><p>Teks dibersihkan (huruf kecil, hapus angka dan tanda baca), kata henti "
        "dihapus, dan imbuhan dipotong dengan Sastrawi. Teks lalu dipecah menjadi n-gram dua kata, setiap n-gram "
        "diubah menjadi nilai hash dengan Rolling Hash, dan dicocokkan dengan algoritma Rabin-Karp. Skor dihitung "
        "dengan Jaccard Coefficient: jumlah fingerprint yang sama dibagi jumlah fingerprint unik gabungan "
        "kedua dokumen.</p></div>"
    )
    kaki_halaman()


def halaman_tentang():
    anggota = [
        ("Rafif Rizal Ali Ahmadi", "Perencanaan, implementasi hashing dan algoritma, pengujian"),
        ("Aldi Nur Cholis", "Studi literatur, implementasi hashing dan algoritma"),
        ("Putri Aulia Rahmah", "Studi literatur, preprocessing, laporan dan dokumentasi"),
        ("Rakha Ariqah Wijaya", "Pengajuan proposal, data collection"),
    ]
    tim = "".join(f"<div><b>{esc(n)}</b><span>{esc(p)}</span></div>" for n, p in anggota)
    st.html(
        '<div class="kartu statis"><h2>Tentang Kami</h2>'
        "<p>TimPa (Teks Similarity Plagiasi) adalah prototipe platform deteksi plagiarisme untuk Tugas Akhir "
        "mata kuliah Desain dan Analisis Algoritma. Aplikasi ini mengukur tingkat kemiripan suatu dokumen "
        "dengan dokumen lainnya menggunakan algoritma Rabin-Karp, sebagai alternatif gratis dari alat "
        "deteksi plagiarisme berbayar.</p>"
        f"<h4>Tim</h4><div class=\"tim\">{tim}</div></div>"
    )
    kaki_halaman()


# ================================================================ main

topbar()
{"cek": halaman_cek, "detail": halaman_detail, "panduan": halaman_panduan, "tentang": halaman_tentang}[ss.view]()
