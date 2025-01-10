#!/usr/bin/env python3
import sys
import json
from pathlib import Path

def parse_pca_file(file_path: str) -> dict:
    """Parse PCA file and return data as dictionary."""
    data_dict = {}
    
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or "=" not in line:
                continue
                
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            
            # Try to convert numeric values
            try:
                if "." in value:
                    data_dict[key] = float(value)
                else:
                    data_dict[key] = int(value)
            except ValueError:
                data_dict[key] = value
                
    return data_dict

def main():
    if len(sys.argv) != 2:
        print("Usage: python pca_to_json.py <pca_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    input_path = Path(input_file)
    # Include original extension in output filename
    output_path = Path('data/output') / f"{input_path.stem}.pca.json"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Parse and save data
    data = parse_pca_file(input_file)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    main()
