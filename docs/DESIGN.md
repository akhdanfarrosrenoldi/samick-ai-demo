# Arah desain — Samick Guitar Guide

Status: **diterapkan pada halaman customer Next.js**, 28 Oktober 2026. Situs dapat dilihat melalui alamat frontend Docker Compose. Dokumen ini mencatat keputusan visual dan batas implementasi; tidak ada pratinjau HTML terpisah.

## Acuan yang diperiksa

Beranda [PT Samick Indonesia](http://ptsamick.com/inc_html/index.html) menampilkan logo di tengah, navigasi horizontal, dan carousel tiga gambar. Halaman Produk memakai sidebar kategori. Proyek ini mengambil struktur **beranda** sebagai acuan visual dan tidak membawa sidebar ke halaman customer. Gambar carousel disimpan lokal; aplikasi tidak mengambilnya dari website lain saat berjalan.

Menu resmi yang teramati adalah Perusahaan, Produk, Dealer, CSR, Kontak Kami, dan Community. Sesuai keputusan pemilik proyek, navigasi proyek hanya memuat bagian yang benar-benar tersedia: **Beranda, Produk, Asisten**. Beranda dan Produk menuju bagian halaman; Asisten membuka percakapan. CMS tidak muncul dalam navigasi publik dan tetap dapat dibuka langsung melalui `/admin`.

## Susunan halaman

1. Logo Samick di tengah pada header putih, diikuti satu baris navigasi dengan garis burgundy.
2. Carousel tiga gambar dengan tombol sebelumnya/berikutnya dan indikator gambar. Gambar gitar ditampilkan pertama; dua gambar lain mengikuti aset carousel situs acuan. Gerak otomatis berhenti saat hover/fokus serta dinonaktifkan bila pengguna memilih pengurangan animasi.
3. Katalog gitar tanpa sidebar. Kategori berada dalam baris filter yang mengambil kategori dari data produk; nama dan spesifikasi berasal dari API katalog.
4. Bubble asisten tetap di kanan bawah. Saat dibuka, panel berisi percakapan dua arah, rekomendasi produk, unggah foto, dan pengambilan satu foto melalui kamera.
5. Footer singkat. Tidak ada tombol login CMS, tautan ke website lain, maupun tulisan berulang tentang demo pada halaman customer.

## Prinsip tampilan

- Gunakan proporsi, logo, aset, dan warna yang mendekati beranda Samick tanpa membawa navigasi yang tidak mempunyai halaman.
- Biarkan foto produk dan informasi model menjelaskan katalog; hindari slogan abstrak, ornamen, dan tumpukan kartu promosi.
- Tampilkan kategori dan spesifikasi dari database. Harga simulasi tetap tersimpan internal, tetapi tidak dikirim oleh API publik atau ditampilkan kepada pembeli.
- Satu komponen `ProductCard` merender produk di katalog dan rekomendasi chat dengan ukuran yang sesuai konteks.
- Pada layar sempit, navigasi tetap tiga pilihan, katalog menjadi dua kolom, dan panel chat menyesuaikan lebar layar.

## Batas data dan CMS

Katalog awal berasal dari seed lokal satu kali. Admin mengisi dan mengubah produk manual lewat CMS, termasuk foto dan status aktif. Tidak ada input URL, crawler, atau sinkronisasi dengan website PT Samick Indonesia. Perubahan produk aktif langsung memengaruhi katalog dan rekomendasi berikutnya tanpa mengubah kode.

## Pemeriksaan yang diperlukan

- Periksa desktop dan mobile, navigasi, perpindahan tiga gambar, filter kategori, buka/tutup bubble, percakapan Gemini dua giliran, unggah foto, dan penanganan izin kamera.
- Pastikan API publik tidak memuat harga atau metadata internal.
- Perubahan produk dan jawaban AI telah diuji melalui API live; status produk bertahan setelah restart backend.
