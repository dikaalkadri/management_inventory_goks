import os
import re
import datetime
import zipfile
import openpyxl

from modules.stockin.helpers import convert_to_xlsx_if_needed

def _safe_write(ws, row, col, value):
    cell = ws.cell(row=row, column=col)
    if type(cell).__name__ == 'MergedCell':
        for merged_range in ws.merged_cells.ranges:
            if (merged_range.min_row <= row <= merged_range.max_row and
                    merged_range.min_col <= col <= merged_range.max_col):
                cell = ws.cell(row=merged_range.min_row, column=merged_range.min_col)
                break
    try:
        cell.value = value
    except:
        pass

def proses_mass_update(file_paths, formulas, output_folder, job_id=None, progress_tracker=None):
    """
    Memproses daftar file Excel, mengubah rumus di Kolom J sesuai data 'formulas',
    dan mengemas hasilnya ke dalam file ZIP.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder, exist_ok=True)
        
    timestamp = datetime.datetime.now().strftime("%Y%md_%H%M%S")
    zip_filename = f"MassUpdate_Rumus_{timestamp}.zip"
    zip_path = os.path.join(output_folder, zip_filename)
    
    success_count = 0
    fail_count = 0
    errors = []
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for fpath in file_paths:
            basename = os.path.basename(fpath)
            # Hilangkan prefix 'mu_' yang kita tambahkan di route
            clean_basename = basename[3:] if basename.startswith("mu_") else basename
            
            try:
                # Convert ke .xlsx jika perlu
                fpath_xlsx = convert_to_xlsx_if_needed(fpath)
                if not fpath_xlsx or not os.path.exists(fpath_xlsx):
                    raise Exception("Gagal memproses file atau format tidak didukung")
                
                wb = openpyxl.load_workbook(fpath_xlsx)
                sheet_updated = False
                
                for sheet_name in wb.sheetnames:
                    # Proses hanya sheet harian (01, 02, ..., 31)
                    if re.match(r"^\d{2}$", sheet_name.strip()):
                        ws = wb[sheet_name]
                        # Buka proteksi sheet sementara jika diperlukan (Openpyxl terkadang bisa menulis cell yang di-lock, 
                        # tapi amannya disable dulu)
                        ws.protection.sheet = False
                        
                        for row_str, item in formulas.items():
                            try:
                                row_idx = int(row_str)
                                formula_val = item.get("formula", "")
                                if formula_val:
                                    _safe_write(ws, row_idx, 10, formula_val)
                            except ValueError:
                                continue
                                
                        # Kembalikan proteksi
                        ws.protection.sheet = True
                        ws.protection.password = "12345678"
                        sheet_updated = True
                
                if sheet_updated:
                    # Simpan workbook hasil modifikasi ke output sementara
                    temp_output_path = os.path.join(output_folder, f"temp_{clean_basename}")
                    wb.save(temp_output_path)
                    wb.close()
                    
                    # Tambahkan ke zip
                    zipf.write(temp_output_path, clean_basename)
                    
                    # Hapus temp output
                    try:
                        os.remove(temp_output_path)
                    except:
                        pass
                        
                    success_count += 1
                else:
                    wb.close()
                    fail_count += 1
                    errors.append(f"{clean_basename}: Tidak ada sheet harian (01-31) yang ditemukan.")
                    
                # Hapus fpath_xlsx jika itu adalah file hasil konversi
                if fpath_xlsx != fpath and os.path.exists(fpath_xlsx):
                    try:
                        os.remove(fpath_xlsx)
                    except:
                        pass
                        
            except Exception as e:
                fail_count += 1
                errors.append(f"{clean_basename}: {str(e)}")

            if job_id and progress_tracker and job_id in progress_tracker:
                progress_tracker[job_id]['current'] += 1
                
    return zip_filename, success_count, fail_count, errors
