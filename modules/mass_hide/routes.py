import os
from flask import request, jsonify, render_template, send_from_directory, Blueprint
from werkzeug.utils import secure_filename
from config import UPLOAD_FOLDER, OUTPUT_FOLDER

mass_hide_bp = Blueprint('mass_hide', __name__)

from .processor import proses_mass_hide

progress_tracker = {}

@mass_hide_bp.route('/mass-hide')
def mass_hide_page():
    return render_template('mass_hide.html')

@mass_hide_bp.route('/api/mass-hide/progress/<job_id>', methods=['GET'])
def get_progress(job_id):
    data = progress_tracker.get(job_id, {"total": 0, "current": 0, "status": "unknown"})
    return jsonify(data)

@mass_hide_bp.route('/api/mass-hide/process', methods=['POST'])
def process_mass_hide():
    if 'files[]' not in request.files:
        return jsonify({"status": "error", "message": "Tidak ada file yang diunggah"}), 400
        
    uploaded_files = request.files.getlist('files[]')
    if not uploaded_files or len(uploaded_files) == 0:
        return jsonify({"status": "error", "message": "Tidak ada file yang diunggah"}), 400

    job_id = request.form.get('job_id', 'default_job')
    progress_tracker[job_id] = {'total': len(uploaded_files), 'current': 0, 'status': 'running'}

    saved_paths = []
    
    try:
        for f in uploaded_files:
            filename = secure_filename(f.filename)
            if not filename.endswith(('.xlsx', '.xls')):
                continue
            path = os.path.join(UPLOAD_FOLDER, f"mh_{filename}")
            f.save(path)
            saved_paths.append(path)
            
        if not saved_paths:
            return jsonify({"status": "error", "message": "Tidak ada file valid yang diunggah (.xlsx/.xls)"}), 400

        output_filename, success_count, fail_count, errors = proses_mass_hide(
            file_paths=saved_paths,
            output_folder=OUTPUT_FOLDER,
            job_id=job_id,
            progress_tracker=progress_tracker
        )
            
        return jsonify({
            "status": "ok",
            "message": f"Proses selesai. {success_count} berhasil, {fail_count} gagal.",
            "download_url": f"/api/mass-hide/download/{output_filename}",
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

@mass_hide_bp.route('/api/mass-hide/download/<filename>')
def download_mass_hide_output(filename):
    filename = secure_filename(filename)
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)
