#!/usr/bin/env python3
import sys
import json
import re
from pathlib import Path
import argparse
from typing import Dict, Any, Union
from datetime import datetime

def clean_key(key: str) -> str:
    """Clean and normalize key names."""
    # Remove numeric prefixes and common artifacts
    key = re.sub(r'^[\d-]+', '', key)
    key = re.sub(r'{\s*(\d+\s*)*{*\s*', '', key)
    # Remove trailing numbers and special characters
    key = re.sub(r'\d+$', '', key)
    key = re.sub(r'[{}]', '', key)
    return key.strip()

def clean_value(value: str) -> Union[str, float, int]:
    """Clean and normalize values, converting to appropriate types."""
    # Remove common artifacts
    value = re.sub(r'^00000$', '', value)
    value = re.sub(r'[{}]', '', value)
    
    # Try to convert to numeric if possible
    value = value.strip()
    try:
        if '.' in value:
            return float(value)
        return int(value)
    except ValueError:
        return value

def parse_timestamp(key: str, value: str) -> str:
    """Parse and format timestamp values."""
    if any(time_key in key.lower() for time_key in ['date', 'time', 'start', 'end']):
        # Handle split datetime values
        if value.endswith('M}00000'):  # Time part
            time_match = re.search(r'(\d{2}:\d{2}:\d{2}\s*[AP]M)', value)
            if time_match:
                return time_match.group(1)
        elif re.match(r'\d{1,2}/\d{1,2}/\d{4}', value):
            return value
    return value

def merge_datetime_entries(data: Dict[str, Any]) -> Dict[str, Any]:
    """Merge split date and time entries."""
    result = {}
    date_pattern = re.compile(r'(\d{1,2}/\d{1,2}/\d{4})\s*$')
    time_pattern = re.compile(r'(\d{2}:\d{2}:\d{2}\s*[AP]M)')
    
    temp_date = None
    for key, value in data.items():
        if isinstance(value, str):
            date_match = date_pattern.search(value)
            time_match = time_pattern.search(value)
            
            if date_match and time_match:
                result[key] = f"{date_match.group(1)} {time_match.group(1)}"
            elif date_match:
                temp_date = date_match.group(1)
            elif time_match and temp_date:
                result[key] = f"{temp_date} {time_match.group(1)}"
            else:
                result[key] = value
        else:
            result[key] = value
    
    return result

def structure_sections(data: Dict[str, Any]) -> Dict[str, Any]:
    """Organize data into proper sections."""
    structured_data = {}
    current_section = None
    
    for key, value in data.items():
        clean_k = clean_key(key)
        
        # Check if this is a section header
        if value == "00000" and not any(char.isdigit() for char in clean_k):
            current_section = clean_k
            structured_data[current_section] = {}
        else:
            if current_section and clean_k != current_section:
                structured_data[current_section][clean_k] = clean_value(value)
            else:
                structured_data[clean_k] = clean_value(value)
    
    return structured_data

def process_rtf_file(input_file: Path, output_dir: Path) -> None:
    """Process RTF file and save as clean JSON."""
    try:
        # Read input file
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Parse initial JSON
        data = json.loads(content)
        
        # Clean and structure the data
        cleaned_data = {clean_key(k): v for k, v in data.items()}
        merged_data = merge_datetime_entries(cleaned_data)
        structured_data = structure_sections(merged_data)
        
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
