#!/usr/bin/env python3
import sys
import json
import re
from pathlib import Path
import argparse
from typing import Dict, Any, List, Tuple

def extract_key_value(line: str) -> Tuple[str, str]:
    """Extract clean key-value pair from a line."""
    # Skip table formatting lines
    if line.startswith('+--') or not line.strip():
        return None, None
        
    # Split on colon if present
    parts = line.split(':', 1)
    if len(parts) != 2:
        return None, None
        
    key = parts[0].strip()
    value = parts[1].strip()
    
    # Clean key
    key = re.sub(r'[^a-zA-Z0-9\s/_]', '', key)  # Remove special chars except spaces and /
    key = re.sub(r'\s+', '_', key)  # Replace spaces with single underscore
    key = key.lower()  # Convert to lowercase
    
    # Clean value
    value = value.strip('| []{}\\')
    value = re.sub(r'\s+', ' ', value).strip()
    
    return key, value

def parse_rtf_content(content: str) -> Dict[str, Any]:
    """Parse RTF content into structured data."""
    data = {
        "machine": {},
        "xray_source": {},
        "detector": {},
        "distances": {},
        "motion_positions": {},
        "setup": {},
        "ct_scan": {}
    }
    
    current_section = None
    lines = content.split('\n')
    datetime_parts = []
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines and table borders
        if not line or line.startswith('+--'):
            continue
            
        # Handle section headers
        if line.startswith('**') and line.endswith(':**'):
            section = line.strip('*: ').lower()
            current_section = section.replace(' ', '_')
            continue
            
        # Extract key-value pair
        key, value = extract_key_value(line)
        if not key:
            continue
            
        # Handle datetime components
        if re.search(r'\d{1,2}/\d{1,2}/\d{4}', value):
            datetime_parts.append(value)
        elif re.search(r'\d{1,2}:\d{2}:\d{2}\s*[AP]M', value):
            if datetime_parts:
                value = f"{datetime_parts[-1]} {value}"
                
        # Handle special fields
        if key.startswith('gain_map_'):
            if 'gain_maps' not in data['detector']:
                data['detector']['gain_maps'] = {}
            map_num = key.split('_')[-1]
            # Combine the timestamp with the gain map value if present
            if value.endswith('AM)') or value.endswith('PM)'):
                prev_line = [l for l in lines if l.strip().startswith('___') and 'dev' in l]
                if prev_line:
                    value = f"{prev_line[0].split('___')[1].strip()}, {value}"
            data['detector']['gain_maps'][f'map_{map_num}'] = value
            continue
            
        # Map to appropriate section
        if current_section in data:
            data[current_section][key] = value
        else:
            # Try to map based on key prefix
            mapped = False
            for section in data:
                if key.startswith(section):
                    cleaned_key = key.replace(f"{section}_", "")
                    data[section][cleaned_key] = value
                    mapped = True
                    break
            if not mapped:
                data["machine"][key] = value
    
    # Clean up empty sections and fields
    return {k: {sk: sv for sk, sv in v.items() if sv} 
            for k, v in data.items() if any(sv for sv in v.values())}

def process_rtf_file(input_file: Path, output_dir: Path) -> None:
    """Process RTF file and save as clean JSON."""
    try:
        # Read RTF file
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the content
        structured_data = parse_rtf_content(content)
        
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
