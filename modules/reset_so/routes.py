import os
from flask import Blueprint, render_template, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
import openpyxl
from io import BytesIO

reset_so_bp = Blueprint('reset_so', __name__)

@reset_so_bp.route('/reset-so', methods=['GET'])
def reset_so_page():
    return render_template('reset_so.html', active_menu='reset_so')

@reset_so_bp.route('/api/reset-so', methods=['POST'])
def process_reset_so():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'Tidak ada file yang diunggah'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'Tidak ada file yang dipilih'}), 400
        
    if not file.filename.endswith(('.xlsx', '.xlsm')):
        return jsonify({'status': 'error', 'message': 'File harus berupa Excel (.xlsx)'}), 400

    filename = secure_filename(file.filename)
    
    try:
        # Load workbook (data_only=False untuk mempertahankan rumus)
        wb = openpyxl.load_workbook(file, data_only=False)
        
        # Kolom-kolom yang harus dihapus di semua sheet
        # A=1, B=2, C=3, D=4, E=5, F=6, G=7, H=8, ..., Q=17
        cols_to_clear_all = [3, 5, 6, 7, 8, 17] # C, E, F, G, H, Q
        
        sheet_count = len(wb.sheetnames)
        processed_sheets = 0
        
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            processed_sheets += 1
            
            # Tentukan target kolom untuk sheet ini
            target_cols = list(cols_to_clear_all)
            if sheet_name == "01":
                target_cols.append(4) # Tambahkan D untuk sheet "01"
            
            # Kita hanya ingin menghapus data input, biasanya mulai dari baris setelah header.
            # Berhubung tidak tahu baris pastinya, kita asumsikan mulai baris 2 hingga akhir
            max_row = ws.max_row
            
            # Mengosongkan nilai pada kolom yang dituju
            for row in range(2, max_row + 1):
                for col in target_cols:
                    # Clear value tapi pertahankan format
                    ws.cell(row=row, column=col).value = None

        # Simpan hasil ke BytesIO agar bisa langsung didownload / atau disave ke disk
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        # Simpan ke folder output/temp
        output_dir = os.path.join(current_app.root_path, 'output', 'reset_so')
        os.makedirs(output_dir, exist_ok=True)
        
        output_filename = f"SO_Reset_{filename}"
        output_filepath = os.path.join(output_dir, output_filename)
        
        with open(output_filepath, 'wb') as f:
            f.write(output.getvalue())
            
        return jsonify({
            'status': 'success',
            'message': 'File SO berhasil di-reset',
            'data': {
                'original_filename': file.filename,
                'output_filename': output_filename,
                'sheet_count': sheet_count,
                'processed_sheets': processed_sheets,
                'download_url': f'/api/reset-so/download/{output_filename}'
            }
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Gagal memproses file: {str(e)}'}), 500

@reset_so_bp.route('/api/reset-so/download/<filename>', methods=['GET'])
def download_reset_so(filename):
    output_dir = os.path.join(current_app.root_path, 'output', 'reset_so')
    filepath = os.path.join(output_dir, filename)
    
    if not os.path.exists(filepath):
        return jsonify({'status': 'error', 'message': 'File tidak ditemukan'}), 404
        
    return send_file(
        filepath,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
