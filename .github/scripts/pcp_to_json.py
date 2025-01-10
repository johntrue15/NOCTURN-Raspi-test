#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Union

class PCPConverter:
    def __init__(self, file_path: str):
        """Initialize the converter with the input file path."""
        self.file_path = file_path
        self.header_info: Dict[str, str] = {}
        self.measurements: List[Dict[str, Union[float, str]]] = []

    def parse_header(self, line: str) -> None:
        """Parse header information from the file."""
        if '|' in line:
            # Handle the datos line
            key, value = line.split('|', 1)
            self.header_info[key.strip()] = value.strip()
        elif line.startswith('ImgNr'):
            # Store column headers
            self.header_info['columns'] = line.strip().split('\t')

    def parse_measurement(self, line: str) -> None:
        """Parse a measurement line into a dictionary."""
        values = line.strip().split('\t')
        if not values or not values[0].isdigit():
            return
        measurement = {}
        for column, value in zip(self.header_info['columns'], values):
            # Convert numeric values to appropriate types
            if value.replace('.', '').replace('-', '').isdigit():
                measurement[column] = float(value)
            else:
                try:
                    # Try to parse as datetime
                    measurement[column] = datetime.strptime(
                        value, '%Y-%m-%d %H:%M:%S'
                    ).isoformat()
                except ValueError:
                    measurement[column] = value
        self.measurements.append(measurement)

    def convert(self) -> Dict:
        """Convert the PCP file to a dictionary format."""
        with open(self.file_path, 'r', encoding='utf-8') as file:
            # Process file line by line
            for line in file:
                line = line.strip()
                if not line:
                    continue
                
                if line.startswith('ImgNr') or '|' in line:
                    self.parse_header(line)
                else:
                    self.parse_measurement(line)

        # Create the final output structure
        output = {
            'metadata': self.header_info.copy(),
            'measurements': self.measurements
        }
        
        # Remove columns from metadata as it's internal info
        if 'columns' in output['metadata']:
            del output['metadata']['columns']
            
        return output

    def save_json(self, output_path: str) -> None:
        """Convert and save the data to a JSON file."""
        data = self.convert()
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

def main():
    if len(sys.argv) != 2:
        print("Usage: python pcp_to_json.py <pcp_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    input_path = Path(input_file)
    # Include original extension in output filename
    output_path = Path('data/output') / f"{input_path.stem}.pcp.json"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Process the file
    converter = PCPConverter(input_file)
    converter.save_json(str(output_path))

if __name__ == "__main__":
    main()
