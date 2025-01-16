#!/usr/bin/env python3
"""
VGL to JSON Converter
This script converts VGL binary files to JSON format.
It handles binary data and produces structured JSON output.
"""
import json
import sys
import struct
from pathlib import Path
from typing import Dict, Any, BinaryIO

class VGLConverter:
    def __init__(self):
        self.data = {}
        self.current_offset = 0
        
    def read_string(self, file: BinaryIO, max_length: int = 256) -> str:
        """Read a null-terminated string from the binary file."""
        chars = []
        while True:
            if len(chars) >= max_length:
                break
            char = file.read(1)
            if not char or char == b'\x00':
                break
            try:
                chars.append(char.decode('utf-8'))
            except UnicodeDecodeError:
                # Skip invalid characters
                continue
        return ''.join(chars)
    
    def read_int32(self, file: BinaryIO) -> int:
        """Read a 32-bit integer from the binary file."""
        data = file.read(4)
        if len(data) != 4:
            raise EOFError("End of file reached while reading int32")
        return struct.unpack('<i', data)[0]
    
    def read_float32(self, file: BinaryIO) -> float:
        """Read a 32-bit float from the binary file."""
        data = file.read(4)
        if len(data) != 4:
            raise EOFError("End of file reached while reading float32")
        return struct.unpack('<f', data)[0]
    
    def read_header(self, file: BinaryIO) -> Dict[str, Any]:
        """Read the VGL file header."""
        header = {}
        
        # Read magic number or identifier if present
        magic = file.read(4)
        if magic:
            header['magic'] = magic.hex()
        
        return header
    
    def read_metadata(self, file: BinaryIO) -> Dict[str, Any]:
        """Read metadata section of the VGL file."""
        metadata = {}
        
        try:
            # Attempt to read basic metadata fields
            metadata['version'] = self.read_int32(file)
            metadata['timestamp'] = self.read_int32(file)
            
            # Read name or identifier string
            name = self.read_string(file)
            if name:
                metadata['name'] = name
                
        except (EOFError, struct.error):
            pass
            
        return metadata
    
    def convert_file(self, input_path: Path) -> Dict[str, Any]:
        """Convert VGL file to dictionary structure."""
        self.data = {}
        
        try:
            with open(input_path, 'rb') as file:
                # Read file header
                self.data['header'] = self.read_header(file)
                
                # Read metadata
                self.data['metadata'] = self.read_metadata(file)
                
                # Store binary content info
                file.seek(0, 2)  # Seek to end
                self.data['file_size'] = file.tell()
                
        except (IOError, EOFError, struct.error) as e:
            print(f"Error processing file: {e}")
            return {}
            
        return self.data

def main():
    if len(sys.argv) != 2:
        print("Usage: python vgl_to_json.py <vgl_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    input_path = Path(input_file)
    
    if not input_path.exists():
        print(f"Error: Input file '{input_path}' does not exist")
        sys.exit(1)

    # Include original extension in output filename
    output_path = Path('data/output') / f"{input_path.stem}.vgl.json"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert the file
    converter = VGLConverter()
    data = converter.convert_file(input_path)
    
    # Write JSON output
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    main()
