#!/usr/bin/env python3
import sys
import json
import re
from pathlib import Path
import argparse
from typing import Dict, Any, Union, List, Tuple
from datetime import datetime

def extract_table_data(rtf_content: str) -> List[Tuple[str, str]]:
    """Extract key-value pairs from RTF table format."""
    # Remove RTF control sequences and extra whitespace
    cleaned = re.sub(r'\\[a-zA-Z]+[\d]*\s?', ' ', rtf_content)
    cleaned = re.sub(r'\{|\}|\[|\]|\\|\|', ' ', cleaned)
    
    # Split into lines and clean up
    lines = [line.strip() for line in cleaned.split('\n') if line.strip()]
    
    pairs = []
    current_section = None
    
    for line in lines:
        # Skip separator lines and empty lines
        if line.startswith('+--') or not line.strip():
            continue
            
        # Check for section headers
        if line.startswith('**') and line.endswith(':**'):
            current_section = line.strip('*: ')
            continue
            
        # Look for key-value pairs
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            
            # Add section prefix if we're in a section
            if current_section:
                key = f"{current_section}_{key}"
            
            pairs.append((key, value))
    
    return pairs

def clean_key(key: str) -> str:
    """Clean and normalize key names."""
    # Remove any remaining RTF artifacts
    key = re.sub(r'\s+', ' ', key)
    key = key.strip()
    # Convert spaces to underscores for JSON compatibility
    key = re.sub(r'\s+', '_', key)
    return key.lower()

def clean_value(value: str) -> Union[str, float, int]:
    """Clean and normalize values, converting to appropriate types."""
    # Remove common RTF artifacts
    value = re.sub(r'\s+', ' ', value)
    value = value.strip()
    
    # Handle empty or placeholder values
    if not value or value == 'n/a':
        return ""
    
    # Try to convert numeric values
    try:
        if '.' in value:
            return float(value)
        elif value.isdigit():
            return int(value)
    except ValueError:
        pass
    
    return value

def parse_timestamp(value: str) -> str:
    """Parse and standardize timestamp values."""
    # Various timestamp patterns
    timestamp_patterns = [
        r'\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}:\d{2}\s*(?:AM|PM)',
        r'\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}\s*(?:AM|PM)',
    ]
    
    for pattern in timestamp_patterns:
        match = re.search(pattern, value)
        if match:
            return match.group(0)
    
    return value

def structure_data(pairs: List[Tuple[str, str]]) -> Dict[str, Any]:
    """Convert pairs into structured JSON data."""
    structured_data = {}
    
    for key, value in pairs:
        clean_k = clean_key(key)
        
        # Handle sections
        if '_' in clean_k:
            section, subkey = clean_k.split('_', 1)
            if section not in structured_data:
                structured_data[section] = {}
            
            # Check if it's a timestamp
            if any(time_word in subkey for time_word in ['date', 'time', 'start', 'end']):
                cleaned_value = parse_timestamp(value)
            else:
                cleaned_value = clean_value(value)
                
            structured_data[section][subkey] = cleaned_value
        else:
            structured_data[clean_k] = clean_value(value)
    
    return structured_data

def process_rtf_file(input_file: Path, output_dir: Path) -> None:
    """Process RTF file and save as clean JSON."""
    try:
        # Read RTF file
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract table data
        pairs = extract_table_data(content)
        
        # Structure the data
        structured_data = structure_data(pairs)
        
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
