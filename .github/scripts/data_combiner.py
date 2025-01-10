#!/usr/bin/env python3
"""
Custom Data Combiner
Combines data from multiple JSON files into a human-readable table format.
"""
import json
import sys
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Union
import glob

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
        
        # Handle both naming patterns
        patterns = [
            f"{base_name}.{file_type}.json",  # Pattern: Name.type.json
            f"{base_name}.json",              # Pattern: Name.json
        ]
        
        for pattern in patterns:
            # Use glob to find files that match the pattern
            matches = list(output_dir.glob(pattern))
            if matches:
                return matches[0]
        
        raise FileNotFoundError(f"No matching file found for {base_name} with type {file_type}")

    def extract_key_metrics(self, data: Dict, file_type: str) -> Dict:
        """Extract key metrics based on file type."""
        metrics = {}
        
        if file_type == 'pca':
            # Extract PCA specific metrics
            metrics = {k: v for k, v in data.items() if isinstance(v, (int, float))}
            
        elif file_type == 'pcj':
            # Extract PCJ specific metrics
            if 'info' in data:
                metrics = data['info']
            if 'data' in data and data['data']:
                metrics['last_data_point'] = data['data'][-1]
            
        elif file_type == 'pcp':
            # Extract PCP specific metrics
            if 'metadata' in data:
                metrics = data['metadata']
            if 'measurements' in data and data['measurements']:
                metrics['last_measurement'] = data['measurements'][-1]
                
        elif file_type == 'pcr':
            # Extract PCR specific metrics
            for section, content in data.items():
                if isinstance(content, dict):
                    for key, value in content.items():
                        if isinstance(value, (int, float, str, bool)):
                            metrics[f"{section}_{key}"] = value
                    
        elif file_type == 'vgl':
            # Extract VGL specific metrics
            if 'metadata' in data:
                metrics = data['metadata']
            if 'header' in data:
                metrics.update(data['header'])
                
        return metrics

    def combine_data(self, files: List[tuple]) -> pd.DataFrame:
        """
        Combine data from multiple files into a DataFrame.
        files: List of tuples (filename, file_type)
        """
        combined_data = {}
        
        for file_spec, file_type in files:
            try:
                # Try to find the correct JSON file
                try:
                    json_file = self.find_json_file(file_spec, file_type)
                except FileNotFoundError as e:
                    print(f"Warning: {str(e)}")
                    continue
                
                # Load and process the data
                json_data = self.load_json_file(json_file)
                metrics = self.extract_key_metrics(json_data, file_type)
                
                # Add to combined data
                combined_data[f"{json_file.stem} ({file_type})"] = metrics
                
            except Exception as e:
                print(f"Error processing {file_spec}: {str(e)}")
                continue
        
        # Convert to DataFrame
        df = pd.DataFrame(combined_data).transpose()
        
        # Clean up the DataFrame
        df = df.fillna('N/A')  # Replace NaN with N/A
        # Convert numbers to string with reasonable precision
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
    if len(sys.argv) < 3:
        print("Usage: python custom.py <output_path> <file1> <type1> [<file2> <type2> ...]")
        sys.exit(1)

    output_path = Path(sys.argv[1])
    
    # Parse file inputs (filename and type pairs)
    files = []
    for i in range(2, len(sys.argv), 2):
        if i + 1 < len(sys.argv):
            files.append((sys.argv[i], sys.argv[i + 1]))
    
    combiner = DataCombiner()
    df = combiner.combine_data(files)
    markdown_table = combiner.generate_markdown_table(df)
    combiner.save_output(markdown_table, output_path)

if __name__ == "__main__":
    main()
