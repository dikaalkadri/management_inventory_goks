"""
Mass Sinkronisasi Blueprint Routes.

Endpoints:
  GET  /mass-sinkronisasi        → halaman UI
  POST /api/mass-sinkronisasi/proses  → proses batch semua outlet
  GET  /api/mass-sinkronisasi/download/<filename>  → download ZIP hasil
"""
import os
from flask import Blueprint, render_template, request, jsonify, send_from_directory

import config
from modules.mass_sinko.processor import process_mass_sinkronisasi
from services.file_handler import save_upload, cleanup_file
from services.task_manager import start_task
from modules.eresto_mass.cleaner import clean_mass_data
from modules.eresto_mass.processor import process_mass_to_zip

mass_sinko_bp = Blueprint('mass_sinko', __name__, template_folder='../../templates')


@mass_sinko_bp.route('/mass-sinkronisasi')
def mass_sinko_page():
    """Render halaman Mass Sinkronisasi."""
    return render_template('mass_sinkronisasi_massal.html')


@mass_sinko_bp.route('/api/mass-sinkronisasi/proses', methods=['POST'])
def api_proses_mass_sinko():
    """
    Proses mass sinkronisasi semua outlet.

    Form-data:
      eresto_zip  : file ZIP hasil eResto Mass Analysis
      so_zip      : file ZIP berisi semua file SO per outlet
      bulan       : nama bulan (mis: "juli")
      tahun       : tahun (mis: "2026")
    """
    # ── Validasi input ──────────────────────────────────────────────────
    if 'eresto_zip' not in request.files and 'eresto_raw' not in request.files:
        return jsonify({"status": "error", "message": "File eResto (ZIP atau Raw XLSX) wajib diunggah"}), 400
    if 'so_zip' not in request.files:
        return jsonify({"status": "error", "message": "File ZIP SO wajib diunggah"}), 400

    bulan = request.form.get('bulan', '').strip().lower()
    tahun = request.form.get('tahun', '').strip()

    if not bulan or not tahun:
        return jsonify({"status": "error", "message": "Parameter bulan dan tahun wajib diisi"}), 400

    eresto_file = request.files.get('eresto_zip')
    eresto_raw  = request.files.get('eresto_raw')
    so_file     = request.files.get('so_zip')

    if not so_file.filename.lower().endswith('.zip'):
        return jsonify({"status": "error", "message": "SO ZIP harus berupa file .zip"}), 400

    eresto_zip_bytes = None
    temp_files = []

    try:
        # If raw xlsx is provided (n8n workflow)
        if eresto_raw:
            ext = eresto_raw.filename.lower()
            if not (ext.endswith('.xlsx') or ext.endswith('.xls')):
                return jsonify({"status": "error", "message": "File Raw eResto harus berupa .xlsx atau .xls"}), 400
            
            # 1. Save upload temporarily
            raw_path, _ = save_upload(eresto_raw, subfolder='mass_sinko_raw')
            temp_files.append(raw_path)
            
            # 2. Clean data
            clean_result = clean_mass_data(raw_path)
            
            # 3. Process into zip
            import uuid, tempfile
            temp_zip_path = os.path.join(tempfile.gettempdir(), f"temp_eresto_{uuid.uuid4().hex}.zip")
            temp_files.append(temp_zip_path)
            
            process_mass_to_zip(
                df=clean_result['df'],
                date_col=clean_result['date_col'],
                outlet_col=clean_result['outlet_col'],
                product_col=clean_result['product_col'],
                qty_col=clean_result['qty_col'],
                zip_output_path=temp_zip_path
            )
            
            # 4. Read bytes
            with open(temp_zip_path, 'rb') as f:
                eresto_zip_bytes = f.read()
            
            # 5. Cleanup temp files immediately
            for temp_file in temp_files:
                try:
                    os.remove(temp_file)
                except:
                    pass
                
        # If standard zip is provided (Web UI)
        elif eresto_file:
            if not eresto_file.filename.lower().endswith('.zip'):
                return jsonify({"status": "error", "message": "eResto ZIP harus berupa file .zip"}), 400
            eresto_zip_bytes = eresto_file.read()

        so_zip_bytes = so_file.read()
    except Exception as e:
        return jsonify({"status": "error", "message": f"Gagal membaca file: {str(e)}"}), 500

    # ── Proses ─────────────────────────────────────────────────────────
    try:
        task_id = start_task(
            "mass_sinko",
            process_mass_sinkronisasi,
            eresto_zip_bytes=eresto_zip_bytes,
            so_zip_bytes=so_zip_bytes,
            bulan=bulan,
            tahun=tahun,
            output_folder=config.OUTPUT_FOLDER,
        )
    except Exception as e:
        return jsonify({"status": "error", "message": f"Gagal memulai proses: {str(e)}"}), 500

    return jsonify({
        "status": "ok",
        "message": "Proses sinkronisasi dimulai di background.",
        "task_id": task_id
    })


@mass_sinko_bp.route('/api/mass-sinkronisasi/download/<filename>')
def download_mass_sinko(filename):
    """Download ZIP hasil mass sinkronisasi."""
    filename = os.path.basename(filename)
    return send_from_directory(config.OUTPUT_FOLDER, filename, as_attachment=True)
