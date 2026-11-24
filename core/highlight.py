"""FR-14: highlight kosakata teridentifikasi plagiat pada teks asli.

Setiap n-gram cocok dipetakan ke rentang kata asli, dari kata pertama sampai kata
terakhir penyusunnya. Kata henti di antaranya ikut ter-highlight agar frasa
terbaca utuh. Kata berurutan dengan warna sama digabung menjadi satu <mark>.
"""
import html
from typing import Dict, List, Optional, Sequence, Set, Tuple

# Warna latar terang dengan teks gelap: terbaca di tema terang maupun gelap.
WARNA_INTENSITAS = ("#fff3b0", "#ffe066", "#ffc300")
WARNA_SUMBER = (
    "#ffe066", "#a5d8ff", "#b2f2bb", "#ffc9c9",
    "#d0bfff", "#ffd8a8", "#99e9f2", "#fcc2d7",
)
WARNA_LAINNYA = "#dee2e6"

Label = Optional[Tuple[str, Set[str]]]  # (warna, isi tooltip) atau None


def cakupan_kata(n_kata: int, fp: dict, idx_ngram: Sequence[int]) -> List[Set[str]]:
    """Untuk setiap kata asli: himpunan n-gram cocok yang menutupinya."""
    cakupan: List[Set[str]] = [set() for _ in range(n_kata)]
    for i in idx_ngram:
        ng = fp["ngrams"][i]
        for w in range(min(ng["orig_idx"]), max(ng["orig_idx"]) + 1):
            cakupan[w].add(ng["gram"])
    return cakupan


def label_pasangan(cakupan: List[Set[str]], intensitas: bool = False) -> List[Label]:
    label: List[Label] = []
    for grams in cakupan:
        if not grams:
            label.append(None)
            continue
        level = min(len(grams), len(WARNA_INTENSITAS)) - 1 if intensitas else 1
        label.append((WARNA_INTENSITAS[level], set(grams)))
    return label


def label_gabungan(
    cakupan_per_sumber: Dict[str, List[Set[str]]], skor: Dict[str, float]
) -> Tuple[List[Label], Dict[str, str]]:
    """Highlight X terhadap semua pembanding. Satu kata yang cocok dengan beberapa
    pembanding diberi warna pembanding dengan skor tertinggi."""
    urutan = sorted(cakupan_per_sumber, key=lambda s: -skor[s])
    warna = {s: (WARNA_SUMBER[k] if k < len(WARNA_SUMBER) else WARNA_LAINNYA) for k, s in enumerate(urutan)}
    n_kata = len(next(iter(cakupan_per_sumber.values()), []))
    label: List[Label] = []
    for w in range(n_kata):
        sumber = [s for s in urutan if cakupan_per_sumber[s][w]]
        label.append((warna[sumber[0]], set(sumber)) if sumber else None)
    return label, warna


def render(teks: str, words: List[dict], label: List[Label], tinggi: int = 420) -> str:
    bagian = []
    pos = 0
    i = 0
    while i < len(words):
        if label[i] is None:
            i += 1
            continue
        warna, tips = label[i][0], set(label[i][1])
        j = i
        while j + 1 < len(words) and label[j + 1] is not None and label[j + 1][0] == warna:
            j += 1
            tips |= label[j][1]
        awal, akhir = words[i]["start"], words[j]["end"]
        bagian.append(html.escape(teks[pos:awal]))
        judul = html.escape(" | ".join(sorted(tips)), quote=True)
        bagian.append(
            f'<mark style="background:{warna};color:#111;padding:0 2px;border-radius:3px" '
            f'title="{judul}">{html.escape(teks[awal:akhir])}</mark>'
        )
        pos = akhir
        i = j + 1
    bagian.append(html.escape(teks[pos:]))
    return (
        f'<div style="max-height:{tinggi}px;overflow-y:auto;border:1px solid rgba(128,128,128,.4);'
        f'border-radius:6px;padding:12px 14px;line-height:1.8;font-size:15px">{"".join(bagian)}</div>'
    )


def statistik(label: List[Label]) -> Tuple[int, int, float]:
    total = len(label)
    tertandai = sum(1 for lb in label if lb is not None)
    return tertandai, total, (100 * tertandai / total if total else 0.0)


def legenda(warna: Dict[str, str]) -> str:
    item = "".join(
        f'<span style="display:inline-block;margin:0 12px 6px 0">'
        f'<span style="background:{w};display:inline-block;width:12px;height:12px;'
        f'border-radius:2px;margin-right:6px;vertical-align:middle"></span>{html.escape(s)}</span>'
        for s, w in warna.items()
    )
    return f"<div>{item}</div>"


def halaman_html(judul: str, isi: str) -> str:
    """File HTML mandiri untuk diunduh dan dilampirkan di laporan."""
    return f"""<!doctype html>
<html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(judul)}</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 24px; color: #1a1a1a; background: #fff; }}
.kolom {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
@media (max-width: 760px) {{ .kolom {{ grid-template-columns: 1fr; }} }}
h1 {{ font-size: 20px; }} h2 {{ font-size: 16px; margin-bottom: 4px; }}
table {{ border-collapse: collapse; margin-bottom: 16px; }}
td, th {{ border: 1px solid #ccc; padding: 4px 10px; text-align: left; }}
</style></head><body>
<h1>{html.escape(judul)}</h1>
{isi}
</body></html>"""
