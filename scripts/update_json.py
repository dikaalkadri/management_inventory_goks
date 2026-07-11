import json
import re

updates = {
    '11': '1tBsKg06dLuoy6JmtHcbqDknVj-4_Dfzy',
    '12': '1iPDc3YItsVnnN9VyTxiscXfUTdzVyknt'
}

with open('n8n kerugian GOKS.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for node in data['nodes']:
    if node['name'] == 'Outlet Folder List':
        code = node['parameters']['jsCode']
        for no, new_id in updates.items():
            pattern = r"({ no: '" + no + r"', name: '.*?',\s*folderId: ')[^']+(' })"
            code = re.sub(pattern, r"\g<1>" + new_id + r"\g<2>", code)
        node['parameters']['jsCode'] = code
        break

with open('n8n kerugian GOKS.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)

print('Updated IDs 11 and 12 successfully!')
