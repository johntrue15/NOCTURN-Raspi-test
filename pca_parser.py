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
from git import Repo
import re
import datetime

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
    def __init__(self, input_dir, output_dir, archive_dir, config):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.archive_dir = archive_dir
        self.config = config  # Store config
        self.processed_files = set()  # Track processed files
        logger.info(f"Initialized handler with: input={input_dir}, output={output_dir}, archive={archive_dir}")
        logger.info(f"Git config: username={self.config['Git']['USERNAME']}, branch={self.config['Git']['BRANCH']}")

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

            # Replace spaces with underscores in filename
            filename = os.path.basename(file_path)
            safe_filename = filename.replace(' ', '_')
            
            logger.info(f"Processing PCA file: {filename} (safe name: {safe_filename})")

            # If file is from network share, copy to input directory
            if '/mnt/windows_share' in file_path:
                logger.info(f"File from network share, copying to input directory")
                local_path = os.path.join(self.input_dir, safe_filename)
                
                # Ensure input directory exists
                os.makedirs(self.input_dir, exist_ok=True)
                
                try:
                    shutil.copy2(file_path, local_path)
                    logger.info(f"Copied to: {local_path}")
                    # Remove original file from share
                    os.remove(file_path)
                    logger.info(f"Removed original file from share")
                    # Add both paths to processed files
                    self.processed_files.add(file_path)
                    self.processed_files.add(local_path)
                    return  # Let the local file watcher handle the processing
                except Exception as copy_error:
                    logger.error(f"Failed to copy file: {str(copy_error)}\n{traceback.format_exc()}")
                    return

            # Convert PCA to JSON
            try:
                with open(file_path, 'r') as pca_file:
                    pca_data = pca_file.read()
                    
                # Parse PCA data and convert to JSON
                json_data = self.convert_pca_to_json(pca_data)
                
                # Save JSON file - use safe filename
                json_filename = os.path.splitext(safe_filename)[0] + '.json'
                json_path = os.path.join(self.output_dir, json_filename)
                
                # Ensure output directory exists
                os.makedirs(self.output_dir, exist_ok=True)
                
                with open(json_path, 'w') as json_file:
                    json.dump(json_data, json_file, indent=4)
                logger.info(f"Created JSON file: {json_path}")
                
                # Move original PCA file to archive - use safe filename
                archive_path = os.path.join(self.archive_dir, safe_filename)
                
                # Ensure archive directory exists
                os.makedirs(self.archive_dir, exist_ok=True)
                
                shutil.move(file_path, archive_path)
                logger.info(f"Moved PCA file to archive: {archive_path}")
                
                # Create readme file
                base_name = os.path.splitext(filename)[0]
                readme_filename = f"{base_name}_metadataparser_readme.txt"
                readme_path = os.path.join(self.input_dir, readme_filename)
                with open(readme_path, "w") as readme_file:
                    readme_file.write(
                        f"This file indicates that '{filename}' has been parsed and archived.\n"
                        f"JSON output is at '{self.output_dir}'\n"
                        f"A copy of the original is in '{self.archive_dir}'"
                    )
                
                # Git operations
                try:
                    repo_dir = "/opt/pca_parser/gitrepo"
                    # Create json directory in repo if it doesn't exist
                    json_repo_path = os.path.join(repo_dir, 'json')
                    os.makedirs(json_repo_path, exist_ok=True)
                    
                    # Copy JSON to git repo
                    repo_json_path = os.path.join(json_repo_path, json_filename)
                    shutil.copy2(json_path, repo_json_path)
                    
                    # Git operations
                    repo = Repo(repo_dir)
                    repo.git.config('--local', 'user.name', self.config['Git']['USERNAME'])
                    repo.git.config('--local', 'user.email', 'jtrue15@ufl.edu')
                    
                    # Fetch and pull latest changes
                    try:
                        origin = repo.remote('origin')
                        fetch_info = origin.fetch()
                        if fetch_info:
                            logger.info("Fetched latest changes")
                            # Stash any uncommitted changes
                            if repo.is_dirty(untracked_files=True):
                                logger.info("Stashing uncommitted changes")
                                repo.git.stash('save')
                            
                            # Pull with rebase strategy
                            repo.git.pull('--rebase', 'origin', self.config['Git']['BRANCH'])
                            
                            # Pop stash if we stashed changes
                            if repo.git.stash('list'):
                                logger.info("Popping stashed changes")
                                repo.git.stash('pop')
                    except Exception as fetch_error:
                        logger.warning(f"Error lines received while fetching: {str(fetch_error)}")
                    
                    # Only add the specific JSON file
                    repo.git.add(repo_json_path)
                    
                    # Check if there are changes to the specific file
                    if repo.git.diff('--cached', '--name-only'):
                        commit_message = f"Auto-commit: Added {json_filename}"
                        repo.index.commit(commit_message)
                        
                        # Try push with retries
                        max_retries = 3
                        retry_count = 0
                        while retry_count < max_retries:
                            try:
                                origin.push(self.config['Git']['BRANCH'])
                                logger.info(f"Git: Committed and pushed {json_filename}")
                                break
                            except Exception as push_error:
                                retry_count += 1
                                if retry_count == max_retries:
                                    raise
                                logger.warning(f"Push attempt {retry_count} failed, retrying...")
                                time.sleep(2)  # Wait before retry
                    else:
                        logger.info(f"No changes to {json_filename}")
                        
                except Exception as git_error:
                    logger.error(f"Git operation failed: {str(git_error)}\n{traceback.format_exc()}")
                
            except Exception as convert_error:
                logger.error(f"Conversion failed: {str(convert_error)}\n{traceback.format_exc()}")
                return
            
            logger.info(f"File processing complete: {filename}")
            self.processed_files.add(file_path)
            
            # Periodically clean up processed files list (keep last 1000)
            if len(self.processed_files) > 1000:
                self.processed_files = set(list(self.processed_files)[-1000:])

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}\n{traceback.format_exc()}")

    def convert_pca_to_json(self, pca_data):
        """Convert PCA data to JSON format using configparser"""
        try:
            # Create a ConfigParser instance
            parser = configparser.ConfigParser(interpolation=None)  # Disable interpolation
            parser.optionxform = str  # Preserve case in keys
            
            # Read PCA data from string
            parser.read_string(pca_data)
            
            # Convert to dictionary with proper type conversion
            data_dict = {}
            for section in parser.sections():
                section_dict = {}
                for key, value in parser.items(section):
                    try:
                        # Convert to float if decimal point present, else try integer
                        if "." in value and not value.endswith('.tif'):  # Skip .tif files
                            section_dict[key] = float(value)
                        else:
                            try:
                                section_dict[key] = int(value)
                            except ValueError:
                                # Keep as string if conversion fails
                                section_dict[key] = value
                    except ValueError:
                        # Keep as string if conversion fails
                        section_dict[key] = value
                data_dict[section] = section_dict
                
            return data_dict
            
        except Exception as e:
            logger.error(f"PCA to JSON conversion failed: {str(e)}\n{traceback.format_exc()}")
            raise

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

def check_and_remount_share(config_path='/root/.smbcredentials'):
    """Check mount status and attempt remount if needed"""
    try:
        # Read IP from fstab
        with open('/etc/fstab', 'r') as f:
            fstab_content = f.read()
            ip_match = re.search(r'//(\d+\.\d+\.\d+\.\d+)/NOCTURN', fstab_content)
            if not ip_match:
                raise Exception("Could not find Windows IP in fstab")
            windows_ip = ip_match.group(1)

        # Test connection to Windows host
        ping_result = os.system(f"ping -c 1 -W 2 {windows_ip} >/dev/null 2>&1")
        if ping_result != 0:
            logger.error(f"Windows host {windows_ip} is not responding")
            return False

        # Check if share is mounted AND accessible
        is_mounted = os.path.ismount('/mnt/windows_share')
        can_access = False
        if is_mounted:
            try:
                # Try to list directory contents
                os.listdir('/mnt/windows_share')
                can_access = True
            except Exception:
                logger.warning("Share is mounted but not accessible")
                is_mounted = False

        if not is_mounted or not can_access:
            logger.warning("Share not mounted or not accessible, attempting remount...")
            
            # Force unmount if in bad state
            os.system('umount -f /mnt/windows_share 2>/dev/null')
            time.sleep(1)  # Wait a moment
            
            # Attempt remount
            mount_cmd = f"mount -t cifs //{windows_ip}/NOCTURN /mnt/windows_share -o credentials={config_path},iocharset=utf8,dir_mode=0777,file_mode=0777"
            result = os.system(mount_cmd)
            
            if result == 0:
                # Verify the mount is actually working
                try:
                    os.listdir('/mnt/windows_share')
                    logger.info("Successfully remounted share and verified access")
                    return True
                except Exception:
                    logger.error("Mount succeeded but share is not accessible")
                    return False
            else:
                logger.error("Failed to remount share")
                return False
        return True
    except Exception as e:
        logger.error(f"Error in remount attempt: {str(e)}\n{traceback.format_exc()}")
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
        
        # Create handler with config
        event_handler = FileHandler(input_dir, output_dir, archive_dir, config)
        
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
        
        # Track last mount check time
        last_mount_check = datetime.datetime.now()
        mount_check_interval = datetime.timedelta(seconds=15)  # Check every 15 seconds
        
        # Keep the script running
        while True:
            time.sleep(1)
            
            # Check mount status periodically
            now = datetime.datetime.now()
            if now - last_mount_check > mount_check_interval:
                last_mount_check = now
                
                # Check and remount if needed
                if not check_and_remount_share():
                    logger.warning("Mount check failed, will retry in 15 seconds")
                    # Force observer restart on next successful mount
                    for observer in observers:
                        try:
                            observer.stop()
                        except Exception as e:
                            logger.warning(f"Error stopping observer: {str(e)}")
                    observers.clear()
                    continue
                
                # If mount was restored, restart observers
                if not any(observer.is_alive() for observer in observers):
                    logger.info("Restarting observers after mount recovery")
                    observers = []
                    
                    # Recreate local observer
                    observer_local = Observer()
                    observer_local.schedule(event_handler, input_dir, recursive=False)
                    observers.append(observer_local)
                    
                    # Recreate network observer if mount is available
                    if os.path.ismount(network_share):
                        observer_network = PollingObserver(timeout=2)
                        observer_network.schedule(event_handler, network_share, recursive=False)
                        observers.append(observer_network)
                    
                    # Start new observers
                    for observer in observers:
                        observer.start()
                        logger.info(f"Restarted observer for paths: {[w.path for w in observer._watches]}")
            
            # Check if observers are alive
            if not any(observer.is_alive() for observer in observers):
                logger.error("All observers died, attempting recovery")
                # Try to restart observers instead of raising error
                try:
                    for observer in observers:
                        if not observer.is_alive():
                            observer.start()
                    if not any(observer.is_alive() for observer in observers):
                        raise RuntimeError("Failed to restart observers")
                except Exception as restart_error:
                    logger.error(f"Observer restart failed: {str(restart_error)}")
                    raise RuntimeError("Observer restart failed")
                
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}\n{traceback.format_exc()}")
        raise

if __name__ == "__main__":
    main()
