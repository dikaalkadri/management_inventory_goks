import os
from flask import Blueprint, render_template, request, jsonify, send_from_directory
import config

from . import perbaikan_data_bp
from .processor import process_perbaikan_data
from services.task_manager import start_task

@perbaikan_data_bp.route('/perbaikan-data')
def perbaikan_data_page():
    return render_template('perbaikan_data.html')

@perbaikan_data_bp.route('/api/perbaikan-data/proses', methods=['POST'])
def api_proses_perbaikan_data():
    if 'so_file' not in request.files:
        return jsonify({"status": "error", "message": "File SO Drive wajib diunggah"}), 400
    if 'inv_file' not in request.files:
        return jsonify({"status": "error", "message": "File Inventory Movement wajib diunggah"}), 400
    if 'template_file' not in request.files:
        return jsonify({"status": "error", "message": "Template Adjustment wajib diunggah"}), 400

    so_file = request.files.get('so_file')
    inv_file = request.files.get('inv_file')
    template_file = request.files.get('template_file')

    try:
        so_bytes = so_file.read()
        inv_bytes = inv_file.read()
        template_bytes = template_file.read()
    except Exception as e:
        return jsonify({"status": "error", "message": f"Gagal membaca file: {str(e)}"}), 500

    try:
        task_id = start_task(
            "perbaikan_data",
            process_perbaikan_data,
            so_bytes=so_bytes,
            inv_bytes=inv_bytes,
            template_bytes=template_bytes,
            output_folder=config.OUTPUT_FOLDER
        )
    except Exception as e:
        return jsonify({"status": "error", "message": f"Gagal memulai proses: {str(e)}"}), 500

    return jsonify({
        "status": "ok",
        "message": "Proses perbaikan data dimulai di background.",
        "task_id": task_id
    })

@perbaikan_data_bp.route('/api/perbaikan-data/download/<filename>')
def download_perbaikan_data(filename):
    filename = os.path.basename(filename)
    return send_from_directory(config.OUTPUT_FOLDER, filename, as_attachment=True)
