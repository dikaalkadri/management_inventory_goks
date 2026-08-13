import pandas as pd

if __name__ == '__main__':
    so_file = 'd:/Goks!/GOKS! WEB APP - RUNNING/Data Training Old/01. Januari 2025 Air Dingin.xlsx'
    df = pd.read_excel(so_file, sheet_name='REKAP', header=None)
    print("Row 0:", df.iloc[0].values)
    print("Row 1:", df.iloc[1].values)
