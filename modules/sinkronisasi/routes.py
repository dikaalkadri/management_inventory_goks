"""
Flask Blueprint Routes for Sales & Loss Synchronization.
Handles page rendering, catalog CRUD, and the synchronization execution API.
"""
import os
from flask import Blueprint, request, jsonify, render_template, send_from_directory, current_app
from werkzeug.utils import secure_filename

from services.catalog_service import load_pos, save_pos, load_materials, save_materials
from modules.stockin.helpers import convert_to_xlsx_if_needed
from modules.sinkronisasi.processor import proses_sinkronisasi_excel

sinkronisasi_bp = Blueprint('sinkronisasi', __name__, template_folder='../../templates')

@sinkronisasi_bp.route('/sinkronisasi')
def sinkronisasi_page():
    return render_template('sinkronisasi_penjualan.html')

# --- POS ROUTES ---
@sinkronisasi_bp.route('/api/pos/list', methods=['GET'])
def api_get_pos():
    return jsonify({"status": "ok", "items": load_pos()})

@sinkronisasi_bp.route('/api/pos/save-all', methods=['POST'])
def api_save_pos_all():
    data = request.json or {}
    updated_items = data.get('items', [])
    for item in updated_items:
        if not item.get('product', '').strip() or not item.get('category', '').strip():
            return jsonify({"status": "error", "message": "Nama produk dan kategori tidak boleh kosong!"}), 400
        
    ok, msg = save_pos(updated_items)
    if not ok:
        return jsonify({"status": "error", "message": msg}), 500
    return jsonify({"status": "ok", "message": "Menu POS berhasil disimpan."})

@sinkronisasi_bp.route('/api/pos/add', methods=['POST'])
def api_add_pos_item():
    data = request.json or {}
    product = data.get('product', '').strip()
    category = data.get('category', '').strip()
    
    if not product or not category:
        return jsonify({"status": "error", "message": "Nama produk dan kategori wajib diisi!"}), 400
    items = load_pos()
    if any(item['product'].lower() == product.lower() for item in items):
        return jsonify({"status": "error", "message": "Produk sudah ada!"}), 400
    
    items.append({"product": product, "category": category})
    save_pos(items)
    return jsonify({"status": "ok", "message": "Menu POS ditambahkan!", "items": items})

@sinkronisasi_bp.route('/api/pos/delete', methods=['POST'])
def api_delete_pos_item():
    data = request.json or {}
    product_name = data.get('product', '').strip()
    items = load_pos()
    new_items = [item for item in items if item.get('product', '').lower() != product_name.lower()]
    save_pos(new_items)
    return jsonify({"status": "ok", "message": "Menu POS dihapus.", "items": new_items})


# --- MATERIALS ROUTES ---
@sinkronisasi_bp.route('/api/materials/list', methods=['GET'])
def api_get_materials():
    return jsonify({"status": "ok", "items": load_materials()})

@sinkronisasi_bp.route('/api/materials/save-all', methods=['POST'])
def api_save_materials_all():
    data = request.json or {}
    updated_items = data.get('items', [])
    for item in updated_items:
        if not item.get('name', '').strip() or not item.get('category', '').strip():
            return jsonify({"status": "error", "message": "Nama bahan dan kategori tidak boleh kosong!"}), 400
        try:
            item['price'] = float(item.get('price', 0))
        except:
            item['price'] = 0.0
        
    ok, msg = save_materials(updated_items)
    if not ok:
        return jsonify({"status": "error", "message": msg}), 500
    return jsonify({"status": "ok", "message": "Bahan Baku berhasil disimpan."})

@sinkronisasi_bp.route('/api/materials/add', methods=['POST'])
def api_add_materials_item():
    data = request.json or {}
    name = data.get('name', '').strip()
    category = data.get('category', '').strip()
    price = data.get('price', 0)
    
    if not name or not category:
        return jsonify({"status": "error", "message": "Nama bahan dan kategori wajib diisi!"}), 400
    items = load_materials()
    if any(item['name'].lower() == name.lower() for item in items):
        return jsonify({"status": "error", "message": "Bahan sudah ada!"}), 400
    try:
        price = float(price)
    except:
        price = 0.0
    
    items.append({"name": name, "category": category, "price": price})
    save_materials(items)
    return jsonify({"status": "ok", "message": "Bahan ditambahkan!", "items": items})

@sinkronisasi_bp.route('/api/materials/delete', methods=['POST'])
def api_delete_materials_item():
    data = request.json or {}
    name = data.get('name', '').strip()
    items = load_materials()
    new_items = [item for item in items if item.get('name', '').lower() != name.lower()]
    save_materials(new_items)
    return jsonify({"status": "ok", "message": "Bahan dihapus.", "items": new_items})


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
