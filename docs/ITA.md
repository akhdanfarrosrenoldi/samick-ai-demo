# Implementation & Technical Architecture — Samick AI Demo

| Atribut | Nilai |
| --- | --- |
| Versi | 0.3 — Docker penuh dan arah katalog CMS dicatat |
| Tanggal | 28 Oktober 2026 |
| Acuan | [BRD.md](BRD.md), [PEP.md](PEP.md) |
| Sasaran | Demo lokal yang dapat dicoba pada interview, 3 November 2026 |
| Status | Database, auth, chat/vision Gemini, dan RAG PDF live telah diuji. Docker Compose frontend/backend/database berjalan. Halaman customer baru diterapkan; CMS produk tersedia; perubahan katalog, chat Gemini, kontrol akses, dan restart backend telah diuji. OpenAI API terhalang kredit habis. |

## 1. Tujuan dan batas arsitektur

Dokumen ini menerjemahkan kebutuhan BRD menjadi rancangan teknis untuk tiga alur: asisten produk gitar, tanya PDF keuangan fiktif berbasis RAG, dan pencocokan foto/webcam. CMS internal mengelola produk, dokumen, dan pilihan OpenAI/Gemini. Arah tampilan customer ada di [DESIGN.md](DESIGN.md).

Sistem dijalankan pada satu laptop. Frontend, backend, database, dan PDF berada di laptop tersebut; pemanggilan model OpenAI/Gemini memerlukan internet. Rancangan tidak mencakup deployment produksi, OCR PDF scan, streaming video, Redis, Celery, atau MinIO.

## 2. Keputusan arsitektur

| ID | Keputusan | Alasan |
| --- | --- | --- |
| AD-01 | Next.js + TypeScript untuk website customer dan CMS | Satu frontend untuk pengalaman publik dan admin. |
| AD-02 | FastAPI + Python untuk seluruh API dan proses AI | Mendukung parser PDF Python dan pemisahan logika AI dari UI. |
| AD-03 | PostgreSQL + pgvector untuk data serta embedding RAG | Data relasional dan pencarian kemiripan tersedia dalam satu database. |
| AD-04 | PyMuPDF mengekstrak teks **per halaman** | Nomor halaman disimpan sejak awal agar sumber jawaban dapat diverifikasi. |
| AD-05 | Provider jawaban/vision dapat diganti; model embedding tetap | Pergantian LLM tidak membuat vektor yang sudah tersimpan menjadi tidak kompatibel. |
| AD-06 | Katalog awal dimasukkan sekali; produk berikutnya dikelola manual di CMS tanpa URL sumber | Jawaban mengikuti katalog aktif di database. CRUD produk dan unggah foto tersedia pada endpoint admin. |
| AD-07 | PDF disimpan di folder lokal backend | Satu laptop dan sedikit file tidak membutuhkan object storage. |
| AD-08 | Upload PDF pendek diproses dalam permintaan API | Tidak membutuhkan antrean dan worker untuk scope demo. |
| AD-09 | Foto webcam P1 berupa satu snapshot dan tidak disimpan | Alur vision sama untuk unggah foto P0 dan webcam P1. |
| AD-10 | Docker Compose menjalankan Next.js, FastAPI, dan PostgreSQL/pgvector | Satu perintah startup setelah konfigurasi lokal; data DB dan PDF berada pada volume persisten. |

## 3. Gambaran sistem

```text
+--------------------------------------------------------+
| Browser di laptop                                       |
|  Next.js :3000                                          |
|  - Customer: katalog, chat, foto/webcam                 |
|  - CMS: login, katalog, PDF, tanya dokumen, provider    |
+--------------------------+-----------------------------+
                           |
                           | HTTP JSON / multipart
                           v
+--------------------------------------------------------+
| FastAPI :8000                                           |
|  Auth | Catalog | Product Chat | PDF Ingestion          |
|  RAG Retrieval | Finance QA | Vision | AI Settings      |
|  Provider adapter: OpenAI / Gemini                     |
+---------------+----------------+-----------------------+
                |                |                    |
                v                v                    v
       PostgreSQL :5434   Folder PDF lokal     OpenAI / Gemini
       + pgvector                              (internet)
```

### 3.1 Tanggung jawab komponen

| Komponen | Tanggung jawab | Tidak boleh melakukan |
| --- | --- | --- |
| Browser/Next.js | UI, izin webcam, snapshot gambar, render produk dan sumber | Menyimpan atau memanggil API AI dengan secret key dari browser |
| FastAPI | Validasi input, auth, retrieval, orkestrasi AI, verifikasi hasil, akses file internal | Mengembalikan PDF internal melalui endpoint publik |
| PostgreSQL | Katalog, harga simulasi, pengaturan, metadata PDF, teks/chunk, embedding | Menyimpan API key dalam bentuk terbaca lewat CMS |
| Folder backend | Menyimpan PDF yang diunggah dengan nama file internal | Mengekspos file lewat direktori `public` frontend |
| OpenAI/Gemini | Menyusun jawaban dan menganalisis gambar | Menjadi sumber harga, stok, atau angka keuangan yang tidak ada di data demo |

### 3.2 Batas data publik dan internal

- **Domain publik:** produk aktif, spesifikasi, dan gambar. Harga simulasi tersimpan internal tetapi tidak dikirim lewat API publik. Produk tidak menyimpan atau mengirim URL sumber.
- **Domain internal:** PDF fiktif, teks halaman, chunk, embedding, pertanyaan admin, dan pengaturan AI. Seluruh endpoint domain ini memeriksa sesi admin.
- Produk dan PDF memakai fungsi retrieval yang terpisah. Indeks dokumen internal tidak pernah dipakai untuk pertanyaan calon pembeli.

## 4. Alur fitur

### 4.1 Chat rekomendasi produk

```text
Pertanyaan customer
  --> normalisasi dan identifikasi kebutuhan
  --> pencarian/filter katalog di PostgreSQL
  --> kirim hanya kandidat relevan ke LLM terpilih
  --> validasi ID produk yang dikembalikan
  --> render jawaban + kartu produk dari database
```

- Katalog awal berisi sekitar 8–12 gitar sebagai isian awal database. Gambar disimpan lokal. Admin kemudian mengelola produk melalui form CMS tanpa memasukkan URL. Seed berjalan sekali dengan penanda `app_meta`; edit dan penghapusan admin tidak dikembalikan saat startup.
- Retrieval tahap awal memakai atribut terstruktur dan pencarian teks; dataset sekecil ini belum memerlukan embedding produk.
- LLM dapat menyusun penjelasan, tetapi **nama, spesifikasi, dan gambar** pada kartu produk selalu diambil dari database. ID produk hasil LLM harus cocok dengan kandidat yang diizinkan.
- Jika kandidat tidak ada, respons menyatakan katalog belum mempunyai produk yang cocok. Ketersediaan stok dan harga resmi tidak ditanyakan kepada LLM.
- Riwayat percakapan customer cukup berada pada sesi browser selama demo; backend membatasi jumlah pesan yang dikirim sebagai konteks.

### 4.2 Ingestion PDF dan RAG internal

```text
Admin unggah PDF
  --> cek sesi, jenis, ukuran, dan struktur file
  --> simpan sebagai nama UUID di folder backend
  --> PyMuPDF: ekstrak teks halaman 1..N
  --> bila tidak ada teks, tandai tidak didukung (OCR belum tersedia)
  --> potong teks tanpa melewati batas halaman
  --> buat embedding dengan satu model tetap
  --> simpan halaman, chunk, vektor, dan status di PostgreSQL
```

- Target PDF demo adalah dokumen digital pendek, sekitar 2–5 halaman. Batas awal usulan: maksimal **10 MB dan 20 halaman**; angka final dikunci setelah uji M0/M2.
- Setiap chunk memiliki `document_id`, `page_number`, `chunk_index`, `text`, `embedding_model`, dan `embedding`. Chunk tidak melintasi halaman sehingga satu sumber menunjuk halaman yang tepat.
- Status dokumen: `processing`, `ready`, atau `failed`. Jika ekstraksi/embedding gagal, CMS menampilkan sebab yang aman untuk ditampilkan. File dan data parsial dibersihkan atau dokumen ditandai gagal secara konsisten.
- PDF scan tanpa teks tidak dikirim ke retrieval. CMS menampilkan pesan bahwa OCR belum tersedia.

```text
Pertanyaan admin + document_id yang dipilih
  --> cek sesi dan dokumen ready
  --> embedding pertanyaan dengan model yang sama
  --> cari chunk terdekat dengan pgvector
  --> tambah pencarian teks untuk istilah/nominal persis
  --> susun konteks dengan label dokumen dan halaman
  --> LLM terpilih menjawab dari konteks
  --> validasi daftar sumber yang dirujuk
  --> tampilkan jawaban + tautan ke halaman PDF
```

- Pencarian vektor menggunakan kemiripan kosinus. Untuk korpus demo kecil, pencarian tepat (exact search) cukup; indeks ANN/HNSW ditambahkan hanya bila volume dokumen bertambah.
- Pencarian teks membantu pertanyaan dengan nama pos dan nominal yang perlu dicocokkan secara persis. Hanya chunk milik **satu dokumen yang dipilih** yang dapat masuk konteks.
- Jika retrieval tidak menemukan konteks yang memadai, backend mengembalikan jawaban **tidak ditemukan dalam dokumen** tanpa membuat sitasi palsu.
- Daftar sitasi dibentuk dari chunk yang benar-benar diberikan ke model. Respons model yang menyebut halaman di luar daftar tersebut tidak diterima sebagai sumber.

### 4.3 Pertanyaan angka keuangan

RAG digunakan untuk menemukan halaman/tabel yang relevan. Scope hitung P0 adalah **satu penjumlahan atau selisih dua pos berlabel jelas pada PDF contoh**. Backend meminta nilai, label pos, dan halaman sumber dalam format terstruktur, memeriksa kecocokan label serta nilai pada halaman tersebut, lalu menghitung dengan tipe desimal. Hasil hitung dan sumber diberikan kembali untuk penjelasan akhir.

Jika tabel tidak dapat dibaca atau operand tidak dapat diverifikasi, aplikasi menyatakan **tidak dapat memastikan perhitungan**. Data angka yang digunakan untuk membuat PDF fiktif disimpan terpisah sebagai jawaban acuan pengujian, bukan sebagai pengganti pembacaan PDF saat pengguna mengunggahnya.

### 4.4 Foto dan webcam

```text
Unggah gambar / webcam snapshot
  --> cek format dan ukuran
  --> model vision terpilih menghasilkan ciri visual terstruktur
  --> backend memilih kandidat dari katalog berdasarkan ciri
  --> model menyusun alasan yang dibatasi pada kandidat
  --> render maksimal tiga kartu produk dari database
```

- Format awal: JPEG, PNG, atau WebP; batas ukuran awal usulan **5 MB**.
- Webcam diakses browser hanya setelah izin pengguna; tombol **Ambil Foto** mengirim satu frame melalui endpoint yang sama dengan unggah gambar.
- Model vision diminta mengembalikan ciri yang *terlihat* dan tingkat kepastian kualitatif. Tidak ada klaim akurasi persentase yang belum diukur.
- Jika model tidak bisa membedakan model yang mirip atau gambar tidak menunjukkan gitar, respons menyatakan keterbatasan dan dapat meminta foto yang lebih jelas.
- Byte foto diproses untuk satu permintaan dan tidak disimpan permanen.

### 4.5 Pilihan provider

Backend memiliki kontrak `generate_text` dan `analyze_image` yang diimplementasikan adapter OpenAI dan Gemini. Respons keduanya dinormalisasi menjadi bentuk aplikasi yang sama: teks, ID kandidat/sumber yang valid, provider, model, dan status kesalahan.

CMS menyimpan pilihan provider/model untuk tiga fitur: `product_chat`, `finance_qa`, dan `vision`. Backend membaca pilihan terbaru pada setiap permintaan. Hanya kombinasi provider/model yang sudah dikonfigurasi dan diuji yang dapat dipilih. Jika provider gagal, pengguna melihat pesan kegagalan; perpindahan ke provider lain dilakukan melalui CMS, tanpa mengganti provider secara diam-diam.

Embedding RAG menggunakan **`gemini-embedding-2` dengan 1536 dimensi**. Identitas model dicatat pada setiap chunk. Pertanyaan memakai format *question answering* dan chunk memakai format dokumen sesuai panduan Gemini. Mengganti model embedding adalah operasi reindex terpisah di luar scope CMS demo.

## 5. Model data logis

| Entitas | Kolom inti | Catatan |
| --- | --- | --- |
| `products` | `id`, `name`, `category`, spesifikasi, `image`, `price`, `active` | Produk dikelola manual melalui CMS; harga simulasi disembunyikan pada customer dan status aktif menentukan retrieval. |
| Akun admin | `ADMIN_USERNAME`, `ADMIN_PASSWORD_HASH` di environment backend | Satu akun lokal; tidak ada tabel pengguna. |
| `app_meta` | `key`, `value` | Penanda seed katalog agar penghapusan produk tidak dibatalkan saat restart. |
| `documents` | `id`, `filename`, `storage_name`, `page_count`, `created_at` | Nama file penyimpanan dibuat oleh backend. |
| `document_pages` | `document_id`, `page_number`, `text` | Nomor halaman mulai dari satu mengikuti PDF. |
| `document_chunks` | `id`, `document_id`, `page_number`, `chunk_index`, `text`, `embedding_model`, `embedding` | `embedding` memakai `vector(d)` sesuai model yang dipilih. |
| `ai_settings` | `feature`, `provider`, `model` | Satu baris per fitur; tidak berisi API key. |

Penghapusan dokumen menghapus file lokal, halaman, chunk, dan embedding terkait. Percakapan PDF saat ini hanya berada di state browser; tidak disimpan dalam database.

## 6. Kontrak API awal

Semua rute berada di FastAPI pada `http://localhost:8000`. Nama dan bentuk final dapat disesuaikan saat implementasi, tetapi pemisahan akses berikut harus dipertahankan.

| Metode dan rute | Akses | Fungsi | Respons inti |
| --- | --- | --- | --- |
| `GET /api/health` | Publik | Status backend dan database | `status`, `database` |
| `GET /api/products` | Publik | Daftar produk aktif | Nama, kategori, spesifikasi, gambar |
| `GET /api/product-images/{filename}` | Publik | Menampilkan foto produk yang diunggah admin | Gambar |
| `POST /api/product-chat` | Publik | Rekomendasi berdasar katalog | `answer`, `products`, `provider` |
| `POST /api/vision/identify` | Publik | Analisis unggah/snapshot gambar | `observed_features`, `candidates`, `uncertain` |
| `POST /api/admin/login` | Publik | Mulai sesi admin | Sesi/cookie, identitas admin |
| `POST /api/admin/logout` | Admin | Akhiri sesi | Status |
| `GET /api/admin/documents` | Admin | Daftar dan status PDF | Dokumen dan status |
| `POST /api/admin/documents` | Admin | Unggah dan indeks PDF | ID dokumen, status, error jika ada |
| `GET /api/admin/documents/{id}/file` | Admin | Buka PDF asli | PDF inline |
| `GET /api/admin/documents/{id}/pages/{page}/preview` | Admin | Render halaman sumber yang tepat dengan PyMuPDF | Gambar halaman |
| `DELETE /api/admin/documents/{id}` | Admin | Hapus PDF dan data terkait | Status |
| `POST /api/admin/documents/{id}/questions` | Admin | Tanya dokumen terpilih | `answer`, `sources`, `calculation` bila ada |
| `GET/POST /api/admin/products` | Admin | Daftar dan tambah produk | Data produk dari form manual |
| `PUT/DELETE /api/admin/products/{id}` | Admin | Ubah/nonaktifkan/hapus produk | Data atau status terbaru |
| `POST /api/admin/product-images` | Admin | Unggah foto produk | Path gambar lokal |
| `GET /api/admin/ai-settings` | Admin | Baca pilihan provider | Pilihan per fitur |
| `PUT /api/admin/ai-settings/{feature}` | Admin | Ganti provider/model fitur | Pilihan aktif |

Rute produk admin telah diterapkan. Foto baru disimpan di folder data backend dan disajikan melalui endpoint gambar publik dengan nama file tervalidasi. Seed awal berjalan sekali, lalu perubahan admin menjadi sumber data. Komponen customer memakai satu tipe dan satu renderer kartu produk untuk katalog serta rekomendasi.

Objek sumber PDF minimal berisi `document_id`, `filename`, `page_number`, dan cuplikan teks. Saat sitasi diklik, UI membuka **preview halaman tertentu** melalui endpoint admin agar tidak bergantung pada dukungan fragmen `#page=N` di viewer browser; tombol terpisah dapat membuka PDF asli. Harga/spec produk dirender dari data backend, bukan dari teks bebas LLM.

## 7. Keamanan dan penanganan kegagalan

- **Autentikasi:** password admin di-hash; sesi memakai cookie `HttpOnly` dan `SameSite` yang sesuai. Endpoint perubahan data memeriksa sesi dan perlindungan CSRF yang dipilih saat implementasi.
- **Origin:** FastAPI hanya mengizinkan origin frontend lokal yang dikonfigurasi, dengan kredensial bila cookie dipakai; hindari wildcard untuk endpoint admin.
- **Secret:** `OPENAI_API_KEY`, `GEMINI_API_KEY`, serta secret sesi dibaca dari environment backend. File contoh konfigurasi hanya memuat nama variabel dan nilai placeholder.
- **Upload:** periksa MIME, ekstensi, signature file, ukuran, dan batas halaman. Nama simpan memakai UUID untuk mencegah path traversal dan benturan nama.
- **File internal:** hanya endpoint admin yang menyajikan PDF; respons memakai `Content-Type: application/pdf` dan tidak membocorkan path lokal.
- **Log:** catat ID permintaan, durasi, status provider, dan kode kesalahan. Jangan log API key, isi PDF, atau byte foto.
- **Timeout/API gagal:** tampilkan kesalahan yang bisa ditindaklanjuti; jangan mengganti jawaban live dengan teks demo tersimpan tanpa penanda.
- **Jawaban tanpa sumber:** bila konteks tidak cukup, jawab tidak ditemukan; tidak boleh membuat halaman sumber atau nominal baru.

## 8. Topologi lokal dan konfigurasi

Topologi Docker Compose yang disiapkan pada laptop (port host `5432` dan `5433` sudah dipakai proyek lain):

1. PostgreSQL/pgvector berjalan dalam container dengan volume persisten, tersedia pada `localhost:5434`.
2. FastAPI berjalan dalam container pada `localhost:8000`; folder `backend/data/` di-mount ke `/app/data` agar PDF yang sudah diunggah tetap tersedia.
3. Next.js berjalan dalam container pada `localhost:3000` menggunakan keluaran standalone.
4. Browser membuka `localhost:3000`. Kamera browser meminta izin saat fitur webcam dipakai.

Docker Compose telah membangun dan menjalankan frontend, backend, serta database pada port bawaan `3000/8000/5434`; halaman, gambar, health, katalog, dan chat Gemini merespons. **Gemini dengan model `gemini-3.5-flash` juga telah diuji untuk vision dan jawaban PDF. `gemini-embedding-2` menghasilkan vektor 1536 dimensi; PDF empat halaman berhasil diunggah dan pertanyaan penjumlahan menghasilkan Rp 12.300.000.000 dengan sumber halaman 2. OpenAI API mengembalikan `credit_balance_exhausted`.**

Contoh nama konfigurasi yang diperlukan, tanpa nilai rahasia:

```text
SAMICK_DB_PASSWORD (root .env; Compose membentuk DATABASE_URL untuk backend)
DATABASE_URL (diberikan Compose ke backend)
UPLOAD_DIR
OPENAI_API_KEY
GEMINI_API_KEY
EMBEDDING_MODEL
EMBEDDING_DIMENSION
ADMIN_USERNAME
ADMIN_PASSWORD_HASH
SESSION_SECRET
FRONTEND_ORIGIN
NEXT_PUBLIC_API_BASE_URL
```

Data PostgreSQL serta folder PDF dan foto produk bertahan setelah frontend/backend di-restart. Panduan menjalankan tiga container ada di README. Uji restart penuh dan login CMS dari container tetap termasuk pemeriksaan akhir sebelum interview.

## 9. Verifikasi teknis

| Pemeriksaan | Bukti yang diperlukan |
| --- | --- |
| Isolasi data | Endpoint publik tidak dapat membaca PDF, pesan admin, atau pengaturan AI. |
| Katalog | ID rekomendasi valid; spesifikasi sesuai baris database; API publik tidak mengirim harga simulasi. |
| PDF halaman | Pertanyaan yang hanya dapat dijawab dari halaman tertentu menampilkan nomor halaman tersebut. |
| RAG | Query tanpa konteks menghasilkan respons tidak ditemukan, tanpa sitasi rekaan. |
| Numerik | Penjumlahan/selisih yang didukung cocok dengan angka PDF dan hasil `Decimal`. |
| Provider | Gemini menerima permintaan pada semua fitur; OpenAI diuji setelah kredit API tersedia. Embedding yang tersimpan tetap berlaku saat provider jawaban diganti. |
| Vision | Foto jelas dan ambigu menghasilkan perilaku berbeda; kandidat selalu berasal dari katalog. |
| Webcam (P1) | Bila dikerjakan, izin diterima/ditolak tertangani; snapshot memakai endpoint vision yang sama. |
| Restart | Katalog, PDF, chunk, dan pengaturan tetap ada setelah layanan dihidupkan ulang. |

Kriteria penerimaan dan urutan uji pengguna tetap mengikuti [PEP Bagian 7](PEP.md#7-rencana-verifikasi-dan-kriteria-keluar) serta [BRD Bagian 8](BRD.md#8-kriteria-keberhasilan-demo).

## 10. Pertanyaan teknis yang dikunci pada M0/M2

- Model OpenAI dan Gemini yang tersedia bagi API key pengguna, termasuk dukungan input gambar.
- Provider/model embedding tetap dan dimensi vektornya sebelum migrasi `document_chunks` dibuat.
- Cara menjalankan PostgreSQL di laptop dan batas upload final berdasarkan uji PDF demo.
- Pilihan mekanisme sesi dan CSRF untuk frontend `localhost:3000` serta API `localhost:8000`.
- Struktur PDF fiktif dan cara membaca operand numerik yang dapat diverifikasi.

Keputusan tersebut tidak mengubah scope bisnis. Perubahan arsitektur yang menambah layanan baru harus dievaluasi terhadap target demo 3 November.
