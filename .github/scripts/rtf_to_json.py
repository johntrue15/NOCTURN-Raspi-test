#!/usr/bin/env python3
import json
import re
import os
import sys
from striprtf.striprtf import rtf_to_text
from pathlib import Path

def clean_rtf_content(rtf_content):
    """Convert RTF to plain text and clean up formatting."""
    plain_text = rtf_to_text(rtf_content)
    plain_text = re.sub(r'\\[a-z]+\d*', '', plain_text)
    plain_text = re.sub(r'\{|\}', '', plain_text)
    plain_text = re.sub(r'\s+', ' ', plain_text)
    return plain_text

def clean_value(value):
    """Clean up RTF artifacts from values."""
    if not value:
        return None
    
    # Remove common RTF control words
    value = re.sub(r'\\[a-z]+', '', value)
    # Remove extra spaces
    value = re.sub(r'\s+', ' ', value)
    # Clean value
    value = value.strip()
    
    # Return None for empty or RTF-only content
    if not value or value in ['cell', '']:
        return None
    
    return value

def parse_rtf_to_dict(rtf_content):
    """Parse RTF content into a structured dictionary."""
    parsed_data = {}
    sections = {
        'Machine ID': r"Machine ID:\s*(.+)",
        'Machine Serial': r"Machine Serial:\s*(.+)",
        'Operator ID': r"Operator ID:\s*(.+)",
        'Date/Time': r"Date/Time:\s*(.+)",
        'Xray Source': {
            'Name': r"Xray Source[\s\S]*?Name:\s*(.+?)(?=\n|$)",
            'Voltage': r"Voltage:\s*(.+)",
            'Current': r"Current:\s*(.+)",
            'Focal spot size': r"Focal spot size:\s*(.+)"
        },
        'Detector': {
            'Name': r"Detector[\s\S]*?Name:\s*(.+?)(?=\n|$)",
            'Pixel pitch': r"Pixel pitch:\s*(.+)",
            'Gain': r"Gain:\s*(.+)",
            'Binning': r"Binning:\s*(.+)",
            'Framerate': r"Framerate:\s*(.+)",
            'Flip': r"Flip:\s*(.+)",
            'Rotation': r"Rotation:\s*(.+)",
            'Crop': r"Crop:\s*(.+)",
            'ROI': r"ROI:\s*(.+)",
            'Defect map': r"Defect map:\s*(.+)",
            'Offset map': r"Offset map:\s*(.+)",
            'Gain map 0': r"Gain map 0:\s*(.+)",
            'Gain map 1': r"Gain map 1:\s*(.+)",
            'Gain map 2': r"Gain map 2:\s*(.+)",
            'Gain map 3': r"Gain map 3:\s*(.+)",
            'Gain map 4': r"Gain map 4:\s*(.+)"
        },
        'Distances': {
            'Source to detector': r"Source to detector:\s*(.+)",
            'Source to object': r"Source to object:\s*(.+)",
            'Calculated Ug': r"Calculated Ug:\s*(.+)",
            'Zoom factor': r"Zoom factor:\s*(.+)",
            'Effective pixel pitch': r"Effective pixel pitch:\s*(.+)"
        },
        'Motion Positions': {
            'Table rotate': r"Table rotate:\s*(.+)",
            'Table left/right': r"Table left/right:\s*(.+)",
            'Table up/down': r"Table up/down:\s*(.+)",
            'Detector up/down': r"Detector up/down:\s*(.+)",
            'Table mag': r"Table mag:\s*(.+)",
            'Detector mag': r"Detector mag:\s*(.+)",
            'Detector left/right': r"Detector left/right:\s*(.+)"
        },
        'Setup': {
            'Fixturing': r"Fixturing:\s*(.+)",
            'Filter': r"Filter:\s*(.+)"
        },
        'CT Scan': {
            'Project name': r"Project name:\s*(.+)",
            'Project folder': r"Project folder:\s*(.+)",
            '# Frames averaged': r"# Frames averaged:\s*(.+)",
            '# Skip frames': r"# Skip frames:\s*(.+)",
            'Monitor xray down': r"Monitor xray down:\s*(.+)",
            'Type': r"Type:\s*(.+)",
            '# Projections': r"# Projections:\s*(.+)",
            'Start': r"Start:\s*(.+)",
            'End': r"End:\s*(.+)",
            'Duration': r"Duration:\s*(.+)"
        }
    }

    for key, pattern in sections.items():
        if isinstance(pattern, dict):
            section_data = {}
            for sub_key, sub_pattern in pattern.items():
                match = re.search(sub_pattern, rtf_content, re.MULTILINE)
                if match:
                    value = clean_value(match.group(1))
                    if value is not None:
                        section_data[sub_key] = value
            if section_data:  # Only add non-empty sections
                parsed_data[key] = section_data
        else:
            match = re.search(pattern, rtf_content, re.MULTILINE)
            if match:
                value = clean_value(match.group(1))
                if value is not None:
                    parsed_data[key] = value

    return parsed_data

def parse_geometric_formula(rtf_content):
    """Parse the Geometric Unsharpness Custom Formula section."""
    cleaned_text = clean_rtf_content(rtf_content)
    
    section_match = re.search(
        r"Geometric Unsharpness Custom Formula:.*?(?=Motion Positions:|$)",
        cleaned_text,
        re.DOTALL
    )
    
    if not section_match:
        return {}
    
    section_text = section_match.group(0)
    formulas = {}
    
    formula_blocks = re.finditer(
        r"Name:\s*(.*?)(?:\s*\[.*?\])?\s*Expression:\s*(.*?)\s*Value:\s*(.*?)(?=Name:|$)",
        section_text,
        re.DOTALL
    )
    
    def clean_pipes(text):
        """Remove extra pipe characters and clean up the text."""
        cleaned = text.replace('|', '')
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip()
    
    for block in formula_blocks:
        name = block.group(1).strip()
        name = re.sub(r'\s*\[.*?\]', '', name)
        name = clean_pipes(name)
        
        expression = clean_pipes(block.group(2).strip())
        value = clean_pipes(block.group(3).strip())
        
        if not name or name.startswith('\\') or name.endswith('cell'):
            continue
            
        expression = expression.replace('Math.', '')
        
        formulas[name] = {
            'Expression': expression,
            'Value': value
        }
    
    return formulas

def process_rtf_file(input_path):
    """Process RTF file and create JSON output."""
    def remove_empty_sections(d):
        """Recursively remove empty dictionaries and None values."""
        if not isinstance(d, dict):
            return d
        return {
            k: remove_empty_sections(v)
            for k, v in d.items()
            if v is not None and (not isinstance(v, dict) or v)
        }
    try:
        # Create output directory if it doesn't exist
        output_dir = Path('data/output')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate output filename
        input_file = Path(input_path)
        output_file = output_dir / f"{input_file.stem}.json"
        
        # Read and process the RTF file
        with open(input_path, 'r', encoding='utf-8') as file:
            rtf_content = file.read()

        # Initial parsing
        parsed_data = parse_rtf_to_dict(rtf_content)
        
        # Clean up the parsed data
        parsed_data = remove_empty_sections(parsed_data)
        
        # Process Unicode characters
        def process_unicode_in_dict(d):
            if not isinstance(d, dict):
                return d
            result = {}
            for key, value in d.items():
                if isinstance(value, dict):
                    result[key] = process_unicode_in_dict(value)
                elif isinstance(value, str):
                    if '\u00b5' in value:
                        result[key] = value.replace('\u00b5', 'µ')
                    else:
                        result[key] = value
                else:
                    result[key] = value
            return result
        
        parsed_data = process_unicode_in_dict(parsed_data)
        
        # Parse geometric formulas
        formulas = parse_geometric_formula(rtf_content)
        parsed_data['Geometric Unsharpness Custom Formula'] = formulas
        
        # Save final parsed data
        with open(output_file, 'w', encoding='utf-8') as json_file:
            json.dump(parsed_data, json_file, indent=4, ensure_ascii=False)
            
        print(f"Successfully processed {input_path} to {output_file}")
        return True
        
    except Exception as e:
        print(f"Error processing {input_path}: {str(e)}", file=sys.stderr)
        return False

def main():
    """Main entry point for the script."""
    if len(sys.argv) != 2:
        print("Usage: python rtf_to_json.py <input_rtf_file>", file=sys.stderr)
        sys.exit(1)
    
    input_file = sys.argv[1]
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    success = process_rtf_file(input_file)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
