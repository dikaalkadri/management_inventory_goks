"""
routes.py – Add Stock Auth Blueprint
"""
import os
from flask import Blueprint, render_template, request, jsonify, send_from_directory
import config

from . import add_stock_auth_bp
from .processor import process_add_stock_auth
from services.task_manager import start_task


@add_stock_auth_bp.route('/add-stock-auth')
def add_stock_auth_page():
    return render_template('add_stock_auth.html')


@add_stock_auth_bp.route('/api/add-stock-auth/proses', methods=['POST'])
def api_proses_add_stock_auth():
    if 'so_file' not in request.files:
        return jsonify({
            'status': 'error',
            'message': 'File SO Drive wajib diunggah'
        }), 400


    so_file = request.files.get('so_file')
    

    try:
        so_bytes = so_file.read()
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Gagal membaca file: {str(e)}'
        }), 500

    try:
        task_id = start_task(
            'add_stock_auth',
            process_add_stock_auth,
            so_bytes=so_bytes,
            
            output_folder=config.OUTPUT_FOLDER
        )
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Gagal memulai proses: {str(e)}'
        }), 500

    return jsonify({
        'status': 'ok',
        'message': 'Proses Add Stock Auth dimulai di background.',
        'task_id': task_id
    })


@add_stock_auth_bp.route('/api/add-stock-auth/download/<filename>')
def download_add_stock_auth(filename):
    filename = os.path.basename(filename)
    return send_from_directory(config.OUTPUT_FOLDER, filename, as_attachment=True)
