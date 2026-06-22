import os
import json
from flask import request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
from config import UPLOAD_FOLDER, OUTPUT_FOLDER

from . import mass_update_bp
from .processor import proses_mass_update

JSON_PATH = os.path.join("data", "mass_formulas.json")

progress_tracker = {}

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

@mass_update_bp.route('/api/mass-update/progress/<job_id>', methods=['GET'])
def get_progress(job_id):
    data = progress_tracker.get(job_id, {"total": 0, "current": 0, "status": "unknown"})
    return jsonify(data)

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

    job_id = request.form.get('job_id', 'default_job')
    progress_tracker[job_id] = {'total': len(uploaded_files), 'current': 0, 'status': 'running'}

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

        output_filename, success_count, fail_count, errors = proses_mass_update(
            file_paths=saved_paths,
            formulas=formulas,
            output_folder=OUTPUT_FOLDER,
            job_id=job_id,
            progress_tracker=progress_tracker
        )
            
        return jsonify({
            "status": "ok",
            "message": f"Proses selesai. {success_count} berhasil, {fail_count} gagal.",
            "download_url": f"/api/mass-update/download/{output_filename}",
            "filename": output_filename,
            "success_count": success_count,
            "fail_count": fail_count,
            "errors": errors
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": f"Terjadi kesalahan: {str(e)}"}), 500
    finally:
        if job_id in progress_tracker:
            progress_tracker[job_id]['status'] = 'completed'
            
        for p in saved_paths:
            if os.path.exists(p):
                try:
                    os.remove(p)
                except:
                    pass

@mass_update_bp.route('/api/mass-update/download/<filename>')
def download_mass_update_output(filename):
    filename = secure_filename(filename)
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)
