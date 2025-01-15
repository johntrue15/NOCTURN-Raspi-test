#!/usr/bin/env python3
import sys
import json
import re
from pathlib import Path
import argparse
from typing import Dict, Any, List, Tuple
from datetime import datetime

def extract_table_data(rtf_content: str) -> List[Tuple[str, str]]:
    """Extract data from RTF table format."""
    data_pairs = []
    current_section = None
    
    # Split into lines and process
    lines = rtf_content.split('\n')
    for line in lines:
        line = line.strip()
        
        # Skip empty lines and table formatting
        if not line or line.startswith('+--'):
            continue
            
        # Handle section headers
        if '**' in line and ':**' in line:
            current_section = line.strip('*: ').lower()
            continue
            
        # Look for key-value pairs (separated by colon)
        if ':' in line:
            key, value = line.split(':', 1)
            
            # Clean key and value
            key = key.strip()
            value = value.strip()
            
            # Add section prefix if we're in a section
            if current_section:
                key = f"{current_section}_{key}"
            
            data_pairs.append((key, value))
    
    return data_pairs

def clean_key(key: str) -> str:
    """Clean and normalize key names."""
    # Remove RTF control codes
    key = re.sub(r'\\[a-zA-Z]+[\d]*\s?', '', key)
    
    # Remove special characters
    key = re.sub(r'[^a-zA-Z0-9_/\s-]', '', key)
    
    # Convert spaces and normalize
    key = key.strip().lower().replace(' ', '_')
    key = re.sub(r'_{2,}', '_', key)
    
    return key

def clean_value(value: str) -> Any:
    """Clean and normalize values."""
    # Remove RTF codes and formatting
    value = value.strip('| []{}\\')
    value = re.sub(r'\\[a-zA-Z]+[\d]*\s?', '', value)
    value = value.strip()
    
    # Handle empty or placeholder values
    if not value or value == 'n/a' or value == '00000':
        return ""
        
    # Convert numeric values if possible
    try:
        if '.' in value and re.match(r'^[\d.]+$', value):
            return float(value)
        elif value.isdigit():
            return int(value)
    except ValueError:
        pass
        
    return value

def structure_data(pairs: List[Tuple[str, str]]) -> Dict[str, Any]:
    """Organize data into structured sections."""
    data = {
        "machine": {
            "id": "",
            "serial": "",
            "operator": "",
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
            "start_time": "",
            "end_time": "",
            "duration": ""
        }
    }
    
    # Process each key-value pair
    for key, value in pairs:
        clean_k = clean_key(key)
        clean_v = clean_value(value)
        
        # Handle gain maps separately
        if 'gain_map_' in clean_k:
            map_num = clean_k.split('_')[-1]
            if clean_v:  # Only add non-empty values
                data['detector']['gain_maps'][f'map_{map_num}'] = clean_v
            continue
            
        # Map data to appropriate sections
        for section in data:
            if section in clean_k:
                sub_key = clean_k.replace(f"{section}_", "")
                if sub_key in data[section]:
                    data[section][sub_key] = clean_v
                break
            elif clean_k in data[section]:
                data[section][clean_k] = clean_v
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
        
        # Extract data pairs
        data_pairs = extract_table_data(content)
        
        # Structure the data
        structured_data = structure_data(data_pairs)
        
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
