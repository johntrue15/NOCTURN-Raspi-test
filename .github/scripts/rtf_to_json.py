#!/usr/bin/env python3
import json
import re
import os
import sys
from striprtf.striprtf import rtf_to_text
from pathlib import Path

def clean_rtf_content(rtf_content):
    """Convert RTF to plain text and clean up formatting."""
    try:
        # First pass with striprtf
        plain_text = rtf_to_text(rtf_content)
        
        # Clean up common RTF artifacts, but preserve the content
        plain_text = re.sub(r'\\cell', '', plain_text)  # Remove \cell specifically
        plain_text = plain_text.replace('\\par', '\n')  # Convert \par to newlines
        plain_text = re.sub(r'\{|\}', '', plain_text)   # Remove braces
        
        # Remove other RTF commands while preserving content
        plain_text = re.sub(r'\\[a-z]+(?![a-zA-Z])', '', plain_text)
        
        return plain_text
    except Exception as e:
        print(f"Error in clean_rtf_content: {str(e)}")
        return rtf_content

def clean_value(value):
    """Clean value from RTF artifacts and validate."""
    if not value:
        return None
        
    # Remove RTF artifacts
    value = re.sub(r'\\[a-z]+(?:\d+)?', '', value)
    value = re.sub(r'\{|\}', '', value)
    value = value.replace('|', '')
    value = re.sub(r'\s+', ' ', value)
    value = value.strip()
    
    # Validate the cleaned value
    if not value or value == 'cell':
        return None
        
    return value

def parse_rtf_to_dict(rtf_content):
    """Parse RTF content into a structured dictionary."""
    cleaned_text = clean_rtf_content(rtf_content)
    parsed_data = {}
    
    # Define sections and their fields
    sections = [
        ('Machine ID', r'Machine ID:\s*(.*?)(?=\n|$)'),
        ('Machine Serial', r'Machine Serial:\s*(.*?)(?=\n|$)'),
        ('Operator ID', r'Operator ID:\s*(.*?)(?=\n|$)'),
        ('Date/Time', r'Date/Time:\s*(.*?)(?=\n|$)'),
        ('Xray Source', {
            'Name': r'Xray Source[\s\S]*?Name:\s*(.*?)(?=\n|$)',
            'Voltage': r'Voltage:\s*(.*?)(?=\n|$)',
            'Current': r'Current:\s*(.*?)(?=\n|$)',
            'Focal spot size': r'Focal spot size:\s*(.*?)(?=\n|$)'
        }),
        ('Detector', {
            'Name': r'Detector[\s\S]*?Name:\s*(.*?)(?=\n|$)',
            'Pixel pitch': r'Pixel pitch:\s*(.*?)(?=\n|$)',
            'Gain': r'Gain:\s*(.*?)(?=\n|$)',
            'Binning': r'Binning:\s*(.*?)(?=\n|$)',
            'Framerate': r'Framerate:\s*(.*?)(?=\n|$)',
            'Flip': r'Flip:\s*(.*?)(?=\n|$)',
            'Rotation': r'Rotation:\s*(.*?)(?=\n|$)',
            'Crop': r'Crop:\s*(.*?)(?=\n|$)',
            'ROI': r'ROI:\s*(.*?)(?=\n|$)',
            'Defect map': r'Defect map:\s*(.*?)(?=\n|$)',
            'Offset map': r'Offset map:\s*(.*?)(?=\n|$)',
            'Gain map 0': r'Gain map 0:\s*(.*?)(?=\n|$)',
            'Gain map 1': r'Gain map 1:\s*(.*?)(?=\n|$)',
            'Gain map 2': r'Gain map 2:\s*(.*?)(?=\n|$)',
            'Gain map 3': r'Gain map 3:\s*(.*?)(?=\n|$)',
            'Gain map 4': r'Gain map 4:\s*(.*?)(?=\n|$)'
        }),
        ('Distances', {
            'Source to detector': r'Source to detector:\s*(.*?)(?=\n|$)',
            'Source to object': r'Source to object:\s*(.*?)(?=\n|$)',
            'Calculated Ug': r'Calculated Ug:\s*(.*?)(?=\n|$)',
            'Zoom factor': r'Zoom factor:\s*(.*?)(?=\n|$)',
            'Effective pixel pitch': r'Effective pixel pitch:\s*(.*?)(?=\n|$)'
        }),
        ('Motion Positions', {
            'Table rotate': r'Table rotate:\s*(.*?)(?=\n|$)',
            'Table left/right': r'Table left/right:\s*(.*?)(?=\n|$)',
            'Table up/down': r'Table up/down:\s*(.*?)(?=\n|$)',
            'Detector up/down': r'Detector up/down:\s*(.*?)(?=\n|$)',
            'Table mag': r'Table mag:\s*(.*?)(?=\n|$)',
            'Detector mag': r'Detector mag:\s*(.*?)(?=\n|$)',
            'Detector left/right': r'Detector left/right:\s*(.*?)(?=\n|$)'
        }),
        ('Setup', {
            'Fixturing': r'Fixturing:\s*(.*?)(?=\n|$)',
            'Filter': r'Filter:\s*(.*?)(?=\n|$)'
        }),
        ('CT Scan', {
            'Project name': r'Project name:\s*(.*?)(?=\n|$)',
            'Project folder': r'Project folder:\s*(.*?)(?=\n|$)',
            '# Frames averaged': r'# Frames averaged:\s*(.*?)(?=\n|$)',
            '# Skip frames': r'# Skip frames:\s*(.*?)(?=\n|$)',
            'Monitor xray down': r'Monitor xray down:\s*(.*?)(?=\n|$)',
            'Type': r'Type:\s*(.*?)(?=\n|$)',
            '# Projections': r'# Projections:\s*(.*?)(?=\n|$)',
            'Start': r'Start:\s*(.*?)(?=\n|$)',
            'End': r'End:\s*(.*?)(?=\n|$)',
            'Duration': r'Duration:\s*(.*?)(?=\n|$)'
        })
    ]
    
    # Process each section
    for section_name, section_def in sections:
        if isinstance(section_def, dict):
            # Handle nested sections
            section_data = {}
            for field_name, pattern in section_def.items():
                match = re.search(pattern, cleaned_text, re.MULTILINE | re.DOTALL)
                if match:
                    value = clean_value(match.group(1))
                    if value:
                        section_data[field_name] = value
            if section_data:
                parsed_data[section_name] = section_data
        else:
            # Handle top-level fields
            match = re.search(section_def, cleaned_text, re.MULTILINE | re.DOTALL)
            if match:
                value = clean_value(match.group(1))
                if value:
                    parsed_data[section_name] = value
    
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
    
    for block in formula_blocks:
        name = block.group(1).strip()
        name = re.sub(r'\s*\[.*?\]', '', name)
        name = name.replace('|', '').strip()
        
        if not name or name.startswith('\\') or name.endswith('cell'):
            continue
            
        expression = block.group(2).strip().replace('|', '').strip()
        value = block.group(3).strip().replace('|', '').strip()
        expression = expression.replace('Math.', '')
        
        formulas[name] = {
            'Expression': expression,
            'Value': value
        }
    
    return formulas

def process_rtf_file(input_path):
    """Process RTF file and create JSON output."""
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
        
        # Parse main content
        parsed_data = parse_rtf_to_dict(rtf_content)
        
        # Parse geometric formulas
        formulas = parse_geometric_formula(rtf_content)
        if formulas:
            parsed_data['Geometric Unsharpness Custom Formula'] = formulas
        
        # Remove empty sections and None values
        def clean_dict(d):
            if not isinstance(d, dict):
                return d
            return {k: clean_dict(v) for k, v in d.items() 
                   if v is not None and (not isinstance(v, dict) or v)}
        
        parsed_data = clean_dict(parsed_data)
        
        # Save parsed data
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
