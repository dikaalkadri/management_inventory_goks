"""
eResto Mass Analysis Blueprint Routes.

Handles HTTP endpoints for:
- Uploading combined eResto order reports (all outlets in one file)
- Previewing detected outlets & data statistics
- Processing all outlets → generating one Excel per outlet → ZIP download
"""
import os
import uuid

from flask import Blueprint, render_template, request, jsonify, send_from_directory

import config
from services.file_handler import save_upload, cleanup_file
from modules.eresto_mass.cleaner import clean_mass_data
from modules.eresto_mass.processor import process_mass_to_zip

eresto_mass_bp = Blueprint('eresto_mass', __name__, template_folder='../../templates')

# In-memory store: file_id -> { path, original_name, clean_result }
TEMP_FILES = {}


@eresto_mass_bp.route('/eresto-mass')
def index():
    """Render the eResto Mass Analysis page."""
    return render_template('eresto_mass_analysis.html')


# ─── UPLOAD ──────────────────────────────────────────────────────────────────

@eresto_mass_bp.route('/api/eresto-mass/upload', methods=['POST'])
def upload_file():
    """Upload combined eResto Excel and return preview statistics."""
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "Tidak ada file yang diunggah"}), 400

    file_storage = request.files['file']
    try:
        filepath, original_name = save_upload(file_storage, subfolder='eresto_mass_raw')

        clean_result = clean_mass_data(filepath)

        file_id = str(uuid.uuid4())
        TEMP_FILES[file_id] = {
            'path': filepath,
            'original_name': original_name,
            'clean_result': clean_result,
        }

        df_clean = clean_result['df']
        date_col = clean_result['date_col']
        outlet_col = clean_result['outlet_col']
        product_col = clean_result['product_col']
        qty_col = clean_result['qty_col']

        # Build per-outlet summary for preview
        outlet_summaries = []
        for raw_outlet in clean_result['unique_outlets']:
            df_o = df_clean[df_clean[outlet_col].astype(str) == raw_outlet]
            valid_dates = df_o[date_col].dropna()
            if valid_dates.empty:
                date_range_o = '-'
            else:
                date_range_o = (
                    f"{valid_dates.min().strftime('%d/%m/%Y')} – "
                    f"{valid_dates.max().strftime('%d/%m/%Y')}"
                )
            outlet_summaries.append({
                'outlet': raw_outlet,
                'rows': len(df_o),
                'date_range': date_range_o,
            })

        return jsonify({
            "status": "ok",
            "file_id": file_id,
            "filename": original_name,
            "total_rows_raw": clean_result['total_rows_raw'],
            "total_rows_clean": clean_result['total_rows_clean'],
            "outlet_count": len(clean_result['unique_outlets']),
            "unique_products_count": len(clean_result['unique_products']),
            "date_range": clean_result['date_range'],
            "outlet_summaries": outlet_summaries,
        })

    except Exception as e:
        return jsonify({"status": "error", "message": f"Gagal mengunggah file: {str(e)}"}), 500


# ─── PROCESS ─────────────────────────────────────────────────────────────────

@eresto_mass_bp.route('/api/eresto-mass/process', methods=['POST'])
def process_data():
    """Process all outlets, generate Excel per outlet, return ZIP download link."""
    data = request.json or {}
    file_id = data.get('file_id')

    if not file_id:
        return jsonify({"status": "error", "message": "Parameter file_id tidak ditemukan"}), 400

    if file_id not in TEMP_FILES:
        return jsonify({"status": "error", "message": "Data upload kadaluwarsa atau tidak ditemukan"}), 404

    file_info = TEMP_FILES[file_id]
    filepath = file_info['path']
    clean_result = file_info['clean_result']

    df = clean_result['df']
    date_col = clean_result['date_col']
    outlet_col = clean_result['outlet_col']
    product_col = clean_result['product_col']
    qty_col = clean_result['qty_col']

    # Build ZIP filename based on overall date range
    date_range = clean_result['date_range']
    if date_range and date_range[0]:
        zip_name = f"eResto_Mass_Analysis_{date_range[0].replace('/', '-')}_sd_{date_range[1].replace('/', '-')}.zip"
    else:
        zip_name = f"eResto_Mass_Analysis_{uuid.uuid4().hex[:8]}.zip"

    zip_output_path = os.path.join(config.OUTPUT_FOLDER, zip_name)

    try:
        result = process_mass_to_zip(
            df=df,
            date_col=date_col,
            outlet_col=outlet_col,
            product_col=product_col,
            qty_col=qty_col,
            zip_output_path=zip_output_path,
        )

        # Cleanup raw upload
        cleanup_file(filepath)
        del TEMP_FILES[file_id]

        return jsonify({
            "status": "ok",
            "download_url": f"/api/eresto-mass/download/{zip_name}",
            "filename": zip_name,
            "file_count": result['file_count'],
            "outlets_processed": result['outlets_processed'],
            "outlets_skipped": result['outlets_skipped'],
            "message": f"Berhasil generate {result['file_count']} file Excel dalam 1 ZIP!",
        })

    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"Gagal memproses data: {str(e)}"}), 500


# ─── DOWNLOAD ────────────────────────────────────────────────────────────────

@eresto_mass_bp.route('/api/eresto-mass/download/<filename>')
def download_output(filename):
    """Download the generated ZIP file."""
    filename = os.path.basename(filename)
    return send_from_directory(config.OUTPUT_FOLDER, filename, as_attachment=True)
