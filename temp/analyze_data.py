import pandas as pd
import json
import numpy as np

def clean_dict(d):
    # Convert numpy types to python native types
    if isinstance(d, dict):
        return {str(k): clean_dict(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [clean_dict(i) for i in d]
    elif isinstance(d, (int, float)):
        if pd.isna(d):
            return None
        return float(d) if isinstance(d, float) else int(d)
    return str(d)

def analyze_excel(filepath, sheet_name=0):
    try:
        if filepath.endswith('.xls'):
            try:
                df = pd.read_excel(filepath, sheet_name=sheet_name, engine='xlrd')
            except Exception:
                try:
                    df = pd.read_excel(filepath, sheet_name=sheet_name)
                except Exception as e:
                    return str(e)
        else:
            df = pd.read_excel(filepath, sheet_name=sheet_name)
        
        info = {
            'shape': df.shape,
            'columns': df.columns.tolist()[:20],
            'head': df.head(3).to_dict()
        }
        return clean_dict(info)
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    so_file = 'd:/Goks!/GOKS! WEB APP - RUNNING/Data Training Old/01. Januari 2025 Air Dingin.xlsx'
    inv_file = 'd:/Goks!/GOKS! WEB APP - RUNNING/Data Training Old/inventory_movements.xls'
    tpl_file = 'd:/Goks!/GOKS! WEB APP - RUNNING/Data Training Old/stock omname adjustment.xlsx'

    result = {
        'SO_Drive': analyze_excel(so_file, sheet_name='REKAP'),
        'Inv_Move': analyze_excel(inv_file, sheet_name=0),
        'Template': analyze_excel(tpl_file, sheet_name=0)
    }

    with open('d:/Goks!/GOKS! WEB APP - RUNNING/temp/analyze_data.json', 'w') as f:
        json.dump(result, f, indent=4)
    print("Analysis saved")
