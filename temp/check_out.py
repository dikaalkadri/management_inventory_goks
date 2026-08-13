import pandas as pd

out_file = "D:/Goks!/OUTPUT GUDANG AKHIR/Template_Adjustment_Terisi_20260812_103432.xlsx"
df = pd.read_excel(out_file)
print(df.tail(10))
