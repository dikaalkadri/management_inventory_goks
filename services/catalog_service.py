import os
import json

POS_PATH = 'master_pos.json'
MATERIALS_PATH = 'master_materials.json'

def load_pos():
    if not os.path.exists(POS_PATH):
        return []
    try:
        with open(POS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('pos_items', []) if isinstance(data, dict) else data
    except Exception as e:
        print(f"[ERROR] Gagal memuat pos: {e}")
        return []

def save_pos(items):
    try:
        with open(POS_PATH, 'w', encoding='utf-8') as f:
            json.dump({"pos_items": items}, f, ensure_ascii=False, indent=2)
        return True, "Daftar Menu POS berhasil disimpan."
    except Exception as e:
        return False, f"Gagal menyimpan POS: {str(e)}"

def load_materials():
    if not os.path.exists(MATERIALS_PATH):
        return []
    try:
        with open(MATERIALS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('materials', []) if isinstance(data, dict) else data
    except Exception as e:
        print(f"[ERROR] Gagal memuat materials: {e}")
        return []

def save_materials(items):
    try:
        with open(MATERIALS_PATH, 'w', encoding='utf-8') as f:
            json.dump({"materials": items}, f, ensure_ascii=False, indent=2)
        return True, "Daftar Bahan Baku berhasil disimpan."
    except Exception as e:
        return False, f"Gagal menyimpan Bahan Baku: {str(e)}"

def get_catalog_maps():
    """Menghasilkan dictionary map untuk mempermudah pencarian O(1) saat sinkronisasi."""
    pos_items = load_pos()
    materials = load_materials()
    
    category_map = {}
    for item in pos_items:
        prod_name = item.get('product', '').strip()
        if prod_name:
            category_map[prod_name.upper()] = item.get('category', '')
            
    price_map = {}
    for item in materials:
        mat_name = item.get('name', '').strip()
        if mat_name:
            price_map[mat_name.upper()] = float(item.get('price', 0))
            
    return pos_items, category_map, price_map