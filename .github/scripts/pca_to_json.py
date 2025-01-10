#!/usr/bin/env python3
import os
import json
import shutil
from pathlib import Path

class PCAProcessor:
    def __init__(self, input_dir, output_dir, archive_dir):
        """Initialize directories and ensure they exist."""
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.archive_dir = Path(archive_dir)
        
        # Create directories if they don't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def pca_to_dict(self, file_path):
        """Parse PCA file into a dictionary."""
        data_dict = {}
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                
                # Convert values to int or float where possible
                try:
                    if "." in value:
                        value = float(value)
                    else:
                        value = int(value)
                except ValueError:
                    pass  # keep as string if conversion fails
                
                data_dict[key] = value
        return data_dict

    def process_pca_files(self):
        """Process all PCA files in the input directory."""
        # Get set of already processed files
        archived_files = {f.name.lower() for f in self.archive_dir.glob("*.pca")}
        processed_count = 0
        
        # Process each .pca file
        for pca_path in self.input_dir.glob("*.pca"):
            if pca_path.name.lower() in archived_files:
                print(f"Skipping already processed file: {pca_path.name}")
                continue
                
            print(f"Processing: {pca_path.name}")
            
            # Parse PCA to dict
            data = self.pca_to_dict(pca_path)
            if not data:
                print(f"Warning: No data extracted from {pca_path.name}")
                continue
                
            # Create JSON output
            json_path = self.output_dir / f"{pca_path.stem}.json"
            with open(json_path, "w") as f:
                json.dump(data, f, indent=4)
                
            # Archive the processed PCA file
            archive_path = self.archive_dir / pca_path.name
            shutil.move(str(pca_path), str(archive_path))
            
            processed_count += 1
            print(f"Successfully processed {pca_path.name}")
        
        return processed_count

def main():
    # Default directories for GitHub Actions environment
    input_dir = os.getenv("INPUT_DIR", "data/input")
    output_dir = os.getenv("OUTPUT_DIR", "data/output")
    archive_dir = os.getenv("ARCHIVE_DIR", "data/archive")
    
    processor = PCAProcessor(input_dir, output_dir, archive_dir)
    processed_count = processor.process_pca_files()
    
    print(f"\nProcessing complete. Processed {processed_count} files.")
    
    # Set output for GitHub Actions
    if os.getenv("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"processed_files={processed_count}\n")
            f.write(f"output_dir={output_dir}\n")

if __name__ == "__main__":
    main()
