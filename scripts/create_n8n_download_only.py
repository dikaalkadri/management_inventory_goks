import json

def main():
    with open('n8ndriveautmation.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    new_data = {
        "name": "Download GDrive 35 Outlets (Only)",
        "nodes": [],
        "connections": {},
        "active": False,
        "settings": data.get("settings", {}),
        "versionId": "download-only-version-1234",
        "id": "download_only_35_outlets"
    }
    
    # Nodes we want to keep
    keep_nodes = [
        "When clicking \"Test workflow\"",
        "Input Form (Bulan & Tahun)",
        "Build Search Query",
        "Outlet Folder List",
        "Google Drive Search",
        "Filter SO Files",
        "Download Sheet (Export as xlsx)"
    ]
    
    for node in data["nodes"]:
        if node["name"] in keep_nodes:
            new_data["nodes"].append(node)
            
    # Add Write File node
    write_node = {
        "parameters": {
            "operation": "write",
            "fileName": "C:/Users/dikaa/Downloads/SO_Outlets/={{ $json.name || $binary.data.fileName }}",
            "dataPropertyName": "data",
            "options": {}
        },
        "id": "write-file-node-123",
        "name": "Write to Disk",
        "type": "n8n-nodes-base.readWriteFile",
        "typeVersion": 1,
        "position": [
            1552,
            0
        ],
        "notes": "Menyimpan file ke folder C:/Users/dikaa/Downloads/SO_Outlets/"
    }
    new_data["nodes"].append(write_node)
    
    # Fix the fileName parameter in Write File. 
    # Usually the binary property is 'data' or the file's binary key.
    # In 'Download Sheet (Export as xlsx)', it outputs binary data in 'data' by default or we can use generic expressions.
    
    # Rebuild connections
    connections = {
        "When clicking \"Test workflow\"": {
            "main": [[{"node": "Input Form (Bulan & Tahun)", "type": "main", "index": 0}]]
        },
        "Input Form (Bulan & Tahun)": {
            "main": [[{"node": "Build Search Query", "type": "main", "index": 0}]]
        },
        "Build Search Query": {
            "main": [[{"node": "Outlet Folder List", "type": "main", "index": 0}]]
        },
        "Outlet Folder List": {
            "main": [[{"node": "Google Drive Search", "type": "main", "index": 0}]]
        },
        "Google Drive Search": {
            "main": [[{"node": "Filter SO Files", "type": "main", "index": 0}]]
        },
        "Filter SO Files": {
            "main": [[{"node": "Download Sheet (Export as xlsx)", "type": "main", "index": 0}]]
        },
        "Download Sheet (Export as xlsx)": {
            "main": [[{"node": "Write to Disk", "type": "main", "index": 0}]]
        }
    }
    
    new_data["connections"] = connections
    
    with open('n8n_download_only.json', 'w', encoding='utf-8') as f:
        json.dump(new_data, f, indent=2)
        
    print("Created n8n_download_only.json successfully.")

if __name__ == "__main__":
    main()
