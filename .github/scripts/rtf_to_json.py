#!/usr/bin/env python3
import sys
import json
import re
from pathlib import Path
import argparse
from typing import Dict, Any, List, Tuple
from datetime import datetime

def clean_rtf_key(key: str) -> str:
    """Clean RTF control codes from key names."""
    # Remove RTF formatting codes and table instructions
    key = re.sub(r'trow.*?ltrch_', '', key)
    key = re.sub(r'fs\d+intbl_', '', key)
    key = re.sub(r'bintbl_', '', key)
    key = re.sub(r'\\.*?\\', '', key)
    
    # Remove remaining special characters
    key = re.sub(r'[^a-zA-Z0-9_/\s-]', '', key)
    
    # Convert spaces to underscores and clean up
    key = key.strip().lower().replace(' ', '_')
    key = re.sub(r'_{2,}', '_', key)
    
    return key

def clean_rtf_value(value: str) -> str:
    """Clean RTF control codes from values."""
    # Remove RTF control sequences
    value = re.sub(r'\\[a-zA-Z]+\d*', '', value)
    value = re.sub(r'{.*?}', '', value)
    value = re.sub(r'\\', '', value)
    
    # Remove cell formatting
    value = re.sub(r'li\d+', '', value)
    value = re.sub(r'ri\d+', '', value)
    value = re.sub(r'sa\d+', '', value)
    value = re.sub(r'sb\d+', '', value)
    value = re.sub(r'fi\d+', '', value)
    value = re.sub(r'ql', '', value)
    value = re.sub(r'cell', '', value)
    
    return value.strip()

def parse_rtf_table(content: str) -> Dict[str, Any]:
    """Parse RTF table content into structured data."""
    data = {
        "machine": {},
        "xray_source": {},
        "detector": {},
        "distances": {},
        "motion_positions": {},
        "setup": {},
        "ct_scan": {}
    }
    
    # Parse JSON first to get the RTF structure
    try:
        rtf_data = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {str(e)}")
        return data
        
    current_section = None
    
    for key, value in rtf_data.get("machine", {}).items():
        clean_key = clean_rtf_key(key)
        clean_value = clean_rtf_value(value)
        
        # Skip empty values
        if not clean_value:
            continue
            
        # Handle datetime parts
        if re.search(r'\d{1,2}/\d{1,2}/\d{4}', clean_key):
            if 'datetime' not in data['machine']:
                data['machine']['datetime'] = []
            data['machine']['datetime'].append(clean_value)
            continue
            
        # Map to appropriate section
        section_mapping = {
            'xray': 'xray_source',
            'detector': 'detector',
            'distance': 'distances',
            'motion': 'motion_positions',
            'setup': 'setup',
            'ct': 'ct_scan'
        }
        
        mapped = False
        for prefix, section in section_mapping.items():
            if prefix in clean_key:
                # Remove section prefix from key
                sub_key = clean_key.replace(f"{prefix}_", "").replace(prefix, "")
                data[section][sub_key] = clean_value
                mapped = True
                break
                
        if not mapped:
            # Add to machine section by default
            data['machine'][clean_key] = clean_value
    
    # Merge datetime entries
    if 'datetime' in data['machine'] and isinstance(data['machine']['datetime'], list):
        data['machine']['datetime'] = ' '.join(data['machine']['datetime'])
    
    # Remove empty sections
    return {k: v for k, v in data.items() if v}

def process_rtf_file(input_file: Path, output_dir: Path) -> None:
    """Process RTF file and save as clean JSON."""
    try:
        # Read RTF file
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the content
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
