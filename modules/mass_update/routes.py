import os
import json
from flask import request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
from config import UPLOAD_FOLDER, OUTPUT_FOLDER

from . import mass_update_bp
from .processor import proses_mass_update
from services.task_manager import start_task

JSON_PATH = os.path.join("data", "mass_formulas.json")

def load_mass_formulas():
    if not os.path.exists(JSON_PATH):
        return {}
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_mass_formulas(data):
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

@mass_update_bp.route('/mass-update')
def mass_update_page():
    return render_template('mass_update.html')

@mass_update_bp.route('/api/mass-update/formulas', methods=['GET'])
def get_formulas():
    try:
        formulas = load_mass_formulas()
        return jsonify({"status": "ok", "formulas": formulas})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@mass_update_bp.route('/api/mass-update/formulas', methods=['POST'])
def save_formulas():
    try:
        data = request.json or {}
        # data is expected to be a dictionary of {row_number: {"name": "...", "formula": "..."}}
        if not data:
            return jsonify({"status": "error", "message": "Data tidak boleh kosong"}), 400
        save_mass_formulas(data)
        return jsonify({"status": "ok", "message": "Rumus berhasil disimpan permanen."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@mass_update_bp.route('/api/mass-update/process', methods=['POST'])
def process_mass_update():
    if 'files[]' not in request.files:
        return jsonify({"status": "error", "message": "Tidak ada file yang diunggah"}), 400
        
    uploaded_files = request.files.getlist('files[]')
    if not uploaded_files or len(uploaded_files) == 0:
        return jsonify({"status": "error", "message": "Tidak ada file yang diunggah"}), 400

    formulas = load_mass_formulas()
    if not formulas:
        return jsonify({"status": "error", "message": "Data rumus masih kosong."}), 400

    saved_paths = []
    try:
        for f in uploaded_files:
            filename = secure_filename(f.filename)
            if not filename.endswith(('.xlsx', '.xls')):
                continue
            path = os.path.join(UPLOAD_FOLDER, f"mu_{filename}")
            f.save(path)
            saved_paths.append(path)
            
        if not saved_paths:
            return jsonify({"status": "error", "message": "Tidak ada file valid yang diunggah (.xlsx/.xls)"}), 400

        task_id = start_task(
            "mass_update",
            proses_mass_update,
            file_paths=saved_paths,
            formulas=formulas,
            output_folder=OUTPUT_FOLDER
        )
            
        return jsonify({
            "status": "ok",
            "message": "Proses mass update dimulai di background.",
            "task_id": task_id
        })
        
    except Exception as e:
        # Jika error sebelum start_task, hapus file yang sudah ter-save
        for p in saved_paths:
            if os.path.exists(p):
                try:
                    os.remove(p)
                except:
                    pass
        return jsonify({"status": "error", "message": f"Terjadi kesalahan: {str(e)}"}), 500

@mass_update_bp.route('/api/mass-update/download/<filename>')
def download_mass_update_output(filename):
    filename = secure_filename(filename)
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)
