# -*- coding: utf-8 -*-
import os

def search_file(filename, search_path):
    print(f"Searching for {filename} under {search_path}...")
    results = []
    # Skip some massive folders to avoid hanging
    skip_dirs = ['System32', 'SysWOW64', 'WinSxS', '.git', 'node_modules', 'Microsoft', 'Package Cache', 'AppData\\Local\\PackageCache']
    
    for root, dirs, files in os.walk(search_path):
        # Filter directories to skip
        dirs[:] = [d for d in dirs if d not in skip_dirs and not os.path.join(root, d).endswith(tuple(skip_dirs))]
        
        if filename in files:
            full_path = os.path.join(root, filename)
            results.append(full_path)
            print(f"Found: {full_path}")
            
    return results

# Let's search C:\ for 2330.txt
results = search_file("2330.txt", "C:\\")
if not results:
    print("Not found on C:\\")
