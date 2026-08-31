import os
import re
import datetime
import zipfile
import openpyxl
from openpyxl.styles import Border, Side, PatternFill
from openpyxl.cell.cell import MergedCell

from modules.stockin.helpers import convert_to_xlsx_if_needed
from services.task_manager import active_tasks

# Border tipis dan PatternFill untuk zebra
BORDER_THIN = Side(border_style="thin", color="000000")
FILL_ZEBRA_EVEN = PatternFill("solid", fgColor="F5F7FA")
FILL_ZEBRA_ODD  = PatternFill("solid", fgColor="FFFFFF")

def _safe_write(ws, row, col, value):
    cell = ws.cell(row=row, column=col)
    if isinstance(cell, MergedCell):
        for merged_range in ws.merged_cells.ranges:
            if (merged_range.min_row <= row <= merged_range.max_row and
                    merged_range.min_col <= col <= merged_range.max_col):
                cell = ws.cell(row=merged_range.min_row, column=merged_range.min_col)
                break
    try:
        cell.value = value
    except:
        pass
    return cell

def proses_mass_update(task_id, file_paths, formulas, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder, exist_ok=True)
        
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"MassUpdate_Rumus_{timestamp}.zip"
    zip_path = os.path.join(output_folder, zip_filename)
    
    success_count = 0
    fail_count = 0
    errors = []
    
    if task_id in active_tasks:
        active_tasks[task_id]['total'] = len(file_paths)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for fpath in file_paths:
            basename = os.path.basename(fpath)
            clean_basename = basename[3:] if basename.startswith("mu_") else basename
            
            if task_id in active_tasks:
                active_tasks[task_id]['current_item'] = f"Memproses: {clean_basename}"
            
            try:
                fpath_xlsx = convert_to_xlsx_if_needed(fpath)
                if not fpath_xlsx or not os.path.exists(fpath_xlsx):
                    raise Exception("Gagal memproses file atau format tidak didukung")
                
                wb = openpyxl.load_workbook(fpath_xlsx)
                sheet_updated = False
                
                from services.catalog_service import load_materials
                mat_list = load_materials()
                mat_dict = {m.get('name', '').strip().lower(): m.get('price', 0) for m in mat_list}

                sorted_rows = sorted([int(k) for k in formulas.keys()])

                for sheet_name in wb.sheetnames:
                    # Proses sheet harian (01, 02, ..., 31)
                    if re.match(r"^\d{2}$", sheet_name.strip()):
                        ws = wb[sheet_name]
                        ws.protection.sheet = False
                        day_num = int(sheet_name.strip())
                        is_first_sheet = (day_num == 1)

                        for idx, row_idx in enumerate(sorted_rows):
                            row_str = str(row_idx)
                            item = formulas[row_str]
                            try:
                                formula_val = item.get("formula", "")
                                orig_cat = item.get("category", "").strip()
                                orig_name = item.get("name", "").strip()
                                mat_name = orig_name.lower()
                                
                                pattern = FILL_ZEBRA_EVEN if idx % 2 == 0 else FILL_ZEBRA_ODD
                                formula_fill = PatternFill("solid", fgColor="E6E6FA") # Warna agak pekat (Lavender)
                                
                                # Tentukan kolom mana yang mendapat warna formula (agak pekat)
                                formula_cols = [1, 9, 10, 11, 12, 13] # A, I, J, K, L, M
                                if not is_first_sheet:
                                    formula_cols.append(4) # Tambah D jika bukan sheet tgl 1
                                
                                # 1. Set border dan fill HANYA untuk kolom A s/d M (kolom 1 s/d 13)
                                for col_idx in range(1, 14):
                                    c = ws.cell(row=row_idx, column=col_idx)
                                    if not isinstance(c, MergedCell):
                                        # Set semua border ke thin secara default untuk merapikan
                                        c.border = Border(left=BORDER_THIN, right=BORDER_THIN, top=BORDER_THIN, bottom=BORDER_THIN)
                                        
                                        # Terapkan warna sesuai jenis kolom
                                        if col_idx in formula_cols:
                                            c.fill = formula_fill
                                        else:
                                            c.fill = pattern
                                
                                # 2. Tulis Kategori (Kolom A)
                                if orig_cat:
                                    _safe_write(ws, row_idx, 1, orig_cat)
                                    
                                # 3. Tulis Nama Bahan (Kolom B)
                                if orig_name:
                                    _safe_write(ws, row_idx, 2, orig_name)
                                    
                                # 4. Tulis Rumus Stock Awal (Kolom D) kecuali sheet 01
                                if not is_first_sheet:
                                    prev_day_str = f"{day_num - 1:02d}"
                                    _safe_write(ws, row_idx, 4, f"='{prev_day_str}'!F{row_idx}")
                                    
                                # 5. Tulis Rumus J (Kolom J - Stock Keluar POS)
                                if formula_val:
                                    _safe_write(ws, row_idx, 10, formula_val)
                                    
                                # 6. Tulis Rumus K, L, M
                                _safe_write(ws, row_idx, 11, f"=D{row_idx}+E{row_idx}-F{row_idx}-G{row_idx}") # K
                                _safe_write(ws, row_idx, 12, f"=D{row_idx}+E{row_idx}-J{row_idx}")            # L
                                _safe_write(ws, row_idx, 13, f"=J{row_idx}-K{row_idx}")                       # M
                                    
                                # 7. Tulis Master Harga (Kolom W)
                                if mat_name and mat_name in mat_dict:
                                    price_val = mat_dict[mat_name]
                                    _safe_write(ws, row_idx, 23, price_val)
                                elif item.get("price") is not None:
                                    _safe_write(ws, row_idx, 23, item.get("price"))
                                    
                                # 8. Tulis Rumus X (Nilai Kerugian)
                                _safe_write(ws, row_idx, 24, f"=W{row_idx}*M{row_idx}")
                            except ValueError:
                                continue

                        # Apply category borders
                        thick_side = Side(style='medium', color='000000')
                        current_cat = None
                        for idx, row_idx in enumerate(sorted_rows):
                            cat = formulas[str(row_idx)].get("category", "").strip()
                            if current_cat is None:
                                current_cat = cat
                            elif current_cat != cat:
                                prev_row = sorted_rows[idx - 1]
                                for col_idx in range(1, 14):
                                    cell = ws.cell(row=prev_row, column=col_idx)
                                    if not isinstance(cell, MergedCell):
                                        # Pastikan border lainnya tetap terjaga (thin)
                                        cell.border = Border(left=cell.border.left, right=cell.border.right, top=cell.border.top, bottom=thick_side)
                                current_cat = cat
                                
                        if sorted_rows:
                            last_row = sorted_rows[-1]
                            for col_idx in range(1, 14):
                                cell = ws.cell(row=last_row, column=col_idx)
                                if not isinstance(cell, MergedCell):
                                    cell.border = Border(left=cell.border.left, right=cell.border.right, top=cell.border.top, bottom=thick_side)

                        # Kembalikan proteksi sheet
                        ws.protection.sheet = True
                        ws.protection.password = "12345678"
                        sheet_updated = True
                
                if sheet_updated:
                    temp_output_path = os.path.join(output_folder, f"temp_{clean_basename}")
                    wb.save(temp_output_path)
                    wb.close()
                    
                    zipf.write(temp_output_path, clean_basename)
                    try:
                        os.remove(temp_output_path)
                    except:
                        pass
                        
                    success_count += 1
                else:
                    wb.close()
                    fail_count += 1
                    errors.append(f"{clean_basename}: Tidak ada sheet harian (01-31) yang ditemukan.")
                    
                if fpath_xlsx != fpath and os.path.exists(fpath_xlsx):
                    try:
                        os.remove(fpath_xlsx)
                    except:
                        pass
                        
            except Exception as e:
                fail_count += 1
                errors.append(f"{clean_basename}: {str(e)}")

            if task_id in active_tasks:
                active_tasks[task_id]['progress'] += 1
                
        # Bersihkan file origin
        for p in file_paths:
            if os.path.exists(p):
                try:
                    os.remove(p)
                except:
                    pass
                
    return zip_filename, success_count, fail_count, errors

