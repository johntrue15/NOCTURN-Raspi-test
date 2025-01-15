#!/usr/bin/env python3
import sys
import json
import re
from pathlib import Path
import argparse
from typing import Dict, Any

def clean_value(value: str) -> str:
    """Clean and normalize values from RTF file."""
    # Remove common RTF artifacts
    value = re.sub(r'\\[a-zA-Z]+', '', value)
    value = value.strip('| []\\{}')
    # Remove multiple spaces
    value = re.sub(r'\s+', ' ', value)
    return value.strip()

def parse_rtf_table(content: str) -> Dict[str, Any]:
    """Parse RTF table content into a structured dictionary."""
    result = {}
    current_section = None
    
    # Split content into lines and process
    lines = content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check for section headers (bold text in RTF)
        if line.startswith('**') and line.endswith(':**'):
            current_section = line.strip('*: ')
            result[current_section] = {}
            i += 1
            continue
            
        # Look for key-value pairs separated by ':'
        if ':' in line and not line.startswith('+'):
            parts = line.split(':', 1)
            if len(parts) == 2:
                key = clean_value(parts[0])
                value = clean_value(parts[1])
                
                if current_section:
                    result[current_section][key] = value
                else:
                    result[key] = value
        
        i += 1
    
    return result

def process_rtf_file(input_file: Path, output_dir: Path) -> None:
    """Process RTF file and save as JSON."""
    try:
        # Read RTF file
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the content
        data = parse_rtf_table(content)
        
        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate output filename
        output_file = output_dir / f"{input_file.stem}.json"
        
        # Write JSON output
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        print(f"Successfully processed {input_file} to {output_file}")
        
    except Exception as e:
        print(f"Error processing {input_file}: {str(e)}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Convert RTF files to JSON')
    parser.add_argument('input_file', type=str, help='Input RTF file path')
    parser.add_argument('--output-dir', type=str, default='data/output',
                       help='Output directory for JSON files')
    
    args = parser.parse_args()
    
    input_path = Path(args.input_file)
    output_path = Path(args.output_dir)
    
    process_rtf_file(input_path, output_path)

if __name__ == '__main__':
    main()
