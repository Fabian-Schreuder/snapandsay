#!/usr/bin/env python3
import json
import sys
from pathlib import Path

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_keys(data, prefix=""):
    keys = set()
    if isinstance(data, dict):
        for k, v in data.items():
            full_key = f"{prefix}.{k}" if prefix else k
            keys.add(full_key)
            keys.update(get_keys(v, full_key))
    return keys

def verify_parity(en_path, nl_path):
    print(f"Verifying parity between:\n- {en_path}\n- {nl_path}\n")
    
    try:
        en_data = load_json(en_path)
        nl_data = load_json(nl_path)
    except Exception as e:
        print(f"Error loading files: {e}")
        return False

    en_keys = get_keys(en_data)
    nl_keys = get_keys(nl_data)

    missing_in_nl = en_keys - nl_keys
    missing_in_en = nl_keys - en_keys

    valid = True

    if missing_in_nl:
        print("❌ Missing keys in NL (present in EN):")
        for k in sorted(missing_in_nl):
            print(f"  - {k}")
        valid = False

    if missing_in_en:
        print("❌ Missing keys in EN (present in NL):")
        for k in sorted(missing_in_en):
            print(f"  - {k}")
        valid = False
        
    if valid:
        print("✅ SUCCESS: Translation files are in sync.")
    
    return valid

if __name__ == "__main__":
    # Assuming script is run from project root, or we find relative to this script
    script_dir = Path(__file__).parent.resolve()
    project_root = script_dir.parent # script is in scripts/, so parent is root (maybe)
    
    # Actually, the file path given in tools was /home/fabian/dev/work/snapandsay/frontend/messages
    # Let's try to locate it relative to current working directory or hardcoded based on workspace
    
    base_path = Path("/home/fabian/dev/work/snapandsay/frontend/messages")
    en_path = base_path / "en.json"
    nl_path = base_path / "nl.json"
    
    if not en_path.exists() or not nl_path.exists():
        print(f"Could not find translation files at {base_path}")
        sys.exit(1)

    success = verify_parity(en_path, nl_path)
    sys.exit(0 if success else 1)
