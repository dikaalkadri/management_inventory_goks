"""
Flask Blueprint Routes for Sales & Loss Synchronization.
Handles page rendering, catalog CRUD, and the synchronization execution API.
"""
import os
from flask import Blueprint, request, jsonify, render_template, send_from_directory, current_app
from werkzeug.utils import secure_filename

from services.catalog_service import load_master_catalog, save_master_catalog
from modules.stockin.helpers import convert_to_xlsx_if_needed
from modules.sinkronisasi.processor import proses_sinkronisasi_excel

sinkronisasi_bp = Blueprint('sinkronisasi', __name__, template_folder='../../templates')

@sinkronisasi_bp.route('/sinkronisasi')
def sinkronisasi_page():
    return render_template('sinkronisasi_penjualan.html')

@sinkronisasi_bp.route('/api/catalog/list', methods=['GET'])
def api_get_catalog():
    return jsonify({"status": "ok", "catalog": load_master_catalog()})

@sinkronisasi_bp.route('/api/catalog/save-all', methods=['POST'])
def api_save_catalog_all():
    data = request.json or {}
    updated_catalog = data.get('catalog', [])
    for item in updated_catalog:
        if not item.get('product', '').strip() or not item.get('category', '').strip():
            return jsonify({"status": "error", "message": "Nama produk dan kategori tidak boleh kosong!"}), 400
        try:
            item['price'] = float(item.get('price', 0))
        except:
            item['price'] = 0.0
        
    ok, msg = save_master_catalog(updated_catalog)
    if not ok:
        return jsonify({"status": "error", "message": msg}), 500
    return jsonify({"status": "ok", "message": "Perubahan katalog berhasil disimpan."})

@sinkronisasi_bp.route('/api/catalog/add', methods=['POST'])
def api_add_catalog_item():
    data = request.json or {}
    product = data.get('product', '').strip()
    category = data.get('category', '').strip()
    price = data.get('price', 0)
    
    if not product or not category:
        return jsonify({"status": "error", "message": "Nama produk dan kategori wajib diisi!"}), 400
    catalog = load_master_catalog()
    if any(item['product'].lower() == product.lower() for item in catalog):
        return jsonify({"status": "error", "message": "Produk sudah ada!"}), 400
    try:
        price = float(price)
    except:
        price = 0.0
    
    catalog.append({"product": product, "category": category, "price": price})
    save_master_catalog(catalog)
    return jsonify({"status": "ok", "message": "Produk berhasil ditambahkan!", "catalog": catalog})

@sinkronisasi_bp.route('/api/catalog/delete', methods=['POST'])
def api_delete_catalog_item():
    data = request.json or {}
    product_name = data.get('product', '').strip()
    catalog = load_master_catalog()
    new_catalog = [item for item in catalog if item['product'].lower() != product_name.lower()]
    save_master_catalog(new_catalog)
    return jsonify({"status": "ok", "message": "Produk dihapus dari master katalog.", "catalog": new_catalog})

@sinkronisasi_bp.route('/api/sinkronisasi/proses', methods=['POST'])
def proses_sinkronisasi():
    if 'file_sumber' not in request.files or 'file_tujuan' not in request.files:
        return jsonify({"status": "error", "message": "File sumber dan tujuan wajib diunggah"}), 400
        
    file_sumber = request.files['file_sumber']
    file_tujuan = request.files['file_tujuan']
    outlet = request.form.get('outlet', '').strip()
    
    if not outlet:
        return jsonify({"status": "error", "message": "Warning: Outlet wajib dipilih!"}), 400
        
    from config import UPLOAD_FOLDER, OUTPUT_FOLDER
    sumber_filename = secure_filename(file_sumber.filename)
    tujuan_filename = secure_filename(file_tujuan.filename)
    sumber_path = os.path.join(UPLOAD_FOLDER, f"sumber_{sumber_filename}")
    tujuan_path = os.path.join(UPLOAD_FOLDER, f"tujuan_{tujuan_filename}")
    
    sumber_path_xlsx = None
    tujuan_path_xlsx = None
    
    try:
        file_sumber.save(sumber_path)
        file_tujuan.save(tujuan_path)
        sumber_path_xlsx = convert_to_xlsx_if_needed(sumber_path)
        tujuan_path_xlsx = convert_to_xlsx_if_needed(tujuan_path)
        
        # Panggil processor utama sinkronisasi
        output_filename, updated_sheets_count = proses_sinkronisasi_excel(
            sumber_path_xlsx=sumber_path_xlsx,
            tujuan_path_xlsx=tujuan_path_xlsx,
            outlet=outlet,
            output_folder=OUTPUT_FOLDER
        )
            
        return jsonify({
            "status": "ok",
            "message": f"Sinkronisasi berhasil! Fitur Auto-Merge Vertikal aktif. {updated_sheets_count} sheet diperbarui.",
            "download_url": f"/api/sinkronisasi/download/{output_filename}",
            "filename": output_filename,
            "updated_sheets_count": updated_sheets_count
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": f"File gagal diproses: {str(e)}"}), 500
    finally:
        for p in [sumber_path, sumber_path_xlsx, tujuan_path, tujuan_path_xlsx]:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except:
                    pass

@sinkronisasi_bp.route('/api/sinkronisasi/download/<filename>')
def download_sinkronisasi_output(filename):
    filename = os.path.basename(filename)
    from config import OUTPUT_FOLDER
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)
