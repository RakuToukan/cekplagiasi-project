# Deteksi Plagiarisme Rabin-Karp (Streamlit)

## Alur

1. Unggah n dokumen (`.txt`, `.pdf`, `.docx`).
2. Semua dokumen digabung menjadi `corpus.txt`, satu dokumen per baris: `nama<TAB>teks`.
3. Preprocessing (Sastrawi): huruf kecil, hapus URL, angka, tanda baca, tokenisasi, hapus kata henti, potong imbuhan.
4. N-gram kata, lalu Rolling Hash `H = (c1*b^(k-1) + ... + ck) mod q` menjadi fingerprint.
5. Setiap dokumen bergantian menjadi X dan dibandingkan dengan semua dokumen lain (Rabin-Karp dengan verifikasi string).
6. Hasil: Jaccard Coefficient per pasangan, bagian cocok bernomor, dan laporan HTML.

## Tampilan

- **Cek Plagiasi**: formulir unggah dataset, panel langkah, dan tabel hasil (satu baris per dokumen uji).
- **Rincian Hasil**: skor similarity (Jaccard tertinggi), statistik, pratinjau dokumen dengan segmen bernomor
  (merah = identik, kuning = parafrase dekat), daftar bagian cocok beserta teks sumbernya, dan unduh laporan HTML.
- **Panduan** dan **Tentang Kami**.

Parameter backend tetap (n=2, b=3, q=10^9) dan tidak ditampilkan di UI. Ubah di konstanta
`N_GRAM`, `BASIS`, `MODULUS` di `app.py`.

## Menjalankan di komputer sendiri

```
pip install -r requirements.txt
streamlit run app.py
```

Klik **Coba dengan dokumen contoh** di formulir untuk mencoba dengan dokumen di `sample_docs/`.

## Deploy ke Streamlit Community Cloud

1. Push folder ini ke repository GitHub (wajib berisi `app.py`, `core/`, `requirements.txt`; `sample_docs/` opsional).
2. Buka https://share.streamlit.io, login dengan akun GitHub.
3. Pilih **Create app**, pilih repository dan branch, isi **Main file path** dengan `app.py`.
4. Klik **Deploy**. Paket di `requirements.txt` terpasang otomatis.

## Tes

```
pip install pytest
python -m pytest -q
```

`tests/test_similarity.py` memastikan hasilnya sama dengan notebook untuk dua dokumen contoh:
294 dan 242 fingerprint, irisan 72, gabungan 464, Jaccard 15.52%.

## Struktur

```
app.py              UI Streamlit (Cek Plagiasi, Rincian Hasil, Panduan, Tentang Kami)
core/extract.py     ekstraksi teks .txt/.pdf/.docx
core/merge.py       gabung n dokumen ke corpus.txt dan baca kembali
core/preprocess.py  preprocessing Sastrawi + pemetaan token ke kata asli (orig_idx)
core/ngram.py       n-gram kata
core/rolling_hash.py rolling hash dan fingerprint
core/rabin_karp.py  pencocokan hash + verifikasi string (spurious hit)
core/similarity.py  Jaccard Coefficient
core/compare.py     all-vs-all, tabel, matriks
core/highlight.py   highlight kosakata plagiat (fungsi dasar)
core/segmen.py      bagian cocok bernomor: deretan n-gram cocok, jenis identik/parafrase
core/laporan.py     HTML pratinjau dokumen, kartu segmen, laporan unduhan
.streamlit/config.toml  tema terang dan batas unggah 10 MB
tests/              unit test
sample_docs/        dokumen contoh (2 dokumen notebook + 1 dokumen berbeda topik)
sample_docs_plagiat/ 4 dokumen yang saling menjiplak (salin, parafrase, gabungan)
```

## Catatan

- **Similarity:** hanya Jaccard Coefficient, `J = |A ∩ B| / |A ∪ B|` pada himpunan fingerprint unik.
- **Modulus:** `10^9` seperti notebook. Collision hash disaring lewat verifikasi string (spurious hit).
- PDF hasil scan (gambar) tidak memiliki teks dan akan dilewati.
