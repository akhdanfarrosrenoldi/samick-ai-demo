# Business Requirements Document — Samick AI Demo

| Atribut | Nilai |
| --- | --- |
| Versi | 0.3 — arah produk, katalog dinamis, dan desain diperjelas |
| Tanggal | 28 Oktober 2026 |
| Target demonstrasi | Interview, Selasa 3 November 2026 |
| Status | Scope demo disepakati; kebutuhan perusahaan belum divalidasi |
| Cara menjalankan | Website dan layanan API di laptop presenter; internet diperlukan untuk API AI |

## 1. Ringkasan

Samick Guitar Guide adalah proyek website mandiri yang sedang dikembangkan dan dapat dicoba saat interview AI Engineer di PT Samick Indonesia. Katalog produk dikelola sendiri melalui CMS: admin memasukkan nama, spesifikasi, dan foto secara manual. Aplikasi tidak mengimpor URL, mengambil data otomatis, atau terhubung dengan website PT Samick Indonesia. Tiga penerapan AI yang saling terkait:

1. Asisten untuk calon pembeli yang menjawab pertanyaan dan merekomendasikan gitar dari katalog PT Samick Indonesia.
2. Asisten dokumen internal yang menjawab pertanyaan berdasarkan PDF laporan keuangan fiktif dengan rujukan halaman.
3. Analisis foto gitar dari unggahan atau satu foto yang diambil melalui webcam, lalu menampilkan kandidat produk dari katalog.

Gemini menjadi provider aktif untuk seluruh alur; OpenAI tetap opsional bila kredit API tersedia. Data awal produk disiapkan sebagai isian awal katalog milik aplikasi, lalu admin mengelolanya melalui CMS. Harga yang tersedia di sistem serta laporan keuangan dibuat sebagai **data simulasi**, bukan informasi resmi perusahaan. Halaman customer tidak memakai label “demo” berulang.

## 2. Latar belakang dan tujuan bisnis

Calon pembeli membutuhkan cara cepat untuk memahami perbedaan model gitar dan menemukan produk yang sesuai kebutuhan. Di sisi internal, karyawan dapat membutuhkan cara menelusuri isi dokumen tanpa membaca seluruh PDF secara manual. Foto produk memberi jalur interaksi tambahan ketika pengguna tidak mengetahui nama model gitar.

Tujuan demo:

- Menunjukkan percakapan AI yang didasarkan pada data produk, bukan jawaban bebas tanpa sumber.
- Menunjukkan alur unggah PDF, pencarian konteks (RAG), jawaban, dan rujukan halaman.
- Menunjukkan pemakaian model vision melalui foto atau webcam.
- Menunjukkan kemampuan memilih OpenAI atau Gemini dari CMS tanpa mengubah kode aplikasi.
- Menyampaikan batas ketepatan AI secara jujur, terutama untuk angka keuangan dan identifikasi model dari foto.

## 3. Pengguna dan akses

| Pengguna | Kebutuhan | Akses |
| --- | --- | --- |
| Calon pembeli | Bertanya tentang gitar, melihat rekomendasi, mengunggah/mengambil foto | Halaman publik tanpa login |
| Admin internal | Mengelola katalog produk, mengunggah PDF, bertanya tentang dokumen, memilih provider AI | CMS dengan satu akun login |

Data PDF internal dan percakapannya tidak boleh muncul pada halaman publik atau endpoint customer. Demo hanya membutuhkan satu akun admin; pengelolaan banyak peran dan departemen berada di luar scope.

## 4. Scope fungsional

### 4.1 Asisten produk untuk calon pembeli

**Alur:** pengunjung menulis kebutuhan → sistem mengambil produk aktif dari database → LLM menyusun jawaban dari kandidat tersebut → halaman menampilkan rekomendasi dan kartu produk milik website ini.

| ID | Kebutuhan |
| --- | --- |
| FR-01 | Halaman publik menyediakan asisten berbahasa Indonesia dalam bubble chat yang dapat dibuka dan ditutup; percakapan lanjutan membawa konteks terbatas. |
| FR-02 | Katalog awal berisi sekitar 8–12 model gitar sebagai isian awal database. Admin dapat memasukkan nama, kategori, spesifikasi, dan gambar secara manual melalui CMS tanpa URL sumber. |
| FR-03 | Harga simulasi boleh tersimpan sebagai data internal. Rancangan awal menyembunyikan harga sampai ada keputusan tampilan; bila kelak ditampilkan, UI harus menandainya sebagai **harga simulasi**, bukan harga resmi atau terkini. |
| FR-04 | Asisten menanyakan kebutuhan yang relevan bila pertanyaan masih umum, misalnya akustik/elektrik, tingkat pengalaman, bentuk bodi, atau kebutuhan elektronik. |
| FR-05 | Rekomendasi dibatasi pada produk aktif di database. Jawaban menampilkan alasan dari spesifikasi tersimpan serta kartu produk website ini. |
| FR-06 | Jika informasi stok, harga resmi, atau model tertentu tidak tersedia, asisten menyatakan keterbatasannya. Website tidak menyediakan checkout atau rute pembelian. |

### 4.2 Analisis foto dan webcam

**Alur:** pengunjung mengunggah foto atau menekan **Ambil Foto** → model vision mendeskripsikan ciri yang tampak → sistem mencocokkan ciri dengan katalog demo → halaman menampilkan kandidat produk.

| ID | Kebutuhan |
| --- | --- |
| FR-07 | Pengunjung dapat mengunggah satu gambar gitar (P0). Pengambilan satu foto lewat webcam setelah izin browser diberikan adalah penyempurnaan P1; alur unggah tetap tersedia bila kamera tidak dapat dipakai. |
| FR-08 | Analisis menjelaskan ciri yang dapat diamati, seperti kategori gitar, bentuk bodi, warna, dan komponen yang terlihat. |
| FR-09 | Hasil menampilkan maksimal tiga kandidat dari katalog, beserta alasan kecocokan dan spesifikasi yang berasal dari katalog. |
| FR-10 | Sistem boleh menyatakan **belum yakin/tidak ditemukan**. Sistem tidak menyajikan model spesifik sebagai fakta jika gambar tidak cukup jelas atau produk tidak ada di katalog. |
| FR-11 | Foto webcam diproses sebagai satu gambar; analisis video real-time dan penyimpanan foto pengguna tidak diperlukan untuk demo. |

Interpretasi fitur webcam ini adalah **identifikasi produk untuk calon pembeli**. Maksud asli pertanyaan HR tentang webcam belum diketahui. Deteksi cacat produksi, absensi, dan pemantauan keselamatan kerja adalah kemungkinan pembahasan lanjutan, bukan klaim kebutuhan PT Samick Indonesia atau fitur demo.

### 4.3 CMS dan asisten PDF internal

**Alur:** admin login → unggah PDF → sistem membaca teks per halaman dan mengindeks potongan teks → admin bertanya → sistem mengambil potongan relevan → LLM menjawab dengan rujukan halaman.

| ID | Kebutuhan |
| --- | --- |
| FR-12 | CMS menyediakan login untuk satu akun admin dan memisahkan data internal dari fitur publik. |
| FR-13 | Admin dapat mengunggah, melihat daftar, membuka, dan menghapus PDF demo. Hanya PDF yang diterima pada versi awal. |
| FR-14 | PDF contoh berupa laporan keuangan fiktif yang tampak realistis: periode, tabel pendapatan dan biaya, ringkasan, dan nomor halaman. Dokumen tetap memuat keterangan bahwa angka adalah data simulasi. |
| FR-15 | Sistem mengekstrak teks per halaman menggunakan PyMuPDF, memecahnya menjadi bagian yang dapat dicari, dan menyimpan hubungan setiap bagian dengan nomor halaman. |
| FR-16 | Asisten menjawab pertanyaan hanya dari **satu dokumen internal yang dipilih admin** dan menampilkan nama dokumen serta nomor halaman sumber. Pengguna dapat membuka preview halaman sumber. |
| FR-17 | Demo mendukung pembacaan nilai langsung serta satu contoh penjumlahan atau selisih dari dua pos yang berlabel jelas pada PDF contoh. Angka dan hasil operasi diverifikasi oleh program. Perhitungan di luar pola itu atau dengan operand yang tidak jelas dijawab sebagai belum dapat dipastikan. |
| FR-18 | PDF hasil scan tanpa lapisan teks diberi pesan yang jelas bahwa dokumen belum dapat diproses. OCR berada di luar scope demo awal. |

### 4.4 Pengaturan provider AI

| ID | Kebutuhan |
| --- | --- |
| FR-19 | CMS menyediakan pilihan OpenAI atau Gemini untuk chat produk, tanya PDF, dan analisis gambar. Perubahan berlaku untuk permintaan berikutnya. |
| FR-20 | Aplikasi menggunakan adapter provider agar format jawaban yang diterima frontend tetap konsisten. |
| FR-21 | Kunci API disimpan pada konfigurasi server, tidak ditampilkan atau dikirim ke browser. CMS hanya mengubah provider/model aktif yang telah dikonfigurasi. |
| FR-22 | Model embedding untuk indeks RAG tetap sama ketika provider jawaban diganti. Perubahan model embedding memerlukan pengindeksan ulang dan tidak menjadi fitur CMS demo. |
| FR-23 | Jika provider yang dipilih gagal atau tidak memiliki konfigurasi yang valid, aplikasi menampilkan pesan kesalahan yang dapat dipahami; admin dapat memilih provider lainnya. |

### 4.5 Katalog dinamis dan tampilan customer

| ID | Kebutuhan |
| --- | --- |
| FR-24 | Admin dapat menambah, mengedit, menonaktifkan, dan menghapus produk di CMS. Perubahan produk yang aktif berlaku pada pertanyaan AI berikutnya tanpa edit kode atau restart. |
| FR-25 | Data awal ditambahkan dari seed lokal tanpa URL. Startup aplikasi tidak boleh menimpa perubahan produk yang dibuat admin. |
| FR-26 | Form produk CMS tidak memakai kolom URL sumber. Website tidak menautkan atau menyinkronkan katalog dengan website PT Samick Indonesia. |
| FR-27 | Halaman customer mengikuti susunan beranda Samick: logo di tengah, navigasi horizontal, dan carousel tiga gambar; tidak memakai sidebar. Navigasi proyek hanya Beranda, Produk, dan Asisten yang benar-benar berfungsi. CMS diakses langsung melalui `/admin`, tanpa tombol publik. Rincian ada di [DESIGN.md](DESIGN.md). |

## 5. Batas scope

| Masuk demo | Di luar demo awal |
| --- | --- |
| Rekomendasi dari katalog gitar aktif yang dikelola CMS | Seluruh katalog otomatis, stok real-time, pembayaran, checkout |
| Harga simulasi yang diberi label | Harga resmi PT Samick Indonesia |
| Unggah satu foto (P0); snapshot webcam bila P1 selesai | Analisis video terus-menerus, absensi, quality control pabrik |
| PDF digital dengan teks yang dapat diekstrak | OCR PDF scan, Excel, data keuangan perusahaan yang sesungguhnya |
| RAG dokumen dengan sumber per halaman | Analitik lintas banyak dokumen/periode yang kompleks dan Text-to-SQL bebas |
| Satu akun admin lokal | Multi-role, multi-departemen, audit enterprise |
| Penyimpanan file di laptop | Object storage, sinkronisasi cloud, deployment produksi |

## 6. Rancangan solusi tingkat tinggi

| Lapisan | Teknologi | Tanggung jawab |
| --- | --- | --- |
| Frontend customer dan CMS | Next.js, React, TypeScript, CSS | Chat, katalog, upload, webcam, panel sumber, pengaturan admin |
| Backend AI dan dokumen | FastAPI, Python | Auth, API chat, upload, parsing PDF, retrieval, provider adapter, analisis gambar |
| Database | PostgreSQL + pgvector | Produk, harga simulasi, metadata dokumen, potongan teks, embedding, pengaturan provider |
| Parser PDF | PyMuPDF | Ekstraksi teks dan pemetaan halaman |
| Model | Gemini API; OpenAI API opsional | Gemini untuk embedding PDF dan jawaban demo; OpenAI dapat dipilih untuk jawaban/chat/foto bila kredit API tersedia |
| Penyimpanan file | Folder lokal backend | PDF yang diunggah dan aset demo yang diperlukan |

Redis, Celery, dan MinIO tidak diperlukan untuk scope demo ini. Pemrosesan beberapa PDF pendek dilakukan langsung oleh backend dengan indikator proses di UI. Foto webcam bersifat sementara. Jika aplikasi kelak dijalankan di banyak server atau memproses dokumen besar secara paralel, kebutuhan antrean dan object storage perlu dievaluasi ulang.

### 6.1 Pemisahan data

- **Katalog publik:** hanya data produk aktif yang dimasukkan ke database aplikasi serta harga simulasi bila diputuskan untuk ditampilkan.
- **Dokumen internal:** PDF fiktif, teks hasil ekstraksi, embedding, dan riwayat pertanyaan admin. Semua akses memerlukan autentikasi.
- Retrieval asisten customer tidak boleh mencari pada indeks dokumen internal.

### 6.2 RAG dokumen

PDF diunggah → teks diekstrak per halaman → teks dipecah menjadi bagian kecil dengan metadata halaman → embedding dibuat dengan `gemini-embedding-2` → bagian relevan dicari melalui pgvector → LLM terpilih menjawab menggunakan bagian tersebut → UI menampilkan sumber. Saat pertanyaan tidak didukung isi dokumen, jawaban harus menyatakan informasi tidak ditemukan. Pergantian provider jawaban tidak mengubah model embedding.

## 7. Kebutuhan nonfungsional

| ID | Kebutuhan |
| --- | --- |
| NFR-01 | Demo dapat dijalankan di laptop presenter pada `localhost`; akses internet diperlukan untuk OpenAI/Gemini. |
| NFR-02 | UI menampilkan status memproses untuk upload, chat, dan analisis gambar serta pesan yang jelas saat API gagal atau jaringan terputus. |
| NFR-03 | Kunci API dan dokumen internal tidak disajikan sebagai aset publik. Endpoint dokumen dan pengaturan memeriksa sesi admin. |
| NFR-04 | Jawaban memakai data produk dan dokumen yang benar-benar digunakan. Harga simulasi diberi label bila ditampilkan; dokumen internal tetap ditandai fiktif. |
| NFR-05 | Foto dan PDF diberi batas ukuran yang wajar untuk demo; jenis file diperiksa sebelum diproses. |
| NFR-06 | Proses demo memiliki data awal yang siap dipakai: katalog terkurasi, PDF fiktif, dan foto contoh sebagai cadangan jika tidak ada gitar fisik. |

## 8. Kriteria keberhasilan demo

1. Pengunjung menanyakan kebutuhan gitar dan menerima rekomendasi dari produk aktif di database, beserta spesifikasi dan alasan yang sesuai tanpa tautan eksternal atau harga rekaan.
2. Pengunjung mengunggah foto contoh; sistem menampilkan ciri visual dan kandidat produk tanpa memaksakan identifikasi pasti. Jika P1 selesai, satu foto dari webcam memberi hasil melalui alur yang sama.
3. Admin login, mengunggah PDF keuangan fiktif, lalu memperoleh jawaban atas pertanyaan isi dokumen dengan rujukan halaman yang dapat dibuka.
4. Pembacaan nilai langsung dan satu pertanyaan hitung dari dua pos berlabel pada PDF contoh menghasilkan angka yang sesuai dengan isi PDF dan perhitungan program.
5. Gemini dipakai untuk semua alur demo. Admin dapat mengganti provider jawaban ke OpenAI dari CMS bila kredit API tersedia, tanpa mengindeks ulang dokumen.
6. Pertanyaan di luar katalog/dokumen dan PDF scan tanpa teks ditangani dengan jawaban atau pesan keterbatasan yang jelas.
7. Pengunjung publik tidak dapat membuka PDF internal atau pengaturan provider.
8. Admin mengubah satu produk melalui CMS; katalog dan jawaban AI berikutnya memakai perubahan itu, dan perubahan bertahan setelah restart.

## 9. Risiko dan mitigasi

| Risiko | Dampak | Mitigasi demo |
| --- | --- | --- |
| Foto gitar kurang jelas atau model tampak mirip | Kandidat salah | Tampilkan ciri yang teramati, maksimal tiga kandidat, dan status ketidakpastian; sediakan foto contoh yang baik. |
| LLM salah membaca atau menghitung angka PDF | Jawaban keuangan keliru | PDF contoh dibuat ringkas; simpan sumber halaman; verifikasi perhitungan yang didukung melalui program. |
| Informasi produk yang dimasukkan admin tidak lengkap | Rekomendasi tidak sesuai | Periksa isian katalog sebelum interview dan batasi jawaban pada data yang tersedia. |
| Koneksi internet/API tidak tersedia saat interview | Fitur AI tidak dapat dipakai | Uji kedua provider sebelum berangkat; siapkan hotspot dan tangkapan layar hasil demo sebagai cadangan presentasi. |
| Istilah “webcam” dari HR merujuk use case lain | Demo kurang relevan dengan kebutuhan perusahaan | Jelaskan bahwa identifikasi produk adalah implementasi demo; tanyakan use case sebenarnya saat interview. |

## 10. Asumsi dan keputusan yang belum dikonfirmasi

- Kebutuhan perusahaan belum diperoleh langsung dari presdir. BRD ini mendefinisikan **prototipe interview**, bukan spesifikasi sistem produksi PT Samick Indonesia.
- Model gitar dan gambar dimasukkan sebagai data awal aplikasi; admin kemudian memeriksa dan memperbaruinya melalui CMS.
- Harga simulasi belum ditentukan angkanya; nilai final akan konsisten antara katalog dan jawaban AI.
- PDF demo akan dibuat baru dengan angka fiktif dan periode yang konsisten. Isinya tidak mewakili laporan keuangan PT Samick Indonesia.
- Produk, PDF, dan foto contoh yang tepat akan dipilih sebelum implementasi dan pengujian demo.
- Provider serta model embedding tetap akan dipilih saat implementasi sesuai ketersediaan API key dan hasil uji pada laptop.

## 11. Glosarium

| Istilah | Arti dalam demo |
| --- | --- |
| LLM | Model bahasa yang menyusun jawaban percakapan dari pertanyaan dan konteks. |
| RAG | Proses mencari data relevan dari katalog/dokumen sebelum LLM menjawab. |
| Embedding | Representasi numerik teks untuk mencari bagian dokumen yang mirip dengan pertanyaan. |
| Vision | Kemampuan model menganalisis gambar gitar. |
| OCR | Proses mengubah tulisan pada gambar/scan menjadi teks; belum termasuk demo awal. |
| CMS | Halaman admin buatan khusus untuk katalog produk, dokumen, dan pengaturan AI. |
