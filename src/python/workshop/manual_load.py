#!/usr/bin/env python3

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.calendar_mcp_server import ROOMS_FILE

def test():
    try:
        with open(ROOMS_FILE, 'r') as f:
            data = json.load(f)
        
        with open('manual_load.txt', 'w') as f:
            f.write("=== Manual Load Test ===\\n")
            f.write(f"File path: {ROOMS_FILE}\\n")
            f.write(f"Data type: {type(data)}\\n")
            f.write(f"Data keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}\\n")
            if 'rooms' in data:
                f.write(f"Rooms count: {len(data['rooms'])}\\n")
                if data['rooms']:
                    f.write(f"First room ID: {data['rooms'][0].get('id', 'NO ID')}\\n")
                    f.write(f"First room name: {data['rooms'][0].get('name', 'NO NAME')}\\n")
            
            f.write("\\n=== Raw Data (first 500 chars) ===\\n")
            raw_data = json.dumps(data, indent=2)
            f.write(raw_data[:500])
            
        print(f"SUCCESS: Loaded {len(data.get('rooms', []))} rooms")
        return data
        
    except Exception as e:
        with open('manual_load.txt', 'w') as f:
            f.write(f"ERROR: {str(e)}\\n")
            import traceback
            f.write(traceback.format_exc())
        print(f"ERROR: {e}")
        return None

if __name__ == "__main__":
    test()
