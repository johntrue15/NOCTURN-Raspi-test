#!/usr/bin/env python3
import sys
import json
import re
from pathlib import Path
import argparse
from typing import Dict, Any, List, Tuple
from datetime import datetime

def extract_table_data(rtf_content: str) -> Dict[str, Any]:
    """Extract and structure data from RTF content."""
    # Remove RTF control sequences
    cleaned = re.sub(r'\\[a-zA-Z]+[-\d]*\s?', ' ', rtf_content)
    
    # Initialize structure
    data = {
        "machine": {},
        "xray_source": {},
        "detector": {},
        "distances": {},
        "geometric_unsharpness": {},
        "motion_positions": {},
        "setup": {},
        "ct_scan": {}
    }
    
    current_section = None
    timestamp_buffer = {}
    
    # Split into lines and process
    lines = cleaned.split('\n')
    for line in lines:
        line = line.strip()
        if not line or line.startswith('+--'):
            continue
            
        # Handle section headers
        if line.startswith('**') and line.endswith(':**'):
            section = line.strip('*: ').lower()
            current_section = section.replace(' ', '_')
            continue
        
        # Process key-value pairs
        if ':' in line:
            key, value = [part.strip() for part in line.split(':', 1)]
            
            # Clean key
            key = key.lower()
            key = re.sub(r'[^a-z0-9_/]', '', key.replace(' ', '_'))
            
            # Clean value
            value = value.strip('| []{}\\')
            value = re.sub(r'\s+', ' ', value).strip()
            
            # Handle empty or placeholder values
            if not value or value == 'n/a' or value == '00000':
                value = ""
            
            # Special handling for timestamps
            if re.search(r'\d{1,2}/\d{1,2}/\d{4}', value):
                timestamp_buffer['date'] = value
                continue
            if re.search(r'\d{1,2}:\d{2}:\d{2}\s*[AP]M', value):
                timestamp_buffer['time'] = value
                if 'date' in timestamp_buffer:
                    value = f"{timestamp_buffer['date']} {value}"
                    timestamp_buffer.clear()
            
            # Handle numeric values
            if value and not isinstance(value, str):
                try:
                    if '.' in str(value):
                        value = float(value)
                    else:
                        value = int(value)
                except ValueError:
                    pass
            
            # Map to appropriate section
            if current_section:
                if current_section in data:
                    data[current_section][key] = value
            else:
                # Try to map to appropriate section based on key
                mapped = False
                for section in data.keys():
                    if key.startswith(section):
                        data[section][key.replace(f"{section}_", "")] = value
                        mapped = True
                        break
                if not mapped:
                    data["machine"][key] = value
    
    # Clean up empty sections
    return {k: v for k, v in data.items() if v}

def process_rtf_file(input_file: Path, output_dir: Path) -> None:
    """Process RTF file and save as clean JSON."""
    try:
        # Read RTF file
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract and structure data
        structured_data = extract_table_data(content)
        
        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate output filename
        output_file = output_dir / f"{input_file.stem}_cleaned.json"
        
        # Write JSON output
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(structured_data, f, indent=2, ensure_ascii=False)
            
        print(f"Successfully processed {input_file} to {output_file}")
        
    except Exception as e:
        print(f"Error processing {input_file}: {str(e)}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Convert RTF files to cleaned JSON')
    parser.add_argument('input_file', type=str, help='Input RTF file path')
    parser.add_argument('--output-dir', type=str, default='data/output',
                       help='Output directory for JSON files')
    
    args = parser.parse_args()
    
    input_path = Path(args.input_file)
    output_path = Path(args.output_dir)
    
    process_rtf_file(input_path, output_path)

if __name__ == '__main__':
    main()
