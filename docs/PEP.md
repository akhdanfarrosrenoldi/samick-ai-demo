# Project Execution Plan — Samick AI Demo

| Atribut | Nilai |
| --- | --- |
| Versi | 0.2 — prioritas dan dependensi diselaraskan dengan BRD |
| Tanggal rencana | 28 Oktober 2026 |
| Dokumen acuan | [BRD.md](BRD.md) |
| Target | Demo langsung di laptop pada interview, Selasa 3 November 2026 |
| Status | Alur AI Gemini dan Docker Compose tiga layanan telah diuji. Halaman customer memakai carousel, katalog tanpa sidebar, dan bubble chat; CMS produk dinamis telah diterapkan; perubahan katalog aktif dan restart backend telah diuji. |

## 1. Tujuan pelaksanaan

Membangun website demo yang dapat dicoba langsung untuk menunjukkan tiga alur: rekomendasi gitar bagi calon pembeli, tanya jawab PDF keuangan fiktif berbasis RAG, dan pencocokan gitar dari foto/webcam. CMS internal menyediakan unggah dokumen dan pilihan provider OpenAI/Gemini.

Pelaksanaan mengutamakan **alur lengkap yang dapat diperagakan**: masukan pengguna, pemrosesan AI, hasil dengan sumber, dan penanganan keadaan gagal. Rincian fungsi dan batas produknya mengikuti [BRD](BRD.md).

## 2. Hasil akhir yang harus tersedia

1. Website customer berisi katalog yang dikelola sendiri, chat rekomendasi, dan analisis foto unggahan; snapshot webcam ditambahkan sebagai P1.
2. CMS dengan satu akun admin, kelola produk, daftar/unggah/buka/hapus PDF, chat dokumen, dan pengaturan provider.
3. Backend FastAPI yang menghubungkan UI, PostgreSQL/pgvector, PyMuPDF, OpenAI, dan Gemini.
4. Data contoh: sekitar 8–12 model gitar yang dimasukkan ke katalog lokal, harga simulasi internal, PDF keuangan fiktif, dan beberapa foto contoh.
5. Panduan menjalankan aplikasi di laptop dan skenario presentasi yang sudah diuji.
6. Hasil verifikasi untuk alur inti, termasuk sumber jawaban, hitungan angka, pergantian provider, serta pemisahan akses publik dan internal.

## 3. Strategi delivery

### 3.1 Prinsip prioritas

- **P0 — harus berjalan saat interview:** chat dari produk aktif di database, katalog yang dapat dikelola admin, unggah dan tanya satu PDF terpilih dengan sumber, satu hitungan terverifikasi, analisis foto, login CMS, serta Gemini teruji pada seluruh alur. Opsi OpenAI tetap ada setelah kredit API tersedia.
- **P1 — penyempurnaan demo:** pengambilan foto melalui webcam dan perapian panel sumber. Desain customer yang disetujui merupakan bagian P0.
- **Di luar rencana:** OCR PDF scan, video real-time, absensi, inspeksi cacat pabrik, checkout, stok aktual, Redis, Celery, dan MinIO.

Jika jadwal tertekan, selesaikan alur P0 sampai dapat diuji dari UI sebelum menambah P1. Foto unggahan tetap menyediakan jalur demonstrasi vision bila webcam bermasalah.

### 3.2 Rancangan komponen

| Komponen | Pilihan | Catatan pelaksanaan |
| --- | --- | --- |
| Frontend dan CMS | Next.js, TypeScript, CSS | Halaman publik dan admin dalam satu aplikasi frontend. |
| Backend | FastAPI, Python | Endpoint terpisah untuk produk, chat, dokumen, vision, dan pengaturan AI. |
| Data | PostgreSQL + pgvector | Katalog, harga simulasi, dokumen, chunk, embedding, dan provider aktif. |
| PDF | PyMuPDF | Ekstraksi teks **per halaman** agar sitasi tetap akurat. |
| AI | OpenAI API dan Gemini API | Adapter dengan hasil terstandardisasi; kunci berada di server. |
| File | Folder lokal backend | PDF internal tidak ditempatkan di direktori aset publik. |

`gemini-embedding-2` dipakai untuk seluruh indeks dokumen dengan 1536 dimensi. Pergantian OpenAI/Gemini dalam CMS mengubah model yang menjawab atau menganalisis gambar, tanpa mengganti ruang embedding dan tanpa perlu mengindeks ulang. OpenAI baru dapat diuji setelah kredit API tersedia.

## 4. Rencana kerja dan milestone

Tanggal berikut adalah **target kerja usulan** untuk mencapai demo 3 November. Urutan dependensi lebih penting daripada pembagian jam per hari.

| Milestone | Target | Pekerjaan utama | Bukti selesai |
| --- | --- | --- | --- |
| M0 — data dan fondasi | 28–29 Okt | Pilih model katalog; siapkan harga simulasi dan foto; buat kerangka Next.js/FastAPI; hidupkan PostgreSQL/pgvector; periksa kedua API key. | Frontend, backend, dan database dapat dijalankan di laptop; data katalog awal tampil. |
| M1 — asisten produk | 29–30 Okt | Simpan katalog; bangun retrieval produk, adapter OpenAI/Gemini, dan chat customer. | Pertanyaan kebutuhan gitar menghasilkan rekomendasi yang hanya merujuk katalog. |
| M2 — PDF internal dan RAG | 30–31 Okt | Buat PDF fiktif; bangun login admin, upload, ekstraksi per halaman, chunking, embedding, retrieval, dan jawaban dengan sumber. | Admin dapat bertanya isi PDF dan membuka halaman yang dirujuk. |
| M3 — vision dan pengaturan | 1 Nov | Bangun unggah foto, pencocokan kandidat, dan pilihan provider per fitur di CMS; tambah snapshot webcam setelah P0 stabil. | Foto contoh menghasilkan kandidat; perubahan provider berlaku pada permintaan berikutnya. |
| M4 — verifikasi dan latihan | 2 Nov | Uji alur end-to-end, akses internal, jawaban angka, dua provider, kamera bila P1 selesai, dan kondisi jaringan gagal; rapikan UI dan siapkan cadangan presentasi. | Seluruh skenario P0 pada Bagian 7 lulus dan urutan demo berhasil dilakukan dari awal sampai akhir. |
| Demo | 3 Nov | Jalankan aplikasi di laptop dan presentasikan skenario Bagian 8. | Seluruh alur inti dapat diperagakan langsung. |

## 5. Paket pekerjaan

| ID | Paket kerja | Hasil | Acuan BRD | Dependensi |
| --- | --- | --- | --- | --- |
| W-01 | Katalog dan data demo | 8–12 produk, spesifikasi bersumber, gambar, harga simulasi | FR-02, FR-03 | Halaman produk publik dapat diakses |
| W-02 | Fondasi aplikasi | Next.js, FastAPI, PostgreSQL/pgvector, konfigurasi lokal | NFR-01 | Runtime dan database siap |
| W-03 | Provider adapter | Pemanggilan OpenAI/Gemini dengan kontrak respons seragam | FR-19–FR-23 | API key valid |
| W-04 | Chat produk | Retrieval katalog aktif dan rekomendasi dengan kartu produk internal | FR-01, FR-04–FR-06 | W-01, W-03 |
| W-05 | Dokumen fiktif | PDF realistis dengan angka konsisten dan label simulasi | FR-14 | Struktur tabel keuangan ditetapkan |
| W-06 | CMS dan akses | Login admin, halaman dokumen, pengaturan provider | FR-12, FR-13, FR-19 | W-02 |
| W-07 | Ingestion PDF | File lokal, ekstraksi halaman, chunk, embedding, metadata | FR-15, FR-18 | W-02, W-05 |
| W-08 | Chat dokumen | Retrieval pgvector, jawaban dengan halaman sumber, verifikasi hitungan sederhana | FR-16, FR-17 | W-03, W-07 |
| W-09 | Analisis gambar | Unggah foto, vision, kandidat produk, penanganan ketidakpastian | FR-07–FR-10 | W-01, W-03 |
| W-10 | Webcam | Izin kamera, snapshot satu foto, kirim ke alur W-09 | FR-07, FR-11 | W-09 |
| W-11 | Uji dan latihan demo | Hasil uji, panduan run lokal, foto cadangan, naskah demo singkat | Bagian 8 BRD, NFR-01–NFR-06 | W-01–W-09; W-10 hanya jika P1 selesai |
| W-12 | CMS katalog dinamis | CRUD produk manual, status aktif, seed sekali, uji setelah restart | FR-24–FR-26 | W-01, W-06 |
| W-13 | Desain customer | Carousel beranda, tiga menu yang berfungsi, katalog tanpa sidebar, bubble chat, hapus CSS/markup lama | FR-27, [DESIGN.md](DESIGN.md) | Koreksi visual pengguna |

## 6. Data, integrasi, dan keamanan demo

### 6.1 Data produk

- Siapkan katalog awal sebagai isian database; admin dapat memasukkan dan mengubah nama model, spesifikasi, kategori, foto, serta status aktif secara manual. Tidak ada kolom URL, impor otomatis, crawler, atau sinkronisasi dengan website lain.
- Harga simulasi dapat disimpan, tetapi tidak ditampilkan pada rancangan customer awal. Bila kelak ditampilkan, wajib diberi label **harga simulasi**. AI tidak boleh membuat nominal baru.
- Seed katalog hanya saat data awal belum ada. Perubahan admin pada produk aktif harus langsung dipakai chat dan tetap ada setelah restart.
- Stok, diskon, dan kemampuan membeli secara online tidak tersedia.

### 6.2 Data PDF

- Buat PDF keuangan baru dengan identitas demo yang realistis, periode yang jelas, tabel angka, total, dan nomor halaman. Sertakan penanda **data fiktif/simulasi**.
- Simpan data angka sumber yang digunakan membuat PDF sebagai jawaban acuan pengujian. Saat aplikasi menjawab, dua operand harus tetap diambil dari PDF terpilih dan diverifikasi sebelum dihitung.
- Batasi unggahan ke PDF berukuran wajar. PDF tanpa teks yang dapat diekstrak mendapat pesan bahwa OCR belum didukung.
- Simpan file pada folder backend dan sajikan melalui endpoint yang memeriksa sesi admin; simpan metadata, teks, dan embedding di database.

### 6.3 API dan provider

- Simpan kunci OpenAI dan Gemini dalam konfigurasi server yang tidak masuk repositori.
- CMS menyimpan pilihan provider/model aktif, bukan nilai kunci API.
- Uji Gemini untuk chat produk, tanya PDF, dan vision. Uji OpenAI setelah kredit API tersedia. Jika provider gagal, tampilkan kesalahan jelas; jangan diam-diam menampilkan respons contoh sebagai jawaban live.

### 6.4 Batas akses

- Endpoint customer hanya boleh membaca katalog publik.
- Endpoint PDF, file internal, percakapan dokumen, dan pengaturan provider hanya dapat diakses setelah login admin.
- Foto customer tidak disimpan permanen; cukup diproses untuk satu permintaan.

## 7. Rencana verifikasi dan kriteria keluar

| Area | Skenario minimum | Hasil yang diharapkan |
| --- | --- | --- |
| Chat produk | Tanya gitar akustik pemula; tanya model di luar katalog | Rekomendasi berasal dari katalog dengan sumber; pertanyaan di luar data dijawab dengan batas yang jelas. |
| Harga | Tanyakan harga produk yang ada | Asisten menjelaskan harga tidak tersedia di halaman customer; tidak membuat nominal. |
| PDF | Unggah PDF contoh; tanya ringkasan dan satu angka pada halaman tertentu | Jawaban sesuai dokumen dan rujukan membuka halaman yang benar. |
| Perhitungan | Tanya satu penjumlahan/selisih dua pos berlabel jelas pada PDF contoh | Kedua operand ditemukan pada PDF terpilih; hasil sesuai perhitungan program. |
| PDF scan | Unggah contoh PDF tanpa teks | Proses dihentikan dengan pesan OCR belum tersedia, tanpa jawaban rekaan. |
| Vision | Unggah foto contoh berlabel dan foto ambigu | Produk yang benar masuk maksimal tiga kandidat untuk foto contoh yang jelas; foto ambigu menghasilkan pernyataan ketidakpastian. |
| Webcam (P1) | Izinkan kamera, ambil foto; tolak izin kamera | Jika P1 selesai, foto masuk ke alur vision; penolakan izin mendapat pesan dan opsi unggah foto tetap tersedia. |
| Provider | Jalankan permintaan dengan Gemini; uji OpenAI bila kredit API tersedia | Provider yang aktif benar-benar dipakai dan tidak menyebabkan reindex dokumen. |
| Akses | Buka URL/API dokumen tanpa login | Akses ditolak; file internal tidak dapat diambil dari aset publik. |
| Operasional | Restart layanan dan ulangi alur demo | Katalog, PDF, dan pengaturan tetap tersedia; perintah menjalankan terdokumentasi. |

**Kriteria keluar M4:** seluruh skenario P0 berhasil dari UI di laptop presenter. Kegagalan P1 webcam dapat ditangani dengan unggah foto; kegagalan P0 harus diperbaiki sebelum demo.

## 8. Urutan demonstrasi interview

1. Buka halaman customer dan tanyakan kebutuhan gitar melalui bubble chat. Tunjukkan alasan rekomendasi dan produk dari katalog database tanpa harga atau tautan eksternal.
2. Unggah foto gitar contoh. Jika kamera dan situasi ruangan mendukung, ambil satu foto dengan webcam. Tunjukkan kandidat serta batas keyakinan AI.
3. Masuk CMS, unggah PDF keuangan fiktif, lalu ajukan pertanyaan ringkasan dan pertanyaan angka. Buka halaman sumber jawaban.
4. Tunjukkan pengaturan provider di CMS. Ulangi satu pertanyaan dengan OpenAI hanya bila kredit API sudah tersedia.
5. Tutup dengan penjelasan singkat: kebutuhan webcam yang sebenarnya dan penggunaan data perusahaan harus divalidasi sebelum sistem produksi dirancang.

Siapkan hotspot, foto contoh lokal, dan tangkapan layar hasil uji sebagai cadangan bila koneksi/API bermasalah. Tangkapan layar harus dijelaskan sebagai **hasil uji sebelumnya**, bukan respons AI yang sedang berjalan.

## 9. Risiko pelaksanaan dan respons

| Risiko | Tanda awal | Respons |
| --- | --- | --- |
| Waktu pengembangan tidak cukup | Alur inti belum tersambung dari UI | Selesaikan P0 secara berurutan; gunakan unggah foto sebagai jalur vision sebelum webcam. |
| Akun/API model bermasalah | Permintaan sederhana gagal di M0 | Uji kedua API key sejak awal dan pilih model yang benar-benar tersedia. |
| Hasil RAG mengutip halaman salah | Jawaban benar tetapi sumber meleset | Simpan nomor halaman saat ekstraksi, lalu uji dengan pertanyaan yang jawabannya hanya ada di satu halaman. |
| Model vision terlalu yakin | Model spesifik disebut dari foto ambigu | Batasi ke kandidat katalog dan minta alasan berdasarkan ciri yang tampak. |
| Internet tidak stabil | Latensi tinggi atau timeout saat latihan | Uji hotspot dan siapkan bukti hasil uji sebagai cadangan presentasi. |
| Layanan lokal sulit dijalankan ulang | Restart menghilangkan data atau konfigurasi | Gunakan penyimpanan persisten dan latihan startup penuh pada M4. |

## 10. Keputusan yang perlu dikunci saat implementasi

- Daftar final 8–12 produk, gambar, dan nilai harga simulasi.
- Isi dan periode PDF fiktif serta jawaban acuan untuk pertanyaan angka.
- Model OpenAI, Gemini, dan satu model embedding yang tersedia pada API key pengguna.
- Batas ukuran file dan durasi timeout berdasarkan uji di laptop.
- Cara menjalankan tiga komponen lokal: langsung di host atau melalui Docker Compose.

Keputusan ini dicatat dan diuji sebelum M4. Perubahan yang menambah use case baru setelah M2 harus dinilai terhadap waktu yang tersisa menuju interview.
