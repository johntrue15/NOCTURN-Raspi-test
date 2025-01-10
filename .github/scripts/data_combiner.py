#!/usr/bin/env python3
"""
Custom Data Combiner
Combines data from multiple JSON files into a human-readable table format.
"""
import json
import sys
from pathlib import Path
import pandas as pd
from typing import Dict, List, Any, Union

class DataCombiner:
    def __init__(self):
        self.data: Dict[str, Any] = {}
        
    def load_json_file(self, file_path: Path) -> Dict:
        """Load a JSON file and return its contents."""
        with open(file_path, 'r') as f:
            return json.load(f)

    def find_json_file(self, base_name: str, file_type: str) -> Path:
        """Find the correct JSON file based on the base name and type."""
        output_dir = Path('data/output')
        
        # Create the expected filename
        json_filename = f"{base_name}.{file_type}.json"
        json_path = output_dir / json_filename
        
        if json_path.exists():
            return json_path
            
        # If not found, try alternative pattern
        alt_filename = f"{base_name}.json"
        alt_path = output_dir / alt_filename
        
        if alt_path.exists():
            return alt_path
            
        raise FileNotFoundError(f"No matching file found for '{base_name}' with type '{file_type}'")

    def extract_key_metrics(self, data: Dict, file_type: str) -> Dict:
        """Extract key metrics based on file type."""
        metrics = {}
        
        if file_type == 'pca':
            metrics = {k: v for k, v in data.items() if isinstance(v, (int, float))}
            
        elif file_type == 'pcj':
            if 'info' in data:
                metrics = data['info']
            if 'data' in data and data['data']:
                last_data = data['data'][-1]
                metrics.update({f"last_{k}": v for k, v in last_data.items()})
            
        elif file_type == 'pcp':
            if 'metadata' in data:
                metrics = data['metadata']
            if 'measurements' in data and data['measurements']:
                last_measurement = data['measurements'][-1]
                metrics.update({f"last_{k}": v for k, v in last_measurement.items()})
                
        elif file_type == 'pcr':
            for section, content in data.items():
                if isinstance(content, dict):
                    for key, value in content.items():
                        if isinstance(value, (int, float, str, bool)):
                            metrics[f"{section}_{key}"] = value
                    
        elif file_type == 'vgl':
            if 'metadata' in data:
                metrics = data['metadata']
            if 'header' in data:
                metrics.update(data['header'])
                
        return metrics

    def combine_data(self, input_file: Path) -> pd.DataFrame:
        """
        Combine data from multiple files into a DataFrame.
        input_file: Path to file containing filename|type pairs
        """
        combined_data = {}
        
        with open(input_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                    
                # Split on pipe character
                file_spec, file_type = line.split('|')
                
                try:
                    # Try to find the correct JSON file
                    json_file = self.find_json_file(file_spec, file_type)
                    
                    # Load and process the data
                    json_data = self.load_json_file(json_file)
                    metrics = self.extract_key_metrics(json_data, file_type)
                    
                    # Add to combined data
                    combined_data[f"{file_spec} ({file_type})"] = metrics
                    
                except Exception as e:
                    print(f"Warning: {str(e)}")
                    continue
        
        # Convert to DataFrame
        df = pd.DataFrame(combined_data).transpose()
        
        # Clean up the DataFrame
        df = df.fillna('N/A')
        for col in df.columns:
            df[col] = df[col].apply(lambda x: f"{x:.2f}" if isinstance(x, float) else str(x))
        
        return df

    def generate_markdown_table(self, df: pd.DataFrame) -> str:
        """Generate a markdown formatted table from DataFrame."""
        return df.to_markdown()

    def save_output(self, content: str, output_path: Path) -> None:
        """Save the combined data as a markdown file."""
        with open(output_path, 'w') as f:
            f.write("# Combined Analysis Results\n\n")
            f.write(content)

def main():
    if len(sys.argv) != 3:
        print("Usage: python custom.py <output_path> <input_file>")
        sys.exit(1)

    output_path = Path(sys.argv[1])
    input_file = Path(sys.argv[2])
    
    combiner = DataCombiner()
    df = combiner.combine_data(input_file)
    markdown_table = combiner.generate_markdown_table(df)
    combiner.save_output(markdown_table, output_path)

if __name__ == "__main__":
    main()
