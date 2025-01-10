#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from typing import Dict, List, Union

class XRayLogParser:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.info_section: Dict[str, Union[str, int, float]] = {}
        self.data_section: List[Dict[str, Union[str, int, float]]] = []
        self.column_names: List[str] = []

    def parse_info_section(self, lines: List[str]) -> None:
        for line in lines:
            if line.startswith('[Info]'):
                continue
            if line.startswith('[Data]'):
                break
            if '=' in line:
                key, value = line.strip().split('=')
                try:
                    if '.' in value:
                        self.info_section[key] = float(value)
                    else:
                        self.info_section[key] = int(value)
                except ValueError:
                    self.info_section[key] = value

    def parse_column_names(self, header_line: str) -> None:
        header = header_line.lstrip(';').strip()
        self.column_names = [col.strip() for col in header.split('\t')]

    def parse_data_line(self, line: str) -> Dict[str, Union[float, int]]:
        values = line.strip().split('\t')
        data_point = {}
        for col_name, value in zip(self.column_names, values):
            try:
                if '.' in value:
                    data_point[col_name] = float(value)
                else:
                    data_point[col_name] = int(value)
            except ValueError:
                data_point[col_name] = value
        return data_point

    def parse_file(self) -> Dict[str, Union[Dict, List]]:
        with open(self.file_path, 'r') as file:
            lines = file.readlines()

        self.parse_info_section(lines)

        data_section_start = False
        for line in lines:
            if line.startswith('[Data]'):
                data_section_start = True
                continue
            if data_section_start:
                if line.startswith(';'):
                    self.parse_column_names(line)
                elif line.strip():
                    data_point = self.parse_data_line(line)
                    self.data_section.append(data_point)

        return {
            'info': self.info_section,
            'data': self.data_section
        }

    def save_json(self, output_path: str) -> None:
        parsed_data = self.parse_file()
        with open(output_path, 'w') as f:
            json.dump(parsed_data, f, indent=2)

def main():
    if len(sys.argv) != 2:
        print("Usage: python pcj_to_json.py <pcj_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    input_path = Path(input_file)
    output_path = Path('data/output') / f"{input_path.stem}.json"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Process the file
    parser = XRayLogParser(input_file)
    parser.save_json(str(output_path))

if __name__ == "__main__":
    main()
