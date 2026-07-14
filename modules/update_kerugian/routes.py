import os
from flask import Blueprint, render_template, request, jsonify, send_from_directory
import config

from . import update_kerugian_bp
from .processor import process_update_kerugian

@update_kerugian_bp.route('/update-kerugian')
def update_kerugian_page():
    return render_template('update_kerugian.html')

@update_kerugian_bp.route('/api/update-kerugian/proses', methods=['POST'])
def api_proses_update_kerugian():
    if 'eresto_zip' not in request.files:
        return jsonify({"status": "error", "message": "File ZIP eResto wajib diunggah"}), 400
    if 'so_zip' not in request.files:
        return jsonify({"status": "error", "message": "File ZIP SO Drive wajib diunggah"}), 400
    if 'kerugian_zip' not in request.files:
        return jsonify({"status": "error", "message": "File ZIP Kerugian Lama wajib diunggah"}), 400

    eresto_file = request.files.get('eresto_zip')
    so_file = request.files.get('so_zip')
    kerugian_file = request.files.get('kerugian_zip')

    if not eresto_file.filename.lower().endswith('.zip'):
        return jsonify({"status": "error", "message": "File eResto harus berupa .zip"}), 400
    if not so_file.filename.lower().endswith('.zip'):
        return jsonify({"status": "error", "message": "File SO Drive harus berupa .zip"}), 400
    if not kerugian_file.filename.lower().endswith('.zip'):
        return jsonify({"status": "error", "message": "File Kerugian Lama harus berupa .zip"}), 400

    try:
        eresto_bytes = eresto_file.read()
        so_bytes = so_file.read()
        kerugian_bytes = kerugian_file.read()
    except Exception as e:
        return jsonify({"status": "error", "message": f"Gagal membaca file: {str(e)}"}), 500

    try:
        result = process_update_kerugian(
            eresto_zip_bytes=eresto_bytes,
            so_zip_bytes=so_bytes,
            kerugian_zip_bytes=kerugian_bytes,
            output_folder=config.OUTPUT_FOLDER
        )
    except Exception as e:
        return jsonify({"status": "error", "message": f"Proses gagal: {str(e)}"}), 500

    if result['processed'] == 0 and not result['errors']:
        return jsonify({
            "status": "error",
            "message": "Tidak ada outlet yang dapat diproses. Periksa isi file ZIP.",
            **result,
        }), 422

    download_url = None
    if result['zip_filename']:
        download_url = f"/api/update-kerugian/download/{result['zip_filename']}"

    return jsonify({
        "status": "ok",
        "message": f"Selesai! {result['processed']} outlet berhasil diupdate.",
        "download_url": download_url,
        **result,
    })

@update_kerugian_bp.route('/api/update-kerugian/download/<filename>')
def download_update_kerugian(filename):
    filename = os.path.basename(filename)
    return send_from_directory(config.OUTPUT_FOLDER, filename, as_attachment=True)
