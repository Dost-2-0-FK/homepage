#!/usr/bin/env python3
"""
Minimal script to update JSON files based on name and surname.
"""

import json
import os
import sys
from pathlib import Path

def update_json_file(json_path, name, sirname, json_field, value):
    """Update a specific field in a JSON file if name and sirname match."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check if name and sirname match (case-insensitive)
        if (data.get('name', '').lower() == name.lower() and data.get('sirname', '').lower() == sirname.lower()):
            
            # Update the field
            data[json_field] = value
            
            # Save the file back
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"Updated {json_path}")
            return True
    
    except json.JSONDecodeError:
        print(f"Skipping {json_path}: Invalid JSON")
    except Exception as e:
        print(f"Error processing {json_path}: {e}")
    
    return False

def main():
    # Get arguments
    if len(sys.argv) != 5:
        print("Usage: python script.py <name> <sirname> <json_field> <value>")
        print("Example: python script.py John Doe age 30")
        sys.exit(1)
    
    name = sys.argv[1]
    sirname = sys.argv[2]
    json_field = sys.argv[3]
    value = sys.argv[4]
    
    # Directory containing JSON files (current directory by default)
    json_dir = Path("/usr/bin/dost/homepage/data/file/")
    
    # Find all JSON files in the directory
    json_files = list(json_dir.glob('*.json'))
    
    if not json_files:
        print(f"No JSON files found in {json_dir}")
        sys.exit(1)
    
    print(f"Searching {len(json_files)} JSON file(s)...")
    
    found = False
    for json_file in json_files:
        if update_json_file(json_file, name, sirname, json_field, value):
            found = True
            break
    
    if not found:
        print(f"No matching record found for {name} {sirname}")
        sys.exit(1)
    else:
        print("Update complete!")

if __name__ == "__main__":
    main()
