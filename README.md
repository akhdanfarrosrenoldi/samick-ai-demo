# Samick Guitar Guide

Proyek website independen untuk membantu calon pembeli memilih gitar dari katalog yang dikelola sendiri, serta menyediakan asisten PDF internal. Repo ini dipakai untuk demonstrasi interview AI Engineer dan **bukan situs resmi PT Samick Indonesia**. Katalog awal diisi sekali dari seed lokal, lalu dikelola manual melalui CMS. Tidak ada impor URL atau koneksi ke website PT Samick Indonesia. Harga yang tersimpan dan laporan keuangan contoh adalah data simulasi.

## Fitur yang sudah berjalan

- Katalog 10 gitar, chat rekomendasi Gemini, analisis satu foto, dan opsi snapshot webcam.
- CMS satu admin untuk tambah/edit/nonaktifkan/hapus produk, unggah foto produk, PDF digital, tanya dokumen dengan sumber, dan pilih provider AI.
- PostgreSQL + pgvector, FastAPI, Next.js, PyMuPDF, dan embedding PDF `gemini-embedding-2`.

Halaman customer menggunakan carousel, katalog gitar tanpa sidebar, dan asisten dalam bubble chat. Keputusan tampilannya dicatat di [DESIGN.md](docs/DESIGN.md). Katalog dan rekomendasi AI mengambil produk aktif dari PostgreSQL. Perubahan admin langsung berlaku; seed hanya dijalankan sekali.

## Menjalankan dengan Docker Desktop

Docker Desktop harus menyala. Pada laptop yang sudah disiapkan, `.env` dan `backend/.env` berisi konfigurasi lokal; jalankan dari root repo:

```powershell
docker compose up -d --build
```

Buka [website](http://localhost:3000) atau [CMS](http://localhost:3000/admin). API health ada di `http://localhost:8000/api/health`. Frontend memakai port 3000 dan backend port 8000; database memakai port host 5434.

Perintah operasional:

```powershell
docker compose ps
docker compose logs -f backend
docker compose down
```

`docker compose down` menghentikan layanan tanpa menghapus volume database. PDF dan foto produk yang diunggah tersimpan di `backend/data/`, yang diabaikan Git dan di-mount ke container. Tidak perlu memasang Node.js atau Python di host untuk menjalankan aplikasi.

### Konfigurasi sekali pada clone baru

Salin `.env.example` menjadi `.env` dan `backend/.env.example` menjadi `backend/.env`. Isi `SAMICK_DB_PASSWORD` pada `.env` dengan password acak, lalu isi `GEMINI_API_KEY`, `ADMIN_PASSWORD_HASH`, dan `SESSION_SECRET` pada `backend/.env`. Kedua file tersebut diabaikan Git. Jangan kirim nilainya melalui chat. `OPENAI_API_KEY` opsional; ChatGPT Plus tidak memberi kredit OpenAI API.

Siapkan file lokal dan buat password database tanpa Python lokal:

```powershell
Copy-Item .env.example .env
Copy-Item backend/.env.example backend/.env
docker run --rm python:3.13-slim python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Tempel hasilnya pada `SAMICK_DB_PASSWORD` di `.env`. Lalu buat hash kata sandi admin dan session secret:

```powershell
docker compose build backend
docker compose run --rm --no-deps backend python -c "from argon2 import PasswordHasher; import getpass; print(PasswordHasher().hash(getpass.getpass('Password admin: ')))"
docker compose run --rm --no-deps backend python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Tempel hash kata sandi dan session secret ke `backend/.env`, isi key Gemini, lalu jalankan `docker compose up -d --build`. Tidak ada file rahasia yang masuk ke build image.

## Skenario pemeriksaan

1. Di CMS, ubah status satu produk; di halaman customer, pastikan katalog serta rekomendasi AI mengikuti produk aktif.
2. Unggah foto gitar dan periksa kandidat serta pernyataan ketidakpastian.
3. Login CMS, unggah PDF digital fiktif, tanyakan ringkasan dan satu angka, lalu buka halaman sumber.
4. Untuk PDF latihan lokal di `testing-assets/`, pertanyaan penjualan gitar akustik dan elektrik seharusnya menghasilkan Rp 12.300.000.000 dari halaman 2. Folder `testing-assets/` diabaikan Git agar bahan latihan tidak memenuhi repo aplikasi.

PDF scan tanpa lapisan teks belum didukung karena OCR belum tersedia. Uji webcam fisik dan foto ambigu masih perlu dilakukan sebelum interview. Perubahan katalog telah diuji bertahan setelah restart backend. OpenAI opsional belum teruji live karena kredit API habis.

Kebutuhan dan rancangan teknis: [BRD](docs/BRD.md), [PEP](docs/PEP.md), [ITA](docs/ITA.md).
