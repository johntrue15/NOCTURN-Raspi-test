#!/usr/bin/env python3
"""
PCR to JSON Converter
This script converts X-ray machine PCR log files to JSON format.
It handles the INI-like format with sections and key-value pairs,
preserving data types where possible.
"""
import json
import sys
from pathlib import Path
from typing import Dict, Union, Any

class PCRConverter:
    def __init__(self):
        self.current_section = None
        self.data = {}
    
    def _convert_value(self, value: str) -> Union[float, int, str, bool]:
        """Convert string values to appropriate Python types."""
        # Handle empty values
        if not value:
            return ""
            
        # Try converting to float/int
        try:
            # Check if it's a float with decimal point
            if '.' in value:
                return float(value)
            # Try converting to int
            num = int(value)
            return num
        except ValueError:
            pass
            
        # Handle boolean values
        if value.lower() in ('true', '1'):
            return True
        if value.lower() in ('false', '0'):
            return False
            
        # Return as string if no other type matches
        return value

    def parse_line(self, line: str) -> None:
        """Parse a single line from the PCR file."""
        # Skip empty lines
        line = line.strip()
        if not line:
            return
            
        # Handle section headers
        if line.startswith('[') and line.endswith(']'):
            self.current_section = line[1:-1]
            self.data[self.current_section] = {}
            return
            
        # Handle key-value pairs
        if '=' in line and self.current_section is not None:
            key, value = line.split('=', 1)
            # Handle keys with special characters (like '|')
            key = key.split('|')[0].strip()
            self.data[self.current_section][key] = self._convert_value(value.strip())

    def convert_file(self, input_path: Path) -> Dict[str, Any]:
        """Convert PCR file to dictionary."""
        self.current_section = None
        self.data = {}
        
        try:
            with open(input_path, 'r', encoding='utf-8') as file:
                for line in file:
                    self.parse_line(line)
        except UnicodeDecodeError:
            # Try with a different encoding if UTF-8 fails
            with open(input_path, 'r', encoding='latin-1') as file:
                for line in file:
                    self.parse_line(line)
                    
        return self.data

def main():
    if len(sys.argv) != 2:
        print("Usage: python pcr_to_json.py <pcr_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    input_path = Path(input_file)
    
    if not input_path.exists():
        print(f"Error: Input file '{input_path}' does not exist")
        sys.exit(1)

    # Include original extension in output filename
    output_path = Path('data/output') / f"{input_path.stem}.pcr.json"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert the file
    converter = PCRConverter()
    data = converter.convert_file(input_path)
    
    # Write JSON output
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    main()
