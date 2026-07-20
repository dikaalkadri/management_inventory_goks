import os
import re

template_dir = 'd:/Goks!/GOKS! WEB APP - RUNNING/templates'

# This pattern matches the entire <a> tag block for agentic-dashboard
pattern = r'\s*<a href="/agentic-dashboard".*?</a>'

count = 0
for filename in os.listdir(template_dir):
    if filename.endswith('.html'):
        filepath = os.path.join(template_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove the matched block
        new_content = re.sub(pattern, '', content, flags=re.DOTALL)
        
        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Removed agentic menu from {filename}")
            count += 1

print(f"Done. Updated {count} files.")
