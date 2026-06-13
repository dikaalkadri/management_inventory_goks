# 📦 Goks! Stock-In Manager

Aplikasi web localhost untuk manajemen stok harian dari PDF surat jalan ke Excel.

---

## 🚀 Cara Install & Jalankan

### 1. Pastikan Python 3.10+ sudah terinstall

```
python --version
```

### 2. Install dependencies

Buka terminal / Command Prompt di folder `goks-stockin`, lalu:

```
pip install -r requirements.txt
```

### 3. Jalankan server

```
python app.py
```

### 4. Buka di browser

```
http://localhost:5000
```

---

## 📁 Struktur Folder

```
goks-stockin/
├── app.py                  ← Backend Flask
├── requirements.txt        ← Dependencies
├── inventory.json          ← Config inventory (auto-update via Settings)
├── app_config.json         ← Config file Excel & stok awal (auto-generated)
├── templates/
│   ├── index.html          ← Halaman utama (upload & submit)
│   └── settings.html       ← Halaman settings
├── uploads/                ← Folder temp PDF (auto-deleted setelah parse)
└── data/                   ← Folder default untuk file Excel
```

---

## 🔧 Setup Pertama Kali

1. **Buka Settings** → isi nama file Excel dan path folder
2. **Isi Stok Awal** → per item, per file Excel
3. Kembali ke halaman Upload → drag & drop PDF → edit → Submit

---

## 📄 Format PDF yang Didukung

PDF yang mengandung teks (bukan gambar scan):
- Surat Jalan
- Stock Order (SO)

Field yang di-parse otomatis:
- **Outlet/Divisi Penerima** — dari baris mengandung "Divisi Penerima" atau "Kepada"
- **Tanggal** — dari baris mengandung "Tanggal" atau "Date"
- **Item & Qty** — dari teks yang cocok dengan keyword di `inventory.json`

---

## 📊 Logika Konversi Qty

```
excel_qty = (pdf_qty / pdf_unit_qty) × excel_factor
```

Contoh SKM 2440gr (faktor=5):
- PDF: 2440 gr → excel_qty = (2440 / 2440) × 5 = **5**
- PDF: 4880 gr → excel_qty = (4880 / 2440) × 5 = **10**

---

## ⚠️ Catatan

- Jika `app_config.json` belum ada, akan dibuat otomatis saat pertama save config
- File Excel akan dibuat otomatis jika belum ada di path yang dikonfigurasi
- Data duplikat (outlet+tanggal+item sama) akan **ditimpa (overwrite)**
- Cup Twist otomatis generate baris Tutup Twist dengan qty yang sama
