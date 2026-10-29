# Panduan agen — Samick AI Demo

## Konteks proyek

Repo ini menyiapkan **prototipe interview AI Engineer**, bukan sistem resmi PT Samick Indonesia. Targetnya website yang dapat dicoba di laptop presenter pada 3 November 2026. Pengguna berbahasa Indonesia; gunakan bahasa Indonesia untuk UI, data contoh, dan penjelasan demo kecuali diminta lain.

Sebelum mengubah aplikasi, baca tiga sumber kebutuhan berikut:

1. [docs/BRD.md](docs/BRD.md) — tujuan, fungsi, batas, dan kriteria keberhasilan.
2. [docs/PEP.md](docs/PEP.md) — urutan kerja, P0/P1, dan rencana verifikasi.
3. [docs/ITA.md](docs/ITA.md) — komponen, alur data, kontrak API, dan keputusan teknis.

Ikuti instruksi terbaru dari pengguna jika mengubah keputusan dalam dokumen. Selaraskan ketiga dokumen ketika keputusan produk atau arsitektur berubah. Jangan menganggap milestone selesai hanya karena tertulis dalam PEP; buktikan dari implementasi dan pengujian.

## Prioritas produk

**P0:**

- Chat customer yang merekomendasikan gitar hanya dari produk aktif pada katalog database.
- Katalog awal sekitar 8–12 gitar sebagai isian awal database; admin mengelola nama, spesifikasi, foto, dan status aktif lewat CMS. Tidak ada impor URL, crawler, sinkronisasi, atau tautan ke website PT Samick Indonesia.
- Harga yang tersimpan adalah simulasi dan tidak dikirim ke halaman customer. Bila ditampilkan kelak, beri label **harga simulasi**.
- CMS satu akun admin untuk unggah, daftar, buka, dan hapus PDF internal fiktif.
- PDF digital dibaca per halaman; RAG menjawab dari **satu dokumen yang dipilih** dan membuka preview halaman sumber yang tepat.
- Pembacaan nilai langsung dan satu contoh penjumlahan/selisih dua pos berlabel pada PDF contoh, dengan operand dan hasil diverifikasi oleh program.
- Analisis satu foto gitar yang diunggah, dengan maksimal tiga kandidat katalog dan pernyataan ketidakpastian bila perlu.
- Pilihan OpenAI/Gemini per fitur dari CMS; Gemini harus diuji untuk seluruh alur demo. OpenAI diuji setelah kredit API tersedia. Model embedding RAG tetap saat provider jawaban diganti.

**P1 setelah P0 stabil:** snapshot satu foto dari webcam, perapian panel sumber, dan polish visual. Alur unggah foto tetap berfungsi jika izin kamera ditolak.

**Di luar scope awal:** OCR PDF scan, analisis video real-time, absensi, quality control pabrik, checkout, stok atau harga resmi, data keuangan asli, multi-role, Redis, Celery, MinIO, dan deployment produksi.

## Arsitektur yang disepakati

- **Frontend/CMS:** Next.js, React, TypeScript, CSS biasa dengan token desain bersama.
- **Backend:** FastAPI dan Python; semua akses OpenAI/Gemini terjadi di backend.
- **Database:** PostgreSQL + pgvector untuk katalog, pengaturan, dokumen, chunk, dan embedding.
- **PDF:** PyMuPDF; pertahankan nomor halaman sejak ekstraksi. Chunk tidak boleh melintasi batas halaman.
- **Embedding PDF:** `gemini-embedding-2` dengan 1536 dimensi; OpenAI API tidak diperlukan untuk alur utama demo.
- **File:** PDF di folder lokal backend yang hanya dapat diakses melalui endpoint admin; gambar produk yang dikurasi tersedia secara lokal untuk demo.
- **Runtime lokal:** Docker Compose menjalankan frontend di `localhost:3000`, backend di `localhost:8000`, dan PostgreSQL di `localhost:5434`. Koneksi internet diperlukan untuk API AI.
- **Desain:** [docs/DESIGN.md](docs/DESIGN.md) mencatat tampilan customer yang diterapkan: header berlogo tengah, carousel, katalog tanpa sidebar, dan bubble chat. Navigasi publik hanya Beranda, Produk, Asisten; CMS dibuka langsung melalui `/admin`.

Repo `C:\Work\GITS\Projects\mono-ai-assistant` adalah referensi pola Aryaduta. Kerjakan aplikasi Samick di repo ini; jangan mengubah repo referensi kecuali pengguna secara khusus memintanya.

## Kebersihan repositori

- `testing-assets/` berisi PDF fiktif, foto, skrip generator, dan catatan uji **hanya untuk latihan lokal**. Folder ini diabaikan Git; jangan memindahkan salinannya kembali ke root repo atau aset publik kecuali aplikasi memang membutuhkannya saat runtime.
- Gambar di `frontend/public/products/` dan `frontend/public/brand/` dipakai UI dan tetap termasuk repo. Hindari salinan tambahan dari gambar yang sama di direktori yang ikut Git.
- Hapus CSS lama yang tertimpa, komponen tidak dipakai, pratinjau usang, dan dependensi khusus tes saat migrasi tampilan. Gunakan komponen bersama untuk produk katalog/rekomendasi dan token desain bersama.
- Jangan menambahkan output render, file unggahan, virtual environment, cache, atau secret ke Git. Jaga README utama berfokus pada menjalankan aplikasi, bukan langkah menghasilkan fixture uji.

## Aturan data dan jawaban AI

- Tandai seluruh laporan keuangan sebagai **data fiktif/simulasi**. Jangan menyajikan harga simulasi sebagai harga resmi; harga tetap tersembunyi pada halaman customer.
- Render nama model, spesifikasi, dan gambar dari produk aktif di database; jangan menerima nilai baru yang dibuat LLM. Form CMS produk tidak memerlukan URL sumber.
- Seed produk sekali; startup tidak boleh menimpa perubahan admin. Setelah CRUD produk selesai, buktikan perubahan di CMS memengaruhi pertanyaan AI berikutnya dan bertahan setelah restart.
- Pisahkan retrieval katalog publik dari indeks PDF internal. Endpoint publik tidak boleh dapat membaca PDF, teks, embedding, riwayat admin, atau pengaturan provider.
- Jawaban PDF harus bersandar pada potongan dokumen terpilih yang benar-benar dikirim ke model. Sitasi memuat dokumen dan halaman yang dapat dibuka lewat endpoint admin.
- Jika konteks, angka, atau gambar tidak cukup jelas, tampilkan keterbatasan. Jangan membuat sumber, nominal, model pasti, stok, atau kemampuan pembelian yang tidak ada di data.
- PDF scan tanpa teks diberi pesan OCR belum tersedia. Foto customer diproses untuk satu permintaan dan tidak disimpan permanen.
- Kunci API dan secret sesi berada di environment backend, tidak masuk Git atau bundle browser. CMS menyimpan pilihan provider/model, bukan API key.
- Password PostgreSQL lokal berada di root `.env` yang diabaikan Git; `backend/.env` juga diabaikan Git. Jangan menaruh nilai nyata di contoh konfigurasi atau dokumentasi.

## Cara bekerja dan verifikasi

- Mulai dari alur vertikal yang bisa dicoba di UI. Selesaikan P0 sebelum menambah fitur P1, kecuali pengguna mengubah prioritas.
- Pada awal implementasi, pastikan model API yang tersedia, model/dimensi embedding, koneksi PostgreSQL, dan akses katalog. Keputusan yang sudah diuji dicatat di dokumen terkait.
- Setelah menambah fitur, jalankan verifikasi yang relevan dari [PEP Bagian 7](docs/PEP.md#7-rencana-verifikasi-dan-kriteria-keluar): rekomendasi bersumber, PDF per halaman, perhitungan, vision jelas/ambigu, pergantian provider, kontrol akses, dan restart lokal.
- Uji dengan API sungguhan sebelum menyebut alur AI berfungsi. Jika API gagal, tunjukkan error; jangan mengganti respons live dengan jawaban contoh tanpa penanda.
- Jangan mengaku sudah menguji kamera, API key, database, atau layanan Docker sebelum benar-benar menjalankan pemeriksaannya.
- README memakai Docker Compose sebagai jalur startup utama. Jangan menambahkan perintah yang mensyaratkan Node.js/Python lokal untuk menjalankan aplikasi.

## Git, commit, dan publikasi

- Identitas Git untuk repo ini adalah **Akhdan Farros Renoldi `<renoldiakhdanfarros@gmail.com>`** sebagai **author dan committer**. Konfigurasi global komputer memakai email kantor; jangan biarkan repo ini mewarisi `@gits.id`.
- Sebelum membuat commit, periksa identitas efektif Git, termasuk kemungkinan override dari environment. Jika author atau committer bukan identitas di atas, perbaiki konfigurasi **lokal repo** sebelum melanjutkan. Setelah commit, periksa metadata commit.
- Gunakan **Conventional Commits** dengan format `type(scope): ringkasan`, misalnya `docs: add project execution plan`, `feat(catalog): add guitar recommendations`, atau `fix(rag): correct page citations`. Pilih `feat`, `fix`, `docs`, `refactor`, `test`, atau `chore` sesuai perubahan.
- Jangan menambahkan `Co-authored-by`, `Signed-off-by`, atau trailer lain yang mencantumkan Codex, AI, bot, akun kantor, atau orang lain. Jangan memakai opsi commit yang mengganti author/committer menjadi identitas lain.
- Repo boleh dipublikasikan sebagai **public**. Sebelum membuat remote atau melakukan push, periksa URL dan akun tujuan; gunakan hanya remote pribadi yang diminta pengguna. Jangan push ke `git.gits.id` atau remote/akun kantor. Jika tujuan pribadi belum diketahui, minta URL atau nama akun Git hosting yang tepat sebelum push.
- Instruksi ini mengatur commit/push **ketika diminta**; pembuatan `AGENTS.md` atau dokumen tidak dengan sendirinya meminta commit atau push.
