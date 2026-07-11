# ✅ Final Plan — Automasi GOKS Pipeline

## Keputusan Final
| Topik | Keputusan |
|---|---|
| Notifikasi | **Telegram Bot** (pemberitahuan saja) |
| Input eResto ZIP | **Folder Downloads PC** (`C:\Users\dikaa\Downloads\`) |
| Pilih bulan | **Saat trigger n8n** (form input) |
| Outlet SO tidak ada | **Kirim alert Telegram** (skip outlet itu) |

---

## Arsitektur Final

```
[User] Download eResto ZIP → simpan di Downloads
         │
         ▼
[n8n]  Manual Trigger
         ├── Form: Bulan (pilih 1-12)
         └── Form: Tahun (mis: 2026)
         │
         ▼
[n8n Node 1] Read Binary File
         └── Baca file ZIP terbaru di C:\Users\dikaa\Downloads\
             yang cocok pola: eResto_Mass_Analysis_*.zip
         │
         ▼
[n8n Node 2] Google Drive Search
         └── Query: name contains '07. JULI 2026'
             (nomor + nama bulan dibentuk dari input form)
             → Dapat list 35 file Sheets + ID-nya
         │
         ▼
[n8n Node 3] Loop — Download & Export per file GDrive
         └── Untuk setiap file Sheets:
             Export sebagai xlsx via Google Drive API
             Simpan ke memory dengan nama aslinya
         │
         ▼
[n8n Node 4] Bundle SO files → ZIP (Code Node JS)
         └── Gabungkan semua file SO jadi so_bundle.zip
         │
         ▼
[n8n Node 5] HTTP POST → Flask (endpoint BARU)
         └── POST http://localhost:5000/api/mass-sinkronisasi
             form-data:
               eresto_zip  = [ZIP dari Downloads]
               so_zip      = [so_bundle.zip]
               bulan       = "juli"
               tahun       = "2026"
         │
         ▼
[Flask] /api/mass-sinkronisasi
         1. Ekstrak eresto_zip → dict {no_outlet: file_bytes}
         2. Ekstrak so_zip → dict {no_outlet: file_bytes}
         3. Cari pasangan berdasarkan nomor outlet (01..35)
         4. Catat outlet tanpa pasangan SO → list_missing
         5. Proses setiap pasangan → proses_sinkronisasi_excel()
         6. Zip semua hasil → hasil_sinkronisasi_{bulan}_{tahun}.zip
         7. Return JSON:
            {
              "download_url": "/api/mass-sinko/download/...",
              "processed": 33,
              "missing_so": ["04. Belibis", "17. Tabing"],
              "errors": []
            }
         │
         ▼
[n8n Node 6] Download hasil ZIP dari Flask
         │
         ▼  
[n8n Node 7] Telegram — Kirim Notifikasi
         └── Pesan sukses:
             "✅ Sinkronisasi selesai!
              📅 Juli 2026
              ✔️ 33 outlet berhasil diproses
              ⚠️ 2 outlet tidak ada file SO:
                 - 04. Belibis
                 - 17. Tabing
              📎 [file ZIP hasil dilampirkan]"
         
         └── Jika ada error:
             "❌ Error pada outlet XX: [pesan error]"
```

---

## Perubahan Code yang Diperlukan

### A. Flask — Endpoint Baru

**File**: `modules/sinkronisasi/routes.py`

```python
@sinkronisasi_bp.route('/api/mass-sinkronisasi', methods=['POST'])
def mass_sinkronisasi():
    """
    Mass sinkronisasi: proses semua outlet sekaligus.
    Input:  eresto_zip  (multipart file) — ZIP hasil eResto Mass Analysis
            so_zip      (multipart file) — ZIP berisi semua file SO GDrive
            bulan       (form field)     — nama bulan: "juli", "agustus", dll
            tahun       (form field)     — tahun: "2026"
    Output: JSON { download_url, processed, missing_so, errors }
    """
```

**Logic matching nomor outlet:**
```python
import re

def extract_outlet_no(filename):
    """Ekstrak '01' dari '01. Taplau_...' atau '07. JULI 2026 01. TAPLAU'"""
    # Cari pola angka 2 digit yang diikuti titik dan spasi
    # Untuk eResto: ambil yang PERTAMA di awal nama
    # Untuk SO: ambil yang KEDUA (setelah nomor bulan)
    matches = re.findall(r'\b(\d{2})\.\s', filename)
    return matches  # [0] untuk eResto, [-1] untuk SO GDrive
```

**Contoh matching:**
- eResto: `01. Taplau_...` → `matches[0]` = `"01"` ✅
- SO GDrive: `07. JULI 2026 01. TAPLAU` → `matches[-1]` = `"01"` ✅

---

### B. n8n Workflow

#### Node detail:

**Node 1 — Manual Trigger**
```
Type: Manual Trigger (with form)
Fields:
  - bulan_no: Number (1-12)
  - tahun: Number (default: 2026)
```

**Node 2 — Code Node: Build search query**
```javascript
const bulan_names = ['JANUARI','FEBRUARI','MARET','APRIL','MEI','JUNI',
                     'JULI','AGUSTUS','SEPTEMBER','OKTOBER','NOVEMBER','DESEMBER'];
const no = String($json.bulan_no).padStart(2, '0');
const nama = bulan_names[$json.bulan_no - 1];
const tahun = $json.tahun;

return [{ query: `${no}. ${nama} ${tahun}`, bulan_str: nama.toLowerCase(), tahun_str: String(tahun) }];
```

**Node 3 — Google Drive: Search Files**
```
Operation: Search
Query: name contains '{{ $json.query }}'
Drive: Shared with me
```

**Node 4 — Loop over results**
```
Type: Split In Batches
Batch Size: 1
```

**Node 5 — Google Drive: Download (Export as xlsx)**
```
Operation: Download
File ID: {{ $json.id }}
Options: Google Workspace File Conversion: xlsx
```

**Node 6 — Code Node: ZIP all SO files**
```javascript
// Kumpulkan semua binary SO files
// Buat ZIP menggunakan jszip library
// Return as binary ZIP
```

**Node 7 — Read Binary File: eResto ZIP**
```
Path: C:\Users\dikaa\Downloads\
Pattern: eResto_Mass_Analysis_*.zip
Action: Read newest file matching pattern
```

**Node 8 — HTTP Request: Mass Sinkronisasi**
```
Method: POST
URL: http://localhost:5000/api/mass-sinkronisasi
Body: Form Data (multipart)
  - eresto_zip: [binary dari node 7]
  - so_zip: [binary ZIP dari node 6]
  - bulan: {{ $('Code').item.json.bulan_str }}
  - tahun: {{ $('Code').item.json.tahun_str }}
```

**Node 9 — HTTP Request: Download hasil**
```
Method: GET
URL: http://localhost:5000{{ $json.download_url }}
Response: Binary
```

**Node 10 — Telegram: Send Document**
```
Operation: Send Document
Chat ID: [Your Telegram Chat ID]
Document: [binary ZIP dari node 9]
Caption: ✅ Sinkronisasi {{ bulan }} {{ tahun }} selesai!
          ✔️ {{ $json.processed }} outlet diproses
          ⚠️ Missing SO: {{ $json.missing_so.join(', ') || 'Tidak ada' }}
```

---

## Urutan Eksekusi

| # | Tugas | Di mana | Estimasi |
|---|---|---|---|
| 1 | Tambah `/api/mass-sinkronisasi` ke Flask | `sinkronisasi/routes.py` | 30 mnt |
| 2 | Tambah helper extract + zip logic | `sinkronisasi/routes.py` | 15 mnt |
| 3 | Test endpoint via Postman (pakai sample ZIP) | Terminal | 15 mnt |
| 4 | Buat Telegram Bot (via @BotFather) | Telegram | 5 mnt |
| 5 | Bangun n8n workflow node per node | n8n UI | 30 mnt |
| 6 | Setup Google Drive credential di n8n | n8n + GDrive OAuth | 10 mnt |
| 7 | Test full flow end-to-end | n8n + Flask | 15 mnt |

**Total estimasi: ~2 jam**

---

## Yang Perlu Disiapkan User

> [!IMPORTANT]
> Sebelum eksekusi, kamu perlu:
> 1. **Buat Telegram Bot** via @BotFather → dapat `BOT_TOKEN`
> 2. **Dapat Chat ID** kamu (kirim pesan ke bot → cek via `getUpdates`)
> 3. **Pastikan Google account** sudah connected ke n8n (OAuth)

---

## Catatan Teknis

- Flask app sudah running di port 5000 ✅
- n8n sudah running di port 5678 ✅
- eResto ZIP output sudah terbukti bekerja ✅
- Existing `proses_sinkronisasi_excel()` akan digunakan ulang (tidak diubah) ✅
