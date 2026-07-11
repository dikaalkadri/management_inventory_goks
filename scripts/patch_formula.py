import re

filepath = r"d:\Goks!\GOKS! WEB APP - RUNNING\modules\stockin\formula_config.py"

with open(filepath, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_code = """import json
import os

J_FORMULAS = {}
_json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "mass_formulas.json")
if os.path.exists(_json_path):
    try:
        with open(_json_path, "r", encoding="utf-8") as _f:
            _data = json.load(_f)
            for _k, _v in _data.items():
                if str(_k).isdigit():
                    J_FORMULAS[int(_k)] = _v.get("formula", "")
    except Exception as e:
        pass
"""

out_lines = []
in_j_formulas = False
for line in lines:
    if line.startswith("J_FORMULAS = {"):
        in_j_formulas = True
        out_lines.append(new_code)
        continue
        
    if in_j_formulas:
        if line.startswith("}"):
            in_j_formulas = False
        continue
        
    out_lines.append(line)

with open(filepath, "w", encoding="utf-8") as f:
    f.writelines(out_lines)

print("Berhasil update formula_config.py")
