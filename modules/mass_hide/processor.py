import os
import re
import datetime
import zipfile
import openpyxl

from modules.stockin.helpers import convert_to_xlsx_if_needed

def proses_mass_hide(file_paths, output_folder, job_id=None, progress_tracker=None):
    """
    Memproses daftar file Excel, menyembunyikan kolom O sampai X pada sheet harian (01-31),
    dan mengemas hasilnya ke dalam file ZIP.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder, exist_ok=True)
        
    timestamp = datetime.datetime.now().strftime("%Y%md_%H%M%S")
    zip_filename = f"MassHide_{timestamp}.zip"
    zip_path = os.path.join(output_folder, zip_filename)
    
    success_count = 0
    fail_count = 0
    errors = []
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for fpath in file_paths:
            basename = os.path.basename(fpath)
            # Hilangkan prefix 'mh_' yang mungkin kita tambahkan di route
            clean_basename = basename[3:] if basename.startswith("mh_") else basename
            
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
                        # Buka proteksi sheet sementara jika diperlukan
                        ws.protection.sheet = False
                        
                        # Hide kolom O sampai X
                        for col_letter in ['O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X']:
                            ws.column_dimensions[col_letter].hidden = True
                        
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
