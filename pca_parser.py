#!/usr/bin/env python3

import configparser
import json
import os
import shutil
import logging
import traceback
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/pca_parser.log'),
        logging.StreamHandler()  # Add console output
    ]
)
logger = logging.getLogger(__name__)

class FileHandler(FileSystemEventHandler):
    def __init__(self, input_dir, output_dir, archive_dir):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.archive_dir = archive_dir
        logger.info(f"Initialized handler with: input={input_dir}, output={output_dir}, archive={archive_dir}")

    def on_created(self, event):
        if event.is_directory:
            return
        self.process_file(event.src_path)

    def process_file(self, file_path):
        try:
            logger.info(f"Processing file: {file_path}")
            # Your existing processing logic here
            pass
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}\n{traceback.format_exc()}")

def main():
    """Main execution function."""
    try:
        logger.info("Starting PCA parser service")
        
        # Read config
        config = configparser.ConfigParser()
        config_path = '/opt/pca_parser/config.ini'
        logger.info(f"Reading config from: {config_path}")
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")
            
        config.read(config_path)
        
        # Set up paths
        input_dir = config['Paths']['input_dir']
        output_dir = config['Paths']['output_dir']
        archive_dir = config['Paths']['archive_dir']
        network_share = config['Paths'].get('network_share', '/mnt/windows_share')
        
        # Verify directories exist
        for path in [input_dir, output_dir, archive_dir]:
            if not os.path.exists(path):
                logger.info(f"Creating directory: {path}")
                os.makedirs(path, exist_ok=True)
        
        logger.info(f"Using paths: input={input_dir}, output={output_dir}, archive={archive_dir}, share={network_share}")
        
        # Create handler
        event_handler = FileHandler(input_dir, output_dir, archive_dir)
        
        # Set up observers for both directories
        observers = []
        
        # Local input directory observer
        logger.info(f"Setting up local directory monitoring: {input_dir}")
        observer_local = Observer()
        observer_local.schedule(event_handler, input_dir, recursive=False)
        observers.append(observer_local)
        
        # Network share observer
        if os.path.ismount(network_share):
            logger.info(f"Setting up network share monitoring: {network_share}")
            observer_network = Observer()
            observer_network.schedule(event_handler, network_share, recursive=False)
            observers.append(observer_network)
        else:
            logger.warning(f"Network share not mounted: {network_share}")
        
        # Start all observers
        for observer in observers:
            observer.start()
            
        logger.info("File monitoring started")
        
        # Keep the script running
        while True:
            time.sleep(1)
            
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}\n{traceback.format_exc()}")
        raise

if __name__ == "__main__":
    main()
