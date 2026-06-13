# 📦 Goks! Stock-In Manager & eResto Analysis — Program Structure Reference

Dokumen ini dibuat khusus untuk memetakan arsitektur, struktur folder, logika bisnis, dan file konfigurasi dari project **Goks! Stock-In Manager & eResto Analysis (Versi 2.7 - Modular Blueprint)**.

Tujuan utama file ini adalah sebagai referensi instan bagi AI (seperti Claude/Gemini) pada sesi chat berikutnya agar **menghemat token secara signifikan** dan mempercepat pemahaman program tanpa perlu men-scan seluruh file source code dari awal.

---

## 🗺️ Gambaran Umum Aplikasi

Aplikasi ini adalah **aplikasi web berbasis Flask (Python)** yang berjalan di localhost untuk kebutuhan operasional gudang dan keuangan **Goks!**:
1. **Stock-In Gudang**: Otomasi input stok masuk/keluar dari PDF surat jalan ke file Excel stok harian gudang dengan kalkulasi stok awal dan histori secara otomatis.
2. **eResto Sales Analysis**: Memproses laporan penjualan eResto (.xlsx/.xls) dan menyusunnya dalam bentuk matriks harian (cross-tabulation produk vs tanggal) secara otomatis menggunakan formula `SUMIFS`.
3. **Sinkronisasi Penjualan & Kerugian (SO Kerugian)**: Menyinkronkan data penjualan dengan file target (Excel kerugian outlet bulanan), menerapkan rumus kerugian otomatis per baris (`=Harga*Selisih`), melakukan *auto-merge* sel kategori secara vertikal, menulis conditional formatting warna merah jika rugi, serta membuat sheet **"Rekap Kerugian"** rangkuman satu bulan penuh.

---

## 📁 Struktur Direktori & File (Modular Blueprint)

Berikut adalah struktur terorganisir lengkap file dalam project ini beserta peran masing-masing file:

```text
d:\Goks!\SO KERUGIAN PROGRAM 2.7\
├── app.py                  # Entrypoint Flask super ringkas, mendaftarkan semua Blueprint (eresto, stockin, sinkronisasi)
├── config.py               # Konfigurasi terpusat (path folder, indeks kolom eResto, warna Excel)
├── requirements.txt        # Dependencies Python (flask, openpyxl, pdfplumber, pandas, xls2xlsx, dll)
│
├── inventory.json          # Konfigurasi metadata item (nama sheet, keyword PDF, faktor konversi) & daftar outlet
├── app_config.json         # Konfigurasi aktif Excel path/nama file & histori stok awal per item per file Excel
├── master_catalog.json     # Katalog harga satuan produk & kategori (digunakan pada menu Sinkronisasi Kerugian)
├── master_products.json    # Daftar urutan produk tetap untuk matriks laporan eResto
│
├── modules/
│   ├── __init__.py
│   │
│   ├── eresto/             # Modul khusus untuk pemrosesan file penjualan eResto
│   │   ├── __init__.py
│   │   ├── routes.py       # Blueprint routes Flask khusus eResto (Upload, Process, CRUD Master Product)
│   │   ├── cleaner.py      # Pipeline pembersihan data eResto Pandas (ekstrak tanggal, produk, paid qty)
│   │   ├── excel_generator.py # Pembuat matriks eResto Excel menggunakan openpyxl & rumus SUMIFS
│   │   └── master_product.py # Helper read/write file master_products.json
│   │
│   ├── stockin/            # Modul khusus untuk logika Stock-In & Stok Gudang
│   │   ├── __init__.py
│   │   ├── routes.py       # [BARU] Blueprint stockin_bp untuk semua routing/API Stock-In
│   │   ├── helpers.py      # [BARU] Tempat 13 fungsi helper manipulasi file Excel stok gudang harian
│   │   └── formula_config.py # Konfigurasi formula kolom J (konversi resep) & K, L, M serta proteksi sheet
│   │
│   └── sinkronisasi/       # Modul khusus untuk Sinkronisasi Penjualan & Kerugian (SO Kerugian)
│       ├── __init__.py
│       ├── routes.py       # [BARU] Blueprint sinkronisasi_bp untuk routing API Sinkronisasi & Katalog CRUD
│       └── processor.py    # [BARU] Inti proses sinkronisasi, unmerge/re-merge vertikal, & rekap bulanan
│
├── services/               # Shared services terpusat (tunggal, mencegah duplikasi)
│   ├── __init__.py
│   ├── catalog_service.py  # Service read/write master_catalog.json dan update harga produk
│   ├── excel_style_helper.py # Helper styling Excel (copy row properties, safe merge cells)
│   └── file_handler.py     # Helper upload/download file, validasi ekstensi, & generate nama file output
│
├── templates/              # Halaman UI Jinja2 HTML (HTML bersih tanpa script/style inline raksasa)
│   ├── index.html          # Halaman utama Stock-In (Upload PDF Surat Jalan & submit input)
│   ├── settings.html       # Halaman pengaturan Stock-In (Nama file Excel, path folder, & Input Stok Awal)
│   ├── stock_gudang.html   # Halaman visualisasi sisa stok gudang saat ini
│   ├── eresto_analysis.html # Halaman upload & pengaturan urutan produk untuk Analisa Laporan eResto
│   └── sinkronisasi_penjualan.html # Halaman utama upload file Penjualan vs Kerugian & kelola Master Catalog
│
├── static/                 # Aset statis aplikasi (ditulis lowercase agar kompatibel dengan Linux)
│   ├── Goks.png            # Logo aplikasi
│   ├── css/
│   │   └── eresto.css      # CSS styling UI modern dengan tema ungu/emerald gelap
│   └── js/
│       └── eresto.js       # Javascript controller frontend untuk interaksi AJAX & event handler
│
├── data/                   # Folder default penyimpanan file Excel hasil generate (jika tidak diubah di settings)
├── uploads/                # Folder temporer menyimpan file PDF/Excel saat diproses (auto-cleanup)
└── output/                 # Folder hasil akhir output Excel yang siap di-download oleh user
```

---

## 🛠️ Modul Utama & Alur Kerja (Workflow)

### 1. Modul Stock-In (Stok Harian Gudang)
* **Tempat Kode**: [modules/stockin/routes.py](file:///d:/Goks!/SO%20KERUGIAN%20PROGRAM%202.7/modules/stockin/routes.py) & [modules/stockin/helpers.py](file:///d:/Goks!/SO%20KERUGIAN%20PROGRAM%202.7/modules/stockin/helpers.py)
* **Tujuan**: Membaca file PDF surat jalan/stock order gudang, mengekstrak data item yang masuk/keluar, dan menulisnya ke file Excel stok gudang di sheet kategori yang sesuai (misal: "Bahan Utama", "Topping", "Powder", dll).
* **Alur Ekstraksi PDF**:
  1. `routes.py` menerima file PDF yang di-upload.
  2. PDF dibaca baris demi baris menggunakan `pdfplumber`.
  3. Divisi penerima (outlet) dan tanggal di-parse otomatis dari baris teks yang mengandung keyword `"Divisi Penerima"`, `"Kepada"`, `"Tanggal"`, atau `"Date"`.
  4. Qty item dicocokkan berdasarkan `pdf_keywords` yang ada di `inventory.json`.
  5. Konversi kuantitas dari PDF ke format Excel menggunakan rumus:
     $$\text{excel\_qty} = \left(\frac{\text{pdf\_qty}}{\text{pdf\_unit\_qty}}\right) \times \text{excel\_factor}$$
  6. Hasil ekstraksi ditampilkan sebagai kartu-kartu preview di UI untuk divalidasi/diedit oleh user sebelum di-submit ke Excel.
* **Alur Penulisan Excel**:
  1. File Excel dimuat via `openpyxl`. Jika file belum ada di path yang ditentukan (`app_config.json`), file baru akan dibuat otomatis.
  2. Item ditulis ke dalam kolom-kolom terpisah (1 item memakan 5 kolom: **Tanggal, Masuk, Keluar, Sisa Stok, Keterangan**). Kolom baru akan dibuat di sebelah kanan (step 6 kolom) jika item belum pernah terdaftar di sheet tersebut.
  3. Menulis baris **"STOCK GUDANG AWAL"** pada baris ke-5 untuk inisialisasi awal.
  4. Jika mendeteksi entri dengan tanggal + keterangan/outlet yang sama, data lama akan **ditimpa (overwrite)** secara otomatis untuk menghindari duplikasi data.
  5. Memicu fungsi `recalculate_item_stock()` untuk memperbarui seluruh rumus sisa stok di bawahnya secara berantai.

### 2. Modul eResto Sales Analysis
* **Tempat Kode**: [modules/eresto/routes.py](file:///d:/Goks!/SO%20KERUGIAN%20PROGRAM%202.7/modules/eresto/routes.py) & [modules/eresto/cleaner.py](file:///d:/Goks!/SO%20KERUGIAN%20PROGRAM%202.7/modules/eresto/cleaner.py)
* **Tujuan**: Merapikan file laporan penjualan mentah eResto dan mengubahnya menjadi format matriks harian untuk mempermudah audit penjualan bulanan.
* **Alur Kerja**:
  1. User mengunggah file Excel laporan order eResto (`.xlsx` atau `.xls`).
  2. Pembersih data `cleaner.py` memuat file ke DataFrame Pandas, mendeteksi kolom kunci (Tanggal di Kolom A, Produk di Kolom P, Paid Qty di Kolom Q) dan membuang baris kosong.
  3. File Excel tujuan dibuat. Kolom B sampai O disembunyikan menggunakan properti `hidden = True`.
  4. Daftar urutan produk dari `master_products.json` ditulis secara vertikal di **Kolom S** (mulai baris 2).
  5. Kalender tanggal dalam bulan terpilih (01 s.d. 30/31) ditulis secara horizontal di **Row 1** mulai dari **Kolom T**.
  6. Di dalam setiap sel matriks pertemuan produk dan tanggal, dituliskan formula Excel `SUMIFS` dinamis:
     `=SUMIFS($Q:$Q, $P:$P, $S<baris>, $A:$A, <kolom>$1)`
  7. Diberikan styling premium (Header Emerald gelap, border lavender soft, zebra striping genap-ganjil lavender-putih).

### 3. Modul Sinkronisasi Penjualan & Kerugian (SO Kerugian)
* **Tempat Kode**: [modules/sinkronisasi/routes.py](file:///d:/Goks!/SO%20KERUGIAN%20PROGRAM%202.7/modules/sinkronisasi/routes.py) & [modules/sinkronisasi/processor.py](file:///d:/Goks!/SO%20KERUGIAN%20PROGRAM%202.7/modules/sinkronisasi/processor.py)
* **Tujuan**: Menyinkronkan file rekap penjualan eResto dengan file Excel kerugian harian outlet, serta menuliskan formula kerugian otomatis.
* **Alur Kerja**:
  1. User mengunggah file penjualan (Sumber) dan file kerugian outlet harian (Tujuan).
  2. Menghitung data penjualan real per hari berdasarkan paid qty eResto.
  3. Membaca master produk dari **Master Catalog** (`master_catalog.json`) yang berisi daftar produk, kategori, dan harga beli per pcs.
  4. Pada setiap sheet tanggal (nama sheet "01" sampai "31") di file tujuan:
     * Menghapus merge sel kategori lama di **Kolom O** (Kolom 15).
     * Melakukan sinkronisasi baris produk: menambah baris kosong (`insert_rows`) jika katalog bertambah, atau menghapus baris (`delete_rows`) jika katalog berkurang, sehingga baris produk di Excel presisi sama dengan urutan Master Catalog.
     * Properti visual (border, font, background) baris yang baru disisipkan akan dikloning dari baris pertama data agar visual tetap rapih dan konsisten.
     * Menuliskan data terbaru ke kolom: **O** (Kategori), **P** (Nama Produk), **Q** (eResto Paid Qty), **W** (Harga Produk dari Master Catalog), dan **X** (Rumus Nilai Kerugian: `=W{r}*M{r}`).
     * Menerapkan formula otomatis untuk kolom operasional toko via `modules/stockin/formula_config.py` (Kolom J, K, L, M) dan kolom total kerugian (Kolom W & X).
     * Melakukan **Auto-Merge Vertikal** kembali pada **Kolom O** untuk sel kategori yang memiliki nama kategori yang sama secara berurutan, lalu memposisikan teks di tengah-tengah (*align center & vertical center*).
     * Menerapkan conditional formatting: jika nilai sel pada area data `< 0` (negatif/rugi), sel otomatis berwarna background merah muda pekat (`FFCCCC`) dengan font merah tebal (`CC0000`).
  5. Membuat/menimpa sheet pertama bernama **"Rekap Kerugian"**:
     * Berisi tabel rangkuman 1 bulan penuh (Tanggal 1 s.d 31).
     * Kolom terdiri dari: **No, Tanggal, Selisih Bersih (Surplus + Defisit)** menggunakan rumus `=SUM('01'!X:X)`, **Kerugian Murni (Defisit Saja)** menggunakan rumus `=SUMIF('01'!X:X, "<0")`, dan **Keterangan**.
     * Baris paling bawah berisi TOTAL menggunakan rumus `=SUM(C3:C33)`.
     * Diberikan visual premium hijau tua ber-border abu-abu tipis, freeze pane di sel A3, dan auto-calculate yang langsung aktif.
  6. File hasil sinkronisasi disimpan di folder `output/` dengan format nama `kerugian_<outlet>_<bulan>_<tahun>.xlsx` (contoh: `kerugian_32__selayo_mei_2026.xlsx`).

---

## 📐 Logika Bisnis, Formula Excel, & Proteksi

Kunci utama dari keandalan perhitungan kerugian dan sisa stok diatur di dalam file `modules/stockin/formula_config.py`.

### 1. Rumus Fix Kolom J (Konversi Porsi Menu ke Bahan Baku)
Kolom J adalah kolom **Pemakaian Riil** bahan baku mentah. Nilainya didapatkan dari perkalian jumlah penjualan menu jadi di POS (Kolom Q) dikalikan gramatur resep standar produk tersebut.

*Contoh beberapa J_FORMULAS penting:*
* **Susu UHT (Baris 2)**:
  `=((Q8+Q9+Q10+Q11+Q14+Q15+Q16+Q17+Q18+Q19+Q49+Q50+Q51+Q52+Q53+Q61+Q63+Q64)*130)+((Q56+Q57+Q65+Q58)*100)+(Q66*150)`
* **Fructose Syrup (Baris 6)**:
  `=(Q2+Q3+Q4+Q5+Q8+Q9+Q10+Q11+Q16+Q17+Q18+Q19+Q49+Q50+Q51+Q52+Q53+Q54+Q55+Q61+Q63+Q64+Q65+Q66+Q6+Q7+Q60)*40`
* **Softmix Vanilla (Baris 60)**:
  `=(Q21*210)+(Q24*210)+(Q25*210)+(Q26*210)+(Q27*210)+(Q28*210)+(Q29*110)+(Q37*210)+(Q38*210)+(Q39*210)+(Q40*210)+(Q41*55)+(Q42*55)+(Q46*55)+(Q48*55)+(Q99*45)+(Q100*85)+(Q107*85)+((Q70+Q101)*100)+(200*(SUM(Q110:Q117)))`

### 2. Rumus Relatif Kolom K, L, M
Rumus ini diterapkan secara dinamis menggunakan perulangan baris (`r`) dari baris **2 sampai 118**:
* **Kolom K (Sisa Teoretis Toko)**: `=D{r}+E{r}-F{r}-G{r}` (Stok Awal + Stok Masuk - Rusak - Transfer Keluar)
* **Kolom L (Sisa Teoretis Penjualan)**: `=D{r}+E{r}-J{r}` (Stok Awal + Stok Masuk - Pemakaian Resep Kolom J)
* **Kolom M (Selisih Teoretis vs Riil)**: `=J{r}-K{r}` (Selisih pemakaian bahan baku berdasarkan POS vs fisik riil)

### 3. Proteksi Sheet & Keamanan Data
Aplikasi ini secara otomatis mengunci lembar kerja Excel agar formula kalkulasi penting tidak terhapus atau rusak oleh user secara tidak sengaja:
* **Password Proteksi**: `"12345678"` (dikonfigurasi pada variabel `SHEET_PASSWORD`).
* **Kolom yang Dikunci (Locked)**: Kolom **J, K, L, M, Q, W, X** (seluruh cell formula dan paid qty dari POS dikunci otomatis).
* **Hak Akses User**: User hanya diizinkan untuk melihat/memilih cell yang tidak dikunci (seperti Stok Masuk, Rusak, Stok Akhir Fisik) serta melakukan resize lebar kolom/tinggi baris.

---

## 🗄️ File & Skema JSON Pengaturan

Project ini menyimpan data konfigurasi menggunakan format JSON sederhana. Berikut adalah struktur skema dari masing-masing file:

### 1. `inventory.json`
Menyimpan daftar item inventarisasi gudang beserta keyword pencocokan teks di PDF surat jalan.
```json
{
  "items": [
    {
      "id": "tapioca_pearl",
      "name": "Tapioca Pearl",
      "display": "Tapioca Pearl",
      "sheet": "Bahan Utama",
      "pdf_keywords": ["tapioca pearl", "bubble pearl", "boba pearl"],
      "pdf_unit_qty": 1000,
      "pdf_unit_type": "gr",
      "excel_factor": 1,
      "default_unit": "gr"
    }
  ],
  "outlets": [
    "000. Gudang",
    "32. Selayo"
  ]
}
```

### 2. `master_catalog.json`
Menyimpan database produk jadi, kategori, dan harga beli per pcs untuk perhitungan kerugian.
```json
{
  "catalog": [
    {
      "product": "Lemon Tea",
      "category": "Tea Series",
      "price": 17.0
    }
  ]
}
```

### 3. `app_config.json`
Menyimpan konfigurasi aktif Excel yang sedang digunakan beserta riwayat stok awal per item per file.
```json
{
  "excel_filename": "april2030.xlsx",
  "excel_folder": "D:\\Goks!\\SO GUDANG MEI 2026\\1 MEI",
  "stok_awal": {
    "so_mei.xlsx": {
      "Tapioca Pearl": 100.0,
      "Soft Mix Vanilla": 50.0
    }
  }
}
```

---

## 💡 Panduan Penambahan & Modifikasi Fitur Baru (Untuk AI/Developer)

Saat Anda meminta untuk melakukan tugas-tugas penambahan fitur di masa depan, gunakan panduan cepat di bawah ini agar perubahan tidak merusak struktur yang sudah ada:

### A. Cara Menambahkan Produk Baru ke Master Catalog
1. Buka file [master_catalog.json](file:///d:/Goks!/SO%20KERUGIAN%20PROGRAM%202.7/master_catalog.json).
2. Tambahkan objek JSON baru di dalam array `"catalog"` dengan format:
   ```json
   {
     "product": "Nama Produk Baru",
     "category": "Kategori Produk Baru",
     "price": 15.000
   }
   ```
3. Jika produk tersebut juga merupakan bagian dari rekap penjualan eResto harian, buka juga [master_products.json](file:///d:/Goks!/SO%20KERUGIAN%20PROGRAM%202.7/master_products.json) dan tambahkan `"Nama Produk Baru"` ke dalam urutan array `"products"`.

### B. Cara Mengubah Rumus Konversi Bahan Baku (Kolom J)
1. Buka file [formula_config.py](file:///d:/Goks!/SO%20KERUGIAN%20PROGRAM%202.7/modules/stockin/formula_config.py).
2. Temukan dictionary `J_FORMULAS`.
3. Cari nomor baris (Key) yang ingin diubah. Misalnya baris 60 untuk Softmix Vanilla.
4. Ganti rumus string (Value)-nya dengan formula Excel yang baru. Pastikan menggunakan huruf kapital untuk nama kolom dan formula (seperti `SUM`, `AVERAGE`, `SUMIFS`).
5. Jalankan fitur **"Recalculate Stock"** dari dashboard settings web untuk memproses ulang data pada file Excel yang sedang aktif.

### C. Cara Menambahkan Outlet Baru
1. Buka file [inventory.json](file:///d:/Goks!/SO%20KERUGIAN%20PROGRAM%202.7/inventory.json).
2. Cari array `"outlets"`.
3. Tambahkan nama outlet baru dengan format penomoran yang rapi (misal: `"36. Solok Baru"`).
4. Simpan file. Nama outlet akan otomatis muncul di dropdown pilihan aplikasi saat melakukan Stock-In maupun Sinkronisasi Kerugian.

### D. Cara Menjalankan Aplikasi di Localhost
* **Virtual Environment (Wajib)**: Gunakan interpreter Python virtual env (`.venv`) agar semua library (`xls2xlsx`, `openpyxl`, dll.) terbaca sempurna.
* **Cara Mengaktifkan Virtual Environment di Terminal**:
  ```powershell
  .venv\Scripts\activate
  ```
* **Cara Menjalankan Server**:
  ```powershell
  python app.py
  ```
* **Port default**: `http://localhost:5000`

---

*File `claude.md` ini merupakan dokumentasi hidup (living document). Pastikan untuk memperbarui file ini jika terdapat perubahan arsitektur atau penambahan modul berskala besar di masa mendatang.*
