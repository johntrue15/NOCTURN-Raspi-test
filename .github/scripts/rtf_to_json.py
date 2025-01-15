#!/usr/bin/env python3
import sys
import json
import re
from pathlib import Path
import argparse
from typing import Dict, Any, List, Tuple

def clean_key(key: str) -> str:
    """Clean and normalize key names."""
    # Remove underscores and special characters
    key = re.sub(r'_{2,}', '', key)  # Remove multiple underscores
    key = re.sub(r'[^a-zA-Z0-9_/]', '', key)  # Keep only alphanumeric, underscore, and forward slash
    
    # Handle special cases
    key = re.sub(r'^_+|_+$', '', key)  # Remove leading/trailing underscores
    key = re.sub(r'_+', '_', key)  # Replace multiple underscores with single
    
    return key.lower().strip()

def clean_value(value: str) -> Any:
    """Clean and normalize values."""
    if not value or value == '00000':
        return ""
        
    # Remove common artifacts
    value = value.strip('| []{}\\')
    value = re.sub(r'\s+', ' ', value).strip()
    
    # Try to convert numeric values
    try:
        if '.' in value and re.match(r'^[\d.]+$', value):
            return float(value)
        elif value.isdigit():
            return int(value)
    except ValueError:
        pass
        
    return value

def parse_rtf_table(content: str) -> Dict[str, Any]:
    """Parse RTF table into structured data."""
    # Initialize structure
    data = {
        "machine": {
            "id": "",
            "serial": "",
            "operator_id": "",
            "datetime": ""
        },
        "xray_source": {
            "name": "",
            "voltage": "",
            "current": "",
            "focal_spot_size": ""
        },
        "detector": {
            "name": "",
            "pixel_pitch": "",
            "gain": "",
            "binning": "",
            "framerate": "",
            "flip": "",
            "rotation": "",
            "crop": "",
            "roi": "",
            "defect_map": "",
            "offset_map": "",
            "gain_maps": {}
        },
        "distances": {
            "units": "",
            "source_to_detector": "",
            "source_to_object": "",
            "calculated_ug": "",
            "zoom_factor": "",
            "effective_pixel_pitch": ""
        },
        "motion_positions": {
            "table_rotate": "",
            "table_left_right": "",
            "table_up_down": "",
            "detector_up_down": "",
            "table_mag": "",
            "detector_mag": "",
            "detector_left_right": ""
        },
        "setup": {
            "fixturing": "",
            "filter": ""
        },
        "ct_scan": {
            "project_name": "",
            "project_folder": "",
            "frames_averaged": "",
            "skip_frames": "",
            "monitor_xray_down": "",
            "type": "",
            "projections": "",
            "start": "",
            "end": "",
            "duration": ""
        }
    }
    
    # Split into lines and process
    lines = content.split('\n')
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('+--'):
            continue
            
        # Handle section headers
        if ':**' in line:
            section = line.split(':**')[0].strip('*: ').lower()
            current_section = section.replace(' ', '_')
            continue
            
        # Process key-value pairs
        if ':' in line:
            parts = line.split(':', 1)
            if len(parts) == 2:
                key = clean_key(parts[0])
                value = clean_value(parts[1])
                
                # Special handling for dates and times
                if re.search(r'\d{1,2}/\d{1,2}/\d{4}', str(value)):
                    if 'time' in key.lower():
                        time_parts = value.split()
                        if len(time_parts) > 1:
                            value = f"{time_parts[0]} {time_parts[1]}"
                
                # Map to appropriate section based on key
                if key.startswith('gain_map_'):
                    map_num = key.split('_')[-1]
                    data['detector']['gain_maps'][f'map_{map_num}'] = value
                elif 'name' in key and current_section:
                    data[current_section]['name'] = value
                else:
                    for section in data:
                        if key in data[section]:
                            data[section][key] = value
                            break
                        elif key.startswith(section):
                            clean_subkey = key.replace(f"{section}_", "")
                            if clean_subkey in data[section]:
                                data[section][clean_subkey] = value
                                break
    
    # Remove empty sections and fields
    return {k: {sk: sv for sk, sv in v.items() if sv} 
            for k, v in data.items() if any(sv for sv in v.values())}

def process_rtf_file(input_file: Path, output_dir: Path) -> None:
    """Process RTF file and save as clean JSON."""
    try:
        # Read RTF file
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse and structure the data
        structured_data = parse_rtf_table(content)
        
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
