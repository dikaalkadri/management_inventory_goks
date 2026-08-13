import pandas as pd
import json

def list_sheets_and_cols(filepath):
    try:
        if filepath.endswith('.xls'):
            try:
                xls = pd.ExcelFile(filepath, engine='xlrd')
            except:
                xls = pd.ExcelFile(filepath)
        else:
            xls = pd.ExcelFile(filepath)
        
        info = {}
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet)
            info[sheet] = {
                'shape': df.shape,
                'columns': df.columns.tolist()
            }
        return info
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    so_file = 'd:/Goks!/GOKS! WEB APP - RUNNING/Data Training Old/01. Januari 2025 Air Dingin.xlsx'

    result = list_sheets_and_cols(so_file)

    with open('d:/Goks!/GOKS! WEB APP - RUNNING/temp/analyze_so_sheets.json', 'w') as f:
        json.dump(result, f, indent=4)
