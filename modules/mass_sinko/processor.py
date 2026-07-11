"""
Mass Sinkronisasi Processor.

Logic utama:
- Ekstrak ZIP eResto → dict {outlet_no (str "01".."35"): bytes}
- Ekstrak ZIP SO     → dict {outlet_no (str "01".."35"): bytes}
- Match berdasarkan nomor outlet 2-digit
- Proses setiap pasangan dengan proses_sinkronisasi_excel()
- Kumpulkan output → ZIP final
"""
import os
import re
import zipfile
import tempfile
import shutil
from io import BytesIO
from typing import Optional

from modules.sinkronisasi.processor import proses_sinkronisasi_excel
from modules.stockin.helpers import convert_to_xlsx_if_needed  # dipakai untuk konversi xls→xlsx


# ─── Regex helper ────────────────────────────────────────────────────────────

from modules.eresto_mass.processor import load_outlets_inventory

def _extract_outlet_no(filename: str) -> Optional[str]:
    """
    Ekstrak nomor outlet 2-digit dari nama file.
    Sekarang membaca nama outlet dari inventory agar 100% akurat 
    meskipun ada typo nomor (misal '3.' bukan '03.').
    """
    name_lower = filename.lower()
    
    # 1. Coba cocokkan nama outlet dari inventory
    outlets_list = load_outlets_inventory()
    for outlet in outlets_list:
        parts = outlet.split('.', 1)
        if len(parts) == 2:
            no = parts[0].strip()
            nama = parts[1].strip().lower()
            if nama in name_lower or nama.replace(' ', '_') in name_lower:
                return no.zfill(2)

    # 2. Fallback: Cari angka 2-digit yang diikuti titik + spasi atau underscore
    # (Hanya jika nama benar-benar tidak cocok/typo parah)
    matches = re.findall(r'(?<!\d)(\d{2})(?:\.[ \t]|_|\s)', filename)
    if not matches:
        return None
    return matches[-1]


def _build_outlet_map(zip_bytes: bytes, label: str) -> dict:
    """
    Buka ZIP dari bytes, return dict:
        { outlet_no: {"filename": str, "bytes": bytes} }
    Abaikan file yang bukan .xlsx / .xls
    """
    outlet_map = {}
    with zipfile.ZipFile(BytesIO(zip_bytes), 'r') as zf:
        for info in zf.infolist():
            fname = os.path.basename(info.filename)
            if not fname or info.is_dir():
                continue
            ext = os.path.splitext(fname)[1].lower()
            if ext not in ('.xlsx', '.xls'):
                continue

            no = _extract_outlet_no(fname)
            if no is None:
                print(f"[MASS-SINKO] [{label}] Tidak dapat ekstrak nomor outlet dari: {fname}")
                continue

            if no in outlet_map:
                print(f"[MASS-SINKO] [{label}] Duplikat nomor {no}: {fname} (diabaikan)")
                continue

            outlet_map[no] = {
                "filename": fname,
                "bytes": zf.read(info.filename),
            }
    return outlet_map


# ─── Main processor ──────────────────────────────────────────────────────────

def process_mass_sinkronisasi(
    eresto_zip_bytes: bytes,
    so_zip_bytes: bytes,
    bulan: str,
    tahun: str,
    output_folder: str,
) -> dict:
    """
    Proses mass sinkronisasi semua outlet.

    Returns dict:
    {
        "zip_filename": str,          # nama ZIP output
        "processed": int,             # jumlah outlet berhasil
        "missing_so": [str],          # outlet yang tidak ada SO-nya
        "missing_eresto": [str],      # outlet yang tidak ada file eResto-nya
        "errors": [{"outlet": str, "error": str}],
        "success_outlets": [str],
    }
    """
    # Build mapping nomor → file info
    eresto_map = _build_outlet_map(eresto_zip_bytes, "eResto")
    so_map     = _build_outlet_map(so_zip_bytes, "SO")

    all_nos = sorted(set(eresto_map.keys()) | set(so_map.keys()))

    missing_so      = []
    missing_eresto  = []
    errors          = []
    success_outlets = []

    # Folder kerja sementara
    tmpdir = tempfile.mkdtemp(prefix="mass_sinko_")

    try:
        for no in all_nos:
            outlet_display = f"{no}. {eresto_map.get(no, so_map.get(no, {})).get('filename', '???').split('_')[0].split('.', 1)[-1].strip()}"

            if no not in eresto_map:
                missing_eresto.append(f"{no} (ada di SO tapi tidak di eResto)")
                continue

            if no not in so_map:
                # Coba dapatkan nama outlet dari eResto filename
                eresto_fname = eresto_map[no]["filename"]
                nama = eresto_fname.split("_")[0]  # "01. Taplau"
                missing_so.append(nama)
                continue

            # ── Pasangan lengkap → proses ──────────────────────────
            eresto_info = eresto_map[no]
            so_info     = so_map[no]

            try:
                # Simpan file sementara ke tmpdir
                eresto_tmp = os.path.join(tmpdir, f"eresto_{no}_{eresto_info['filename']}")
                so_tmp     = os.path.join(tmpdir, f"so_{no}_{so_info['filename']}")

                with open(eresto_tmp, 'wb') as f:
                    f.write(eresto_info['bytes'])
                with open(so_tmp, 'wb') as f:
                    f.write(so_info['bytes'])

                # Konversi ke xlsx jika masih xls
                eresto_xlsx = _to_xlsx(eresto_tmp, tmpdir)
                so_xlsx     = _to_xlsx(so_tmp, tmpdir)

                # Panggil processor sinkronisasi yang sudah ada
                output_filename, sheets_count = proses_sinkronisasi_excel(
                    sumber_path_xlsx=eresto_xlsx,
                    tujuan_path_xlsx=so_xlsx,
                    output_folder=output_folder,
                )

                outlet_name = eresto_info['filename'].split('_')[0]  # "01. Taplau"
                success_outlets.append({
                    "no": no,
                    "name": outlet_name,
                    "output_file": output_filename,
                    "sheets": sheets_count,
                })
                print(f"[MASS-SINKO] ✅ {outlet_name} → {output_filename} ({sheets_count} sheets)")

            except Exception as e:
                eresto_name = eresto_map[no]['filename'].split('_')[0]
                errors.append({"outlet": eresto_name, "error": str(e)})
                print(f"[MASS-SINKO] ❌ {eresto_name}: {e}")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    # ── Buat ZIP final berisi semua output ────────────────────────────────
    zip_name = f"MassSinko_{bulan.capitalize()}_{tahun}.zip"
    zip_path = os.path.join(output_folder, zip_name)

    processed_count = len(success_outlets)

    if processed_count > 0:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zout:
            for item in success_outlets:
                src = os.path.join(output_folder, item['output_file'])
                if os.path.exists(src):
                    zout.write(src, arcname=item['output_file'])

    return {
        "zip_filename": zip_name if processed_count > 0 else None,
        "processed": processed_count,
        "missing_so": missing_so,
        "missing_eresto": missing_eresto,
        "errors": errors,
        "success_outlets": [f"{i['no']}. {i['name'].split('. ', 1)[-1]}" for i in success_outlets],
    }


def _to_xlsx(path: str, tmpdir: str) -> str:
    """
    Jika file adalah .xls, konversi ke xlsx di tmpdir.
    Jika sudah xlsx, kembalikan path asli.
    """
    if path.lower().endswith('.xls'):
        try:
            from xls2xlsx import XLS2XLSX
            out_path = path + 'x'  # .xls → .xlsx
            x2x = XLS2XLSX(path)
            x2x.to_xlsx(out_path)
            return out_path
        except Exception as e:
            raise RuntimeError(f"Gagal konversi xls→xlsx: {e}")
    return path
