#!/usr/bin/env python3

import configparser
import json
import os
import shutil
import logging
import traceback
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from watchdog.observers.polling import PollingObserver
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
        self.processed_files = set()  # Track processed files
        logger.info(f"Initialized handler with: input={input_dir}, output={output_dir}, archive={archive_dir}")

    def on_any_event(self, event):
        """Catch all events for debugging"""
        if event.is_directory:
            return
            
        logger.info(f"Event type: {event.event_type}, path: {event.src_path}")
        
        # Only process created events for network share
        if '/mnt/windows_share' in event.src_path:
            if event.event_type == 'created':
                self.process_file(event.src_path)
        # For local directory, only process modified events
        elif event.event_type == 'modified':
            self.process_file(event.src_path)

    def process_file(self, file_path):
        try:
            # Skip if file was already processed
            if file_path in self.processed_files:
                logger.debug(f"Skipping already processed file: {file_path}")
                return

            logger.info(f"Processing file: {file_path}")
            if not file_path.endswith('.pca'):
                logger.info(f"Skipping non-PCA file: {file_path}")
                return

            filename = os.path.basename(file_path)
            logger.info(f"Processing PCA file: {filename}")

            # If file is from network share, copy to input directory
            if '/mnt/windows_share' in file_path:
                logger.info(f"File from network share, copying to input directory")
                local_path = os.path.join(self.input_dir, filename)
                shutil.copy2(file_path, local_path)
                logger.info(f"Copied to: {local_path}")
                # Remove original file from share
                os.remove(file_path)
                logger.info(f"Removed original file from share")
                # Add both paths to processed files
                self.processed_files.add(file_path)
                self.processed_files.add(local_path)
                return  # Let the local file watcher handle the processing

            # Your existing processing logic here
            # Add actual file processing code here
            logger.info(f"File processing complete: {filename}")
            
            # Add to processed files after successful processing
            self.processed_files.add(file_path)
            
            # Periodically clean up processed files list (keep last 1000)
            if len(self.processed_files) > 1000:
                self.processed_files = set(list(self.processed_files)[-1000:])

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}\n{traceback.format_exc()}")

def test_watchdog(path):
    """Test if watchdog can detect changes in the directory"""
    try:
        test_file = os.path.join(path, "watchdog_test.tmp")
        logger.info(f"Testing watchdog with file: {test_file}")
        
        # Create test file
        with open(test_file, 'w') as f:
            f.write('test')
        time.sleep(2)
        
        # Modify test file
        with open(test_file, 'a') as f:
            f.write('update')
        time.sleep(2)
        
        # Remove test file
        os.remove(test_file)
        logger.info("Watchdog test complete")
        return True
    except Exception as e:
        logger.error(f"Watchdog test failed: {str(e)}\n{traceback.format_exc()}")
        return False

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
        
        # Verify directories exist and are accessible
        for path in [input_dir, output_dir, archive_dir, network_share]:
            if not os.path.exists(path):
                logger.info(f"Creating directory: {path}")
                os.makedirs(path, exist_ok=True)
            # Test directory permissions
            if not os.access(path, os.R_OK | os.W_OK):
                logger.error(f"Insufficient permissions for directory: {path}")
                raise PermissionError(f"Cannot read/write to {path}")
            logger.info(f"Directory verified: {path} (readable: {os.access(path, os.R_OK)}, writable: {os.access(path, os.W_OK)})")
        
        # Create handler
        event_handler = FileHandler(input_dir, output_dir, archive_dir)
        
        # Set up observers
        observers = []
        
        # Local input directory observer
        logger.info(f"Setting up local directory monitoring: {input_dir}")
        observer_local = Observer()
        observer_local.schedule(event_handler, input_dir, recursive=False)
        observers.append(observer_local)
        
        # Network share observer
        if os.path.ismount(network_share):
            logger.info(f"Setting up network share monitoring: {network_share}")
            try:
                # Use PollingObserver for network share
                observer_network = PollingObserver(timeout=2)  # 2 second polling interval
                observer_network.schedule(event_handler, network_share, recursive=False)
                observers.append(observer_network)
                logger.info("Network share observer scheduled successfully")
            except Exception as e:
                logger.error(f"Failed to set up network share observer: {str(e)}\n{traceback.format_exc()}")
        else:
            logger.warning(f"Network share not mounted: {network_share}")
        
        # Test watchdog on network share
        if os.path.ismount(network_share):
            if test_watchdog(network_share):
                logger.info("Network share watchdog test passed")
            else:
                logger.error("Network share watchdog test failed")
        
        # Start all observers
        for observer in observers:
            observer.start()
            logger.info(f"Started observer for paths: {[w.path for w in observer._watches]}")
            
        logger.info("File monitoring started")
        
        # Keep the script running
        while True:
            time.sleep(1)
            # Verify observers are still running
            for observer in observers:
                if not observer.is_alive():
                    logger.error("Observer died, restarting service")
                    raise RuntimeError("Observer died")
            
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}\n{traceback.format_exc()}")
        raise

if __name__ == "__main__":
    main()
