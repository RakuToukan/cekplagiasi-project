"""Potongan HTML untuk halaman rincian hasil dan laporan yang bisa diunduh."""
import html
from typing import List

# Warna per nomor dokumen (berulang jika dokumen lebih dari 8): (warna tegas, warna lembut)
PALET_DOK = [
    ("#c2185b", "#fce4ec"), ("#1f5fd1", "#e3ecfc"), ("#0b7a52", "#dcf3e9"), ("#7b3fe4", "#eee6fd"),
    ("#c2410c", "#fdebdd"), ("#0e7490", "#ddf3f7"), ("#9d2bb3", "#f6e3fa"), ("#4d5bd6", "#e7e9fb"),
]


def warna_dok(nomor: int) -> tuple:
    return PALET_DOK[(nomor - 1) % len(PALET_DOK)]


def chip(nomor: int) -> str:
    """Penanda nomor dokumen, warnanya tetap per dokumen di seluruh halaman."""
    return f'<span class="seg-num" style="background:{warna_dok(nomor)[0]}">{nomor}</span>'

CSS_DOKUMEN = """
.dok { white-space: pre-line; font-size: 15.5px; line-height: 1.95; color: #1f2d3a; }
.seg-link, .seg-link:hover { color: inherit; text-decoration: none; }
.seg-mark { padding: 1px 2px; border-radius: 3px; color: inherit; border-bottom: 2px solid; }
.seg-num { display: inline-block; min-width: 18px; height: 18px; padding: 0 4px; margin-right: 4px;
  border-radius: 4px; color: #fff; font-size: 11px; font-weight: 700; line-height: 18px;
  text-align: center; vertical-align: 2px; }
.seg-num { background: #12304a; }
.src-item { padding: 12px 0; border-bottom: 1px solid #e3e9ef; }
.src-top { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.src-num { display: inline-block; min-width: 38px; padding: 2px 10px; border-radius: 999px; color: #fff;
  font-size: 12px; font-weight: 700; text-align: center; }
.src-row { display: flex; justify-content: space-between; gap: 12px; align-items: baseline; }
.src-row b { font-size: 14px; color: #16283a; word-break: break-word; }
.src-pct { font-size: 14px; font-weight: 700; color: #16283a; white-space: nowrap; }
.src-item small { display: block; color: #5b6b7b; font-size: 12px; margin-top: 2px; }
.legenda { display: flex; flex-wrap: wrap; align-items: center; gap: 8px 18px; font-size: 13px; color: #34475a; }
.legenda > b { color: #16283a; }
.legenda .leg { display: inline-flex; align-items: center; word-break: break-word; }
.legenda .leg i { font-style: normal; color: #5b6b7b; margin-left: 4px; }
.seg-card { border: 1px solid #e3e9ef; border-radius: 12px; padding: 14px 16px; margin-bottom: 12px;
  background: #fff; scroll-margin-top: 16px; }
.seg-card:target { border-color: #0e6fa3; box-shadow: 0 0 0 2px rgba(14,111,163,.18); }
.seg-head { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
.seg-pct { font-weight: 700; font-size: 13.5px; color: #16283a; white-space: nowrap; }
.seg-src { font-weight: 600; font-size: 13px; color: #34475a; margin: 10px 0 8px; word-break: break-word; }
.seg-src span { font-weight: 400; color: #5b6b7b; }
.seg-quote { border: 1px solid #e3e9ef; border-radius: 8px; padding: 10px 12px; background: #fbfcfd;
  font-size: 13px; line-height: 1.6; color: #34475a; }
.seg-quote b { display: block; font-size: 10.5px; letter-spacing: .04em; color: #5b6b7b; margin-bottom: 4px; }
"""


def _esc(teks: str) -> str:
    return html.escape(teks, quote=True)


def _nomor(s: dict) -> str:
    """Penanda nomor dokumen sumber kecocokan (lihat legenda)."""
    return "".join(chip(n) for n in s.get("nomor_dok") or [s["no"]])


def legenda(nama: List[str]) -> str:
    """Legenda nomor dokumen (urutan di dataset, mulai 1)."""
    item = "".join(
        f'<span class="leg">{chip(i + 1)}{_esc(n)}</span>' for i, n in enumerate(nama)
    )
    return f'<div class="legenda"><b>Nomor dokumen:</b>{item}</div>'


def daftar_sumber(sumber: List[dict]) -> str:
    """Daftar semua sumber yang cocok: nomor dokumen, nama, dan Jaccard similarity."""
    if not sumber:
        return '<p class="hint">Tidak ada dokumen lain yang cocok.</p>'
    baris = []
    for a in sumber:
        tegas, _ = warna_dok(a["nomor"])
        baris.append(
            f'<div class="src-item"><div class="src-top">'
            f'<span class="src-num" style="background:{tegas}">{a["nomor"]}</span></div>'
            f'<div class="src-row"><b>{_esc(a["nama"])}</b><span class="src-pct">{a["jaccard"]:.2f}%</span></div>'
            f'<small>Jaccard similarity &bull; {a["kata"]} kata ditandai</small></div>'
        )
    return "".join(baris)


def render_dokumen(teks: str, words: list, segmen: List[dict], tautan: bool = True, awalan_id: str = "") -> str:
    """Teks asli dengan highlight berwarna sesuai dokumen sumber utama, plus nomor semua sumbernya."""
    bagian = []
    pos = 0
    for s in sorted(segmen, key=lambda s: s["lo"]):
        awal, akhir = words[s["lo"]]["start"], words[s["hi"]]["end"]
        bagian.append(_esc(teks[pos:awal]))
        judul = _esc(f"Cocok dengan {', '.join([s['sumber']] + s['sumber_lain'])}")
        tegas, lembut = warna_dok(s["nomor_dok"][0])
        tanda = (
            f'<mark class="seg-mark" style="background:{lembut};border-color:{tegas}" title="{judul}">'
            f"{_nomor(s)}{_esc(teks[awal:akhir])}</mark>"
        )
        if tautan:
            tanda = f'<a class="seg-link" href="#seg-{awalan_id}{s["no"]}">{tanda}</a>'
        bagian.append(tanda)
        pos = akhir
    bagian.append(_esc(teks[pos:]))
    return f'<div class="dok">{"".join(bagian)}</div>'


def kartu_segmen(s: dict, batas_kutipan: int = 420, awalan_id: str = "") -> str:
    kutipan = s["teks_sumber"]
    if len(kutipan) > batas_kutipan:
        kutipan = kutipan[:batas_kutipan].rsplit(" ", 1)[0] + " ..."
    lain = (
        f'<div class="seg-src"><span>Juga cocok dengan: {_esc(", ".join(s["sumber_lain"]))}</span></div>'
        if s["sumber_lain"]
        else ""
    )
    return f"""<div class="seg-card" id="seg-{awalan_id}{s['no']}">
  <div class="seg-head"><span>{_nomor(s)}</span><span class="seg-pct">{s['kata']} kata</span></div>
  <div class="seg-src">Sumber: {_esc(s['sumber'])}</div>{lain}
  <div class="seg-quote"><b>TEKS PADA DATASET PEMBANDING:</b>&ldquo;{_esc(kutipan)}&rdquo;</div>
</div>"""


def laporan_html(judul: str, meta: List[tuple], ringkasan: List[tuple], skor: List[dict],
                 dokumen_html: str, segmen: List[dict], pembanding_html: str = "",
                 legenda_html: str = "", sumber_html: str = "") -> str:
    """Laporan mandiri untuk diunduh. Bisa dicetak ke PDF dari browser (Ctrl+P)."""
    baris_meta = "".join(f"<tr><th>{_esc(k)}</th><td>{_esc(v)}</td></tr>" for k, v in meta + ringkasan)
    baris_skor = "".join(
        f"<tr><td>{_esc(r['nama'])}</td><td>{r['sama']} / {r['gabungan']}</td><td>{r['jaccard']:.2f}%</td></tr>"
        for r in skor
    )
    kartu = "".join(kartu_segmen(s, batas_kutipan=2000) for s in sorted(segmen, key=lambda s: s["no"]))
    return f"""<!doctype html>
<html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(judul)}</title>
<style>
body {{ font-family: system-ui, -apple-system, "Segoe UI", sans-serif; color: #16283a; background: #fff;
  max-width: 900px; margin: 32px auto; padding: 0 16px; }}
h1 {{ font-size: 22px; margin-bottom: 4px; }} h2 {{ font-size: 16px; margin: 28px 0 10px; }}
table {{ border-collapse: collapse; width: 100%; font-size: 13.5px; }}
th, td {{ border: 1px solid #e3e9ef; padding: 6px 10px; text-align: left; vertical-align: top; }}
th {{ background: #f4f7fa; width: 34%; }}
.catatan {{ font-size: 12.5px; color: #5b6b7b; margin-top: 28px; }}
{CSS_DOKUMEN}
.seg-card {{ break-inside: avoid; }}
.kartu {{ border: 1px solid #e3e9ef; border-radius: 12px; margin-bottom: 18px; overflow: hidden; }}
.kepala {{ padding: 12px 16px; background: #f4f7fa; border-bottom: 1px solid #e3e9ef; display: flex;
  justify-content: space-between; gap: 12px; }}
.kepala small {{ display: block; color: #5b6b7b; font-size: 12.5px; margin-top: 2px; }}
.kepala .kanan {{ color: #5b6b7b; font-size: 12.5px; white-space: nowrap; }}
.badge {{ border-radius: 999px; padding: 2px 10px; font-size: 11.5px; font-weight: 700; margin-left: 6px; }}
.badge-biru {{ background: #e3eefc; color: #1f6fd1; }} .badge-hijau {{ background: #e3f6ea; color: #1f9d55; }}
.badge-kuning {{ background: #fff6cc; color: #b88a00; }} .badge-oranye {{ background: #ffead6; color: #e06b00; }}
.badge-merah {{ background: #fde7e7; color: #d93b3b; }}
.gulir {{ padding: 14px 18px; }}
</style></head><body>
<h1>{_esc(judul)}</h1>
<table>{baris_meta}</table>
<h2>Sumber terindikasi plagiat</h2>
{sumber_html}
<h2>Skor per dataset pembanding</h2>
<table><tr><th>Dokumen pembanding</th><th>Fingerprint sama / gabungan</th><th>Jaccard</th></tr>{baris_skor}</table>
<h2>Dokumen dengan bagian cocok</h2>
<p>Angka pada highlight adalah nomor dokumen yang cocok dengan bagian tersebut.</p>
{legenda_html}
{dokumen_html}
<h2>Rincian bagian cocok ({len(segmen)})</h2>
{kartu or "<p>Tidak ada bagian yang cocok.</p>"}
<h2>Semua dokumen di dataset</h2>
{pembanding_html}
<p class="catatan">Persentase similarity menunjukkan kemiripan teks, bukan penentu plagiasi secara mutlak.
Tinjau setiap segmen yang ditandai sebelum memberikan penilaian akhir.</p>
</body></html>"""
