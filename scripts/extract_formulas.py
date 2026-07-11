import json
import re
import os

config_path = r"d:\Goks!\GOKS! WEB APP - RUNNING\modules\stockin\formula_config.py"
json_path = r"d:\Goks!\GOKS! WEB APP - RUNNING\data\mass_formulas.json"

if not os.path.exists(os.path.dirname(json_path)):
    os.makedirs(os.path.dirname(json_path), exist_ok=True)

with open(config_path, "r", encoding="utf-8") as f:
    content = f.read()

# We need to extract the dictionary J_FORMULAS
# It starts at `J_FORMULAS = {` and ends at `}`
match = re.search(r"J_FORMULAS\s*=\s*\{([^}]+)\}", content, re.DOTALL)
if not match:
    print("Could not find J_FORMULAS")
    exit(1)

dict_str = match.group(1)

# Split by lines
lines = dict_str.split("\n")

data = {}
current_key = None
current_formula = None
current_name = None

# Regex to match key: formula
pattern_kf = re.compile(r"^\s*(\d+)\s*:\s*\"([^\"]+)\"")
# Regex to match item name
pattern_item = re.compile(r"^\s*#\s*Item\s*:\s*(.+)")

for line in lines:
    kf_match = pattern_kf.search(line)
    if kf_match:
        # If we had a previous key but no name was found, save it as "Bahan Baku Baris X"
        if current_key is not None:
            data[current_key] = {
                "name": current_name if current_name else f"Bahan Baku Baris {current_key}",
                "formula": current_formula
            }
        
        current_key = kf_match.group(1)
        current_formula = kf_match.group(2)
        current_name = None
        continue
    
    item_match = pattern_item.search(line)
    if item_match and current_key is not None:
        if not current_name:
            current_name = item_match.group(1).strip()

# Last one
if current_key is not None:
    data[current_key] = {
        "name": current_name if current_name else f"Bahan Baku Baris {current_key}",
        "formula": current_formula
    }

with open(json_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4)

print(f"Extracted {len(data)} formulas to {json_path}")
