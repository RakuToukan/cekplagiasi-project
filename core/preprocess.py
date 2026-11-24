"""FR-5: preprocessing teks bahasa Indonesia.

Diadaptasi dari kelas `preprosesingteks` di notebook rabin_karp_simialirity.ipynb:
huruf kecil, hapus URL, angka, dan tanda baca, tokenisasi, hapus kata henti
(Sastrawi), lalu potong imbuhan (Sastrawi).

Perbedaan dari notebook: pembersihan dilakukan per kata asli, sehingga setiap token
menyimpan `orig_idx` (indeks kata asli di teks). Hasil token tetap sama dengan
notebook, tetapi n-gram yang cocok bisa di-highlight pada teks asli (FR-14).
"""
import re
import string
from typing import Dict, List, Optional

from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory

_URL_RE = re.compile(r"https?://\S+|www\.\S+")
_ANGKA_RE = re.compile(r"\d+")
_KATA_RE = re.compile(r"\S+")
_TANDA_BACA = str.maketrans("", "", string.punctuation)


class PreprosesingTeks:
    def __init__(self, kata_henti: Optional[List[str]] = None):
        self._stemmer = StemmerFactory().create_stemmer()
        daftar = list(StopWordRemoverFactory().get_stop_words())
        if kata_henti:
            daftar.extend(kata_henti)
        self.daftar_kata_henti = set(daftar)
        self._cache_imbuhan: Dict[str, List[str]] = {}

    @staticmethod
    def bersihkan_kata(kata: str) -> str:
        kata = kata.lower()
        kata = _URL_RE.sub("", kata)
        kata = _ANGKA_RE.sub("", kata)
        return kata.translate(_TANDA_BACA).strip()

    def potong_imbuhan(self, kata: str) -> List[str]:
        # Sastrawi mengganti karakter non-alfanumerik dengan spasi sebelum stemming,
        # jadi satu kata bisa menjadi nol, satu, atau beberapa kata dasar.
        if kata not in self._cache_imbuhan:
            self._cache_imbuhan[kata] = self._stemmer.stem(kata).split()
        return self._cache_imbuhan[kata]

    def proses(
        self,
        teks: str,
        gunakan_kata_henti: bool = True,
        gunakan_pemotong_imbuhan: bool = True,
    ) -> dict:
        """Kembalikan kata asli beserta posisinya dan token hasil preprocessing.

        words  : [{"raw", "start", "end"}]  indeks list = orig_idx
        tokens : [{"tok", "orig_idx"}]
        """
        words = []
        token_bersih = []  # (token, orig_idx)
        for m in _KATA_RE.finditer(teks):
            idx = len(words)
            words.append({"raw": m.group(), "start": m.start(), "end": m.end()})
            bersih = self.bersihkan_kata(m.group())
            if bersih:
                token_bersih.append((bersih, idx))

        if gunakan_kata_henti:
            token_tanpa_henti = [(t, i) for t, i in token_bersih if t not in self.daftar_kata_henti]
        else:
            token_tanpa_henti = token_bersih

        if gunakan_pemotong_imbuhan:
            token_akhir = [(d, i) for t, i in token_tanpa_henti for d in self.potong_imbuhan(t)]
        else:
            token_akhir = token_tanpa_henti

        return {
            "words": words,
            "token_bersih": [t for t, _ in token_bersih],
            "token_tanpa_kata_henti": [t for t, _ in token_tanpa_henti],
            "tokens": [{"tok": t, "orig_idx": i} for t, i in token_akhir],
        }
