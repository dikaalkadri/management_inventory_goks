import os
import zipfile
import pandas as pd
import re
import tempfile
from flask import render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from . import visualisasi_kerugian_bp

@visualisasi_kerugian_bp.route('/visualisasi_kerugian', methods=['GET', 'POST'])
def visualisasi_kerugian():
    if request.method == 'GET':
        return render_template('visualisasi_kerugian.html')
    
    if request.method == 'POST':
        if 'zip_file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['zip_file']
        filter_type = request.form.get('filter_type') # '1' to '31', or 'rekap'
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        if not file.filename.endswith('.zip'):
            return jsonify({'error': 'File must be a ZIP archive'}), 400
            
        # Determine row index based on filter_type
        if filter_type == 'rekap':
            row_index = 33 # Row 34 is index 33 in 0-indexed pandas df
        else:
            try:
                day = int(filter_type)
                if day < 1 or day > 31:
                    return jsonify({'error': 'Invalid date filter'}), 400
                row_index = day + 1 # if day 1 -> row 3 -> index 2
            except ValueError:
                return jsonify({'error': 'Invalid filter'}), 400
                
        results = []
        
        # Save ZIP to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_zip:
            file.save(tmp_zip.name)
            tmp_zip_path = tmp_zip.name
            
        # Extract and process
        with tempfile.TemporaryDirectory() as extract_dir:
            with zipfile.ZipFile(tmp_zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
                
            for root, dirs, files in os.walk(extract_dir):
                for extracted_file in files:
                    if extracted_file.endswith('.xlsx'):
                        # Extract outlet name using regex
                        f_lower = extracted_file.lower()
                        # hapus ekstensi dan tahun
                        name_stripped = re.sub(r'_\d{4}\.xlsx$', '', f_lower)
                        # hapus nama bulan di akhir string
                        name_stripped = re.sub(r'_?(januari|februari|maret|april|mei|juni|juli|agustus|september|oktober|november|desember)$', '', name_stripped)
                        
                        match = re.search(r'kerugian_(\d+)_+(.+)$', name_stripped)
                        if match:
                            sort_id = int(match.group(1))
                            outlet_name = match.group(2).replace('_', ' ').title()
                        else:
                            # Fallback if format is different
                            sort_id = 999
                            outlet_name = extracted_file.replace('.xlsx', '')
                            
                        file_path = os.path.join(root, extracted_file)
                        try:
                            # Read excel file (header=None so we can use integer indexing)
                            # Column D is index 3
                            df = pd.read_excel(file_path, sheet_name='Rekap Kerugian', header=None)
                            
                            if row_index < len(df):
                                val = df.iloc[row_index, 3]
                                
                                # Handle NaN or non-numeric values
                                if pd.isna(val):
                                    kerugian = 0
                                else:
                                    try:
                                        kerugian = float(val)
                                    except ValueError:
                                        kerugian = 0
                            else:
                                kerugian = 0
                                
                            results.append({
                                'sort_id': sort_id,
                                'outlet': outlet_name,
                                'kerugian': kerugian
                            })
                        except Exception as e:
                            print(f"Error reading {extracted_file}: {e}")
                            
        os.remove(tmp_zip_path)
        
        # Sort results by sort_id, then by outlet name
        results = sorted(results, key=lambda x: (x['sort_id'], x['outlet']))
        
        # Clean up sort_id for frontend response
        for r in results:
            del r['sort_id']
        
        # Create output Excel file
        output_df = pd.DataFrame(results)
        # Rename columns for the output file
        output_df.rename(columns={'outlet': 'Nama Outlet', 'kerugian': 'Kerugian'}, inplace=True)
        
        output_dir = 'uploads/visualisasi_output'
        os.makedirs(output_dir, exist_ok=True)
        output_file_path = os.path.join(output_dir, 'hasil_visualisasi_kerugian.xlsx')
        
        output_df.to_excel(output_file_path, index=False)
        
        return jsonify({
            'success': True,
            'data': results,
            'download_url': '/visualisasi_kerugian/download_result'
        })

@visualisasi_kerugian_bp.route('/visualisasi_kerugian/download_result')
def download_result():
    output_file_path = 'uploads/visualisasi_output/hasil_visualisasi_kerugian.xlsx'
    if os.path.exists(output_file_path):
        return send_file(output_file_path, as_attachment=True, download_name='hasil_kerugian.xlsx')
    return "File not found", 404
