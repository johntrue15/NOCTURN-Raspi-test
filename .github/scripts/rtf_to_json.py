#!/usr/bin/env python3
import sys
import json
import re
from pathlib import Path
import argparse
from typing import Dict, Any, Optional

def extract_gain_map_value(key: str, data: Dict[str, Any]) -> str:
    """Extract gain map value from the raw RTF data."""
    # Find the corresponding raw value entry
    value_key = next((k for k in data['machine'].keys() if f'_{key.split("_")[-1]}_dev_' in k), None)
    if value_key:
        # Extract the numeric value and timestamp
        pattern = r'(\d+\.\d+)_dev_(\d+\.\d+).*?(\d{1,2}/\d{1,2}/\d{4}_\d{1,2}:\d{2}:\d{2}\s*[AP]M)'
        match = re.search(pattern, value_key)
        if match:
            value, dev, timestamp = match.groups()
            return f"{value}, dev {dev}, acquired {timestamp}"
    return ""

def clean_key(key: str) -> str:
    """Clean RTF formatting from key."""
    # Remove RTF control sequences
    key = re.sub(r'fs\d+intbl_ltrch_', '', key)
    key = re.sub(r'bintbl_ltrch_', '', key)
    key = re.sub(r'trow.*?ltrch_', '', key)
    # Remove multiple underscores
    key = re.sub(r'_{2,}', '_', key)
    # Remove remaining special characters
    key = re.sub(r'[^a-zA-Z0-9_/-]', '', key)
    return key.strip('_').lower()

def clean_value(value: str) -> str:
    """Clean RTF formatting from value."""
    # Remove RTF control codes and formatting
    value = re.sub(r'\\[a-zA-Z]+\d*', '', value)
    value = re.sub(r'[\\\{\}]', '', value)
    value = re.sub(r'li\d+', '', value)
    value = re.sub(r'ri\d+', '', value)
    value = re.sub(r'sa\d+', '', value)
    value = re.sub(r'sb\d+', '', value)
    value = re.sub(r'fi\d+', '', value)
    value = re.sub(r'ql', '', value)
    value = re.sub(r'cell', '', value)
    return value.strip()

def extract_time_value(key: str, data: Dict[str, Any]) -> Optional[str]:
    """Extract timestamp from data."""
    time_pattern = r'(\d{1,2}/\d{1,2}/\d{4})_(\d{1,2}:\d{2}:\d{2}\s*[AP]M)'
    if match := re.search(time_pattern, key):
        date, time = match.groups()
        return f"{date} {time}"
    return None

def structure_data(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Structure the data into organized sections."""
    structured = {
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

    # Process machine data
    machine_data = input_data.get('machine', {})
    for key in machine_data:
        clean_k = clean_key(key)
        
        # Handle timestamps
        if time_value := extract_time_value(key, machine_data):
            structured['machine']['datetime'] = time_value
            continue

        # Handle gain maps
        if 'gain_map_' in clean_k:
            map_num = clean_k.split('_')[-1]
            value = extract_gain_map_value(clean_k, input_data)
            if value:
                structured['detector']['gain_maps'][f'map_{map_num}'] = value
            continue

        # Map other values to appropriate sections
        for section in structured:
            if section in clean_k:
                sub_key = clean_k.replace(f"{section}_", "")
                if sub_key in structured[section]:
                    structured[section][sub_key] = clean_value(machine_data[key])
                break
            elif clean_k in structured[section]:
                structured[section][clean_k] = clean_value(machine_data[key])
                break

    # Remove empty sections and fields
    return {k: {sk: sv for sk, sv in v.items() if sv} 
            for k, v in structured.items() if any(sv for sv in v.values())}

def process_rtf_file(input_file: Path, output_dir: Path) -> None:
    """Process RTF-JSON file and save cleaned JSON."""
    try:
        # Read input file
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Structure and clean the data
        structured_data = structure_data(data)
        
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
    parser = argparse.ArgumentParser(description='Convert RTF-JSON files to cleaned JSON')
    parser.add_argument('input_file', type=str, help='Input RTF-JSON file path')
    parser.add_argument('--output-dir', type=str, default='data/output',
                       help='Output directory for JSON files')
    
    args = parser.parse_args()
    
    input_path = Path(args.input_file)
    output_path = Path(args.output_dir)
    
    process_rtf_file(input_path, output_path)

if __name__ == '__main__':
    main()
