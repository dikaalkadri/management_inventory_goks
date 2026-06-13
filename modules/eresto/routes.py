"""
eResto Blueprint Routes.

Handles HTTP endpoints for:
- Uploading eResto order reports
- Previewing raw and cleaned metadata
- Processing Excel files and generating reports
- Downloading generated Excel files
- Managing Master Product List (CRUD & reordering)
"""
import os
import pandas as pd
from flask import Blueprint, render_template, request, jsonify, send_from_directory, current_app

import config
from services.file_handler import save_upload, generate_output_filename, cleanup_file
from modules.eresto.cleaner import clean_data
from modules.eresto.excel_generator import generate_excel
from modules.eresto.master_product import (
    load_master_products, save_master_products,
    add_product, remove_product, reorder_products
)

eresto_bp = Blueprint('eresto', __name__, template_folder='../../templates')

# Uploaded eResto temporary mappings to avoid path traversal (in-memory cache)
# maps file_id -> file_path
TEMP_FILES = {}

@eresto_bp.route('/eresto')
def index():
    """Render the eResto sales analysis page."""
    products = load_master_products()
    return render_template('eresto_analysis.html', master_products=products)

@eresto_bp.route('/api/eresto/upload', methods=['POST'])
def upload_file():
    """Upload eResto order report excel and parse metadata preview."""
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "Tidak ada file yang diunggah"}), 400
        
    file_storage = request.files['file']
    try:
        # Save upload using safe helper
        filepath, original_name = save_upload(file_storage, subfolder='eresto_raw')
        
        # Parse data preview
        clean_result = clean_data(filepath)
        
        # Save path in temporary mappings
        import uuid
        file_id = str(uuid.uuid4())
        TEMP_FILES[file_id] = {
            'path': filepath,
            'original_name': original_name,
            'clean_result': clean_result
        }
        
        # Format preview rows safely (top 15)
        df_clean = clean_result['df']
        date_col = clean_result['date_col']
        product_col = clean_result['product_col']
        qty_col = clean_result['qty_col']
        
        # Convert date to string for json serialization
        df_preview = df_clean.head(15).copy()
        df_preview[date_col] = df_preview[date_col].dt.strftime('%d/%m/%Y')
        
        preview_rows = df_preview[[date_col, product_col, qty_col]].to_dict(orient='records')
        
        return jsonify({
            "status": "ok",
            "file_id": file_id,
            "filename": original_name,
            "total_rows_raw": clean_result['total_rows_raw'],
            "total_rows_clean": clean_result['total_rows_clean'],
            "date_range": clean_result['date_range'],
            "unique_products_count": len(clean_result['unique_products']),
            "preview_rows": preview_rows,
            "preview_cols": [date_col, product_col, qty_col]
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": f"Gagal mengunggah file: {str(e)}"}), 500

@eresto_bp.route('/api/eresto/process', methods=['POST'])
def process_data():
    """Process uploaded file, generate matrix, and return download link."""
    data = request.json or {}
    file_id = data.get('file_id')
    month = data.get('month')
    year = data.get('year')
    outlet = data.get('outlet', '').strip() # Ambil data outlet dari request frontend
    
    if not file_id or not month or not year or not outlet:
        return jsonify({"status": "error", "message": "Parameter tidak lengkap (termasuk outlet)"}), 400
        
    if file_id not in TEMP_FILES:
        return jsonify({"status": "error", "message": "Data upload kadaluwarsa atau tidak ditemukan"}), 404
        
    try:
        month = int(month)
        year = int(year)
    except ValueError:
        return jsonify({"status": "error", "message": "Bulan dan tahun harus numerik"}), 400
        
    # ─── TAMBAHAN: AMBIL FORMAT OUTLET BERNOMOR DARI INVENTORY.JSON ───
    try:
        with open('inventory.json', 'r', encoding='utf-8') as f:
            import json
            inv = json.load(f)
            outlets_list = inv.get("outlets", [])
            
        # Jika frontend mengirim nama murni tanpa nomor (misal "Selayo"), cocokkan ke JSON agar menjadi "32. Selayo"
        if "." not in outlet:
            outlet = next((o for o in outlets_list if outlet.lower() in o.lower()), outlet)
    except Exception as e:
        print(f"[DEBUG] Gagal membaca inventory.json untuk penomoran outlet: {e}")

    file_info = TEMP_FILES[file_id]
    filepath = file_info['path']
    original_name = file_info['original_name']
    clean_result = file_info['clean_result']
    
    df = clean_result['df']
    date_col = clean_result['date_col']
    product_col = clean_result['product_col']
    qty_col = clean_result['qty_col']
    
    # Load current master products
    master_products = load_master_products()
    if not master_products:
        return jsonify({"status": "error", "message": "Master product list kosong. Isi terlebih dahulu di tab Master Product."}), 400
        
    # Get min and max day of transaction from the actual data
    try:
        valid_dates = df[date_col].dropna()
        df_filtered = df[
            (df[date_col].dt.month == month) &
            (df[date_col].dt.year == year)
        ]

        if not df_filtered.empty:
            min_day = int(df_filtered[date_col].dt.day.min())
            max_day = int(df_filtered[date_col].dt.day.max())
        elif not valid_dates.empty:
            min_day = int(valid_dates.dt.day.min())
            max_day = int(valid_dates.dt.day.max())
        else:
            min_day = 1
            max_day = 30
    except Exception as e:
        try:
            all_dates = pd.to_datetime(df[date_col], errors='coerce').dropna()
            if not all_dates.empty:
                min_day = int(all_dates.dt.day.min())
                max_day = int(all_dates.dt.day.max())
            else:
                min_day = 1
                max_day = 30
        except Exception:
            min_day = 1
            max_day = 30

    tglperiode = f"{min_day:02d}-{max_day:02d}"

    # Generate output file name menggunakan variabel 'outlet' yang sudah diisi nomor otomatis
    output_filename = generate_output_filename(original_name, month, year, outlet, tglperiode)
    output_filepath = os.path.join(config.OUTPUT_FOLDER, output_filename)
    
    try:
        # Run calculation and generator
        generate_excel(
            df=df,
            date_col=date_col,
            product_col=product_col,
            qty_col=qty_col,
            master_products=master_products,
            month=month,
            year=year,
            output_path=output_filepath
        )
        
        # Clean up raw temporary upload file
        cleanup_file(filepath)
        del TEMP_FILES[file_id]
        
        return jsonify({
            "status": "ok",
            "download_url": f"/api/eresto/download/{output_filename}",
            "filename": output_filename,
            "message": "Analisa excel penjualan berhasil digenerate!"
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": f"Gagal memproses data: {str(e)}"}), 500

@eresto_bp.route('/api/eresto/download/<filename>')
def download_output(filename):
    """Download the output file from output folder."""
    # Prevent directory traversal
    filename = os.path.basename(filename)
    return send_from_directory(config.OUTPUT_FOLDER, filename, as_attachment=True)

# ─── MASTER PRODUCT ENDPOINTS ───────────────────────────────────────────────

@eresto_bp.route('/api/eresto/master-product', methods=['GET'])
def get_master_products():
    """Retrieve master product list."""
    return jsonify({"products": load_master_products()})

@eresto_bp.route('/api/eresto/master-product', methods=['POST'])
def update_master_products_list():
    """Replace entire master product list."""
    data = request.json or {}
    products = data.get('products', [])
    updated = reorder_products(products)
    return jsonify({"status": "ok", "products": updated})

@eresto_bp.route('/api/eresto/master-product/add', methods=['POST'])
def add_master_product_item():
    """Add item to master product list."""
    data = request.json or {}
    name = data.get('name', '').strip()
    if not name:
        return jsonify({"status": "error", "message": "Nama product tidak boleh kosong"}), 400
    updated = add_product(name)
    return jsonify({"status": "ok", "products": updated})

@eresto_bp.route('/api/eresto/master-product/remove', methods=['POST'])
def remove_master_product_item():
    """Remove item from master product list."""
    data = request.json or {}
    name = data.get('name', '').strip()
    updated = remove_product(name)
    return jsonify({"status": "ok", "products": updated})
