import os
import sys

# Add root directory to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.perbaikan_data.processor import process_perbaikan_data

if __name__ == '__main__':
    training_dir = r"d:\Goks!\GOKS! WEB APP - RUNNING\Data Training Old"
    
    so_file = os.path.join(training_dir, "01. Januari 2025 Air Dingin.xlsx")
    inv_file = os.path.join(training_dir, "inventory_movements.xls")
    tpl_file = os.path.join(training_dir, "stock omname adjustment.xlsx")
    
    with open(so_file, 'rb') as f: so_bytes = f.read()
    with open(inv_file, 'rb') as f: inv_bytes = f.read()
    with open(tpl_file, 'rb') as f: tpl_bytes = f.read()
    
    out_dir = r"D:\Goks!\OUTPUT GUDANG AKHIR"
    
    print("Mulai proses test...")
    res = process_perbaikan_data("test_task", so_bytes, inv_bytes, tpl_bytes, out_dir)
    print("Selesai!", res)
