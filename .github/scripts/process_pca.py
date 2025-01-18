import os
import logging
import sys
from pca_parser import FileHandler

def setup_logging():
    """Configure logging to use workspace log file"""
    log_file = os.environ.get('PCA_PARSER_LOG', 'logs/pca_parser.log')
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def main():
    """Process PCA file from command line argument"""
    if len(sys.argv) != 2:
        print("Usage: process_pca.py <pca_file>")
        sys.exit(1)
        
    pca_file = sys.argv[1]
    setup_logging()
    
    handler = FileHandler('/tmp/input', '/tmp/output', '/tmp/archive', {})
    handler.process_file(pca_file)

if __name__ == "__main__":
    main() 