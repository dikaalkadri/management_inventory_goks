"""
routes.py – Add Stock Auth Blueprint
"""
import os
import json
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


@add_stock_auth_bp.route('/api/add-stock-auth/outlets', methods=['GET'])
def api_get_outlets():
    json_path = os.path.join('data', 'add_stock_outlets.json')
    try:
        with open(json_path, 'r') as f:
            outlets = json.load(f)
        return jsonify({'status': 'ok', 'outlets': outlets})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@add_stock_auth_bp.route('/api/add-stock-auth/outlets', methods=['POST'])
def api_save_outlets():
    json_path = os.path.join('data', 'add_stock_outlets.json')
    try:
        data = request.json
        if not data or 'outlets' not in data:
            return jsonify({'status': 'error', 'message': 'Invalid payload'}), 400
        
        outlets = data['outlets']
        if not isinstance(outlets, list):
            return jsonify({'status': 'error', 'message': 'Outlets must be a list'}), 400
            
        with open(json_path, 'w') as f:
            json.dump(outlets, f, indent=4)
            
        return jsonify({'status': 'ok', 'message': 'Outlets saved successfully.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
