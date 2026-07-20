import uuid
import threading
import traceback
from flask import Blueprint, jsonify

task_bp = Blueprint('task', __name__)

# In-memory storage for active tasks
# { task_id: { "status": "running"|"completed"|"error", "progress": int, "total": int, "current_item": str, "message": str, "result": dict, "errors": list } }
active_tasks = {}

def start_task(task_type, target_func, **kwargs):
    """
    Menjalankan proses secara asinkron di background thread.
    task_type: string unik untuk prefix task_id (e.g. 'mass_sinko')
    target_func: fungsi processor yang akan dijalankan
    kwargs: parameter yang akan dipass ke target_func
    
    Returns: task_id (string)
    """
    task_id = f"{task_type}_{uuid.uuid4().hex[:8]}"
    active_tasks[task_id] = {
        "status": "running",
        "progress": 0,
        "total": 0,
        "current_item": "Memulai...",
        "message": "Menginisialisasi task",
        "result": None,
        "errors": []
    }
    
    def run():
        try:
            # Fungsi processor harus menerima parameter 'task_id' untuk update progress
            result = target_func(task_id=task_id, **kwargs)
            
            # Jika target_func berjalan normal, pastikan status akhirnya diset ke completed
            active_tasks[task_id]["status"] = "completed"
            active_tasks[task_id]["result"] = result
            active_tasks[task_id]["message"] = "Proses selesai."
        except Exception as e:
            traceback.print_exc()
            active_tasks[task_id]["status"] = "error"
            active_tasks[task_id]["message"] = f"Error: {str(e)}"
            
    # Spawn background thread
    thread = threading.Thread(target=run)
    thread.daemon = True
    thread.start()
    
    return task_id

@task_bp.route('/api/task/status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """
    Endpoint untuk polling status task dari frontend.
    """
    task_info = active_tasks.get(task_id)
    if not task_info:
        return jsonify({"status": "not_found", "message": "Task ID tidak ditemukan atau sudah dihapus."}), 404
        
    # Return seluruh dictionary task_info
    return jsonify(task_info)
