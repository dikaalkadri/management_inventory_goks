import os
import json
import tempfile
from datetime import datetime
from flask import render_template, request, jsonify, send_file, current_app

from . import push_gudang_bp
from .processor import (
    load_schedules,
    save_schedules,
    analyze_push_recommendations,
    export_push_recommendation_excel,
    DAYS_ID
)

# In-memory storage sementara untuk hasil analisis terakhir agar bisa langsung didownload
_LATEST_ANALYSIS = {}

@push_gudang_bp.route('/push-gudang', methods=['GET'])
def index():
    today_str = datetime.now().strftime("%Y-%m-%d")
    schedules = load_schedules()
    return render_template(
        'push_gudang.html',
        active_menu='push_gudang',
        today_str=today_str,
        schedules=schedules,
        days_id=DAYS_ID
    )

@push_gudang_bp.route('/api/push-gudang/schedules', methods=['GET'])
def get_schedules():
    schedules = load_schedules()
    return jsonify({"status": "success", "schedules": schedules})

@push_gudang_bp.route('/api/push-gudang/schedules', methods=['POST'])
def update_schedules():
    try:
        data = request.get_json()
        if not data or 'schedules' not in data:
            return jsonify({"status": "error", "message": "Data schedules tidak valid"}), 400

        ok = save_schedules(data['schedules'])
        if ok:
            return jsonify({"status": "success", "message": "Jadwal outlet berhasil disimpan"})
        else:
            return jsonify({"status": "error", "message": "Gagal menyimpan ke disk"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@push_gudang_bp.route('/api/push-gudang/analyze', methods=['POST'])
def analyze():
    global _LATEST_ANALYSIS
    if 'zip_file' not in request.files:
        return jsonify({"status": "error", "message": "File ZIP belum dipilih"}), 400

    file = request.files['zip_file']
    if not file.filename or not file.filename.lower().endswith('.zip'):
        return jsonify({"status": "error", "message": "Harap unggah file arsip .ZIP"}), 400

    target_date = request.form.get('target_date', datetime.now().strftime("%Y-%m-%d"))
    lookback_days = int(request.form.get('lookback_days', 7))
    buffer_days = int(request.form.get('buffer_days', 1))
    include_all = request.form.get('include_all_outlets', 'false').lower() == 'true'

    try:
        zip_bytes = file.read()
        analysis = analyze_push_recommendations(
            zip_bytes=zip_bytes,
            target_date_str=target_date,
            lookback_days=lookback_days,
            buffer_days=buffer_days,
            include_all_outlets=include_all
        )

        _LATEST_ANALYSIS = analysis

        return jsonify({
            "status": "success",
            "data": analysis
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": f"Terjadi kesalahan analisis: {str(e)}"}), 500

@push_gudang_bp.route('/api/push-gudang/download-excel', methods=['POST', 'GET'])
def download_excel():
    global _LATEST_ANALYSIS
    analysis = _LATEST_ANALYSIS

    # Jika dikirim lewat POST body
    if request.is_json and request.get_json():
        analysis = request.get_json()

    if not analysis or "kpi" not in analysis:
        return jsonify({"status": "error", "message": "Belum ada hasil analisis untuk diekspor"}), 400

    out_dir = os.path.join(current_app.root_path, 'uploads', 'push_output')
    os.makedirs(out_dir, exist_ok=True)

    t_date = analysis.get("target_date", datetime.now().strftime("%Y%m%d"))
    clean_date = t_date.replace("-", "")
    filename = f"Surat_Jalan_Push_Gudang_{clean_date}.xlsx"
    filepath = os.path.join(out_dir, filename)

    try:
        export_push_recommendation_excel(analysis, filepath)
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        return jsonify({"status": "error", "message": f"Gagal membuat file Excel: {str(e)}"}), 500
