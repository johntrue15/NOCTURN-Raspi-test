#!/usr/bin/env python3

import configparser
import json
import os
import shutil
import urllib.parse
import logging
from git import Repo, InvalidGitRepositoryError, NoSuchPathError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def read_config():
    """Reads settings from config.ini (same directory) and returns them as a dictionary."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.ini")

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    config = configparser.ConfigParser()
    config.read(config_path)
    
    # Pull values from config
    settings = {
        "INPUT_DIR": config.get("Directories", "INPUT_DIR"),
        "OUTPUT_DIR": config.get("Directories", "OUTPUT_DIR"),
        "ARCHIVE_DIR": config.get("Directories", "ARCHIVE_DIR"),
        "GIT_LOCAL_REPO_DIR": config.get("Directories", "GIT_LOCAL_REPO_DIR"),
        "REPO_URL": config.get("Git", "REPO_URL"),
        "BRANCH": config.get("Git", "BRANCH", fallback="main"),
        "USERNAME": config.get("Git", "USERNAME", fallback=""),
        "TOKEN": config.get("Git", "PERSONAL_ACCESS_TOKEN", fallback="")
    }

    # Verify all directories exist
    for dir_key in ["INPUT_DIR", "OUTPUT_DIR", "ARCHIVE_DIR", "GIT_LOCAL_REPO_DIR"]:
        directory = settings[dir_key]
        if not os.path.exists(directory):
            logger.info(f"Creating directory: {directory}")
            os.makedirs(directory, exist_ok=True)

    return settings

def init_or_update_repo(repo_dir, repo_url, branch, username, token):
    """Initialize or update the Git repository."""
    try:
        if os.path.exists(repo_dir):
            try:
                repo = Repo(repo_dir)
                logger.info(f"Found existing repo at {repo_dir}. Updating...")
                
                # Fetch and reset to match origin
                repo.git.fetch('--all')
                repo.git.reset('--hard', f'origin/{branch}')
                logger.info("Repository updated successfully")
                
            except (InvalidGitRepositoryError, NoSuchPathError):
                logger.info(f"Invalid repository at {repo_dir}, recreating...")
                shutil.rmtree(repo_dir)
                os.makedirs(repo_dir, exist_ok=True)
                repo = Repo.clone_from(repo_url, repo_dir, branch=branch)
                logger.info("Repository cloned successfully")
        else:
            os.makedirs(repo_dir, exist_ok=True)
            repo = Repo.clone_from(repo_url, repo_dir, branch=branch)
            logger.info("Repository cloned successfully")

    except Exception as e:
        logger.error(f"Git operation failed: {str(e)}")
        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)
            os.makedirs(repo_dir)
        raise

def commit_and_push_changes(repo_dir, commit_message, branch, username, token):
    """Commit and push changes to the repository."""
    try:
        repo = Repo(repo_dir)
        
        # Configure Git
        repo.git.config('--local', 'user.name', 'PCA Parser')
        repo.git.config('--local', 'user.email', 'jtrue15@ufl.edu')
        
        # Add all changes
        repo.git.add(A=True)
        
        # Only commit if there are changes
        if repo.is_dirty(untracked_files=True):
            logger.info("Committing changes...")
            repo.index.commit(commit_message)
            
            logger.info("Pushing changes to remote...")
            repo.git.push('origin', branch)
            logger.info("Changes pushed successfully")
        else:
            logger.info("No changes to commit")
            
    except Exception as e:
        logger.error(f"Failed to commit and push changes: {str(e)}")
        raise

def ini_to_dict(file_path):
    """Convert .pca file (INI format) to dictionary with proper type conversion."""
    parser = configparser.ConfigParser()
    parser.optionxform = str  # Preserve case in keys
    parser.read(file_path)

    data_dict = {}
    for section in parser.sections():
        section_dict = {}
        for key, value in parser.items(section):
            try:
                # Convert to float if decimal point present, else try integer
                if "." in value:
                    section_dict[key] = float(value)
                else:
                    section_dict[key] = int(value)
            except ValueError:
                # Keep as string if conversion fails
                section_dict[key] = value
        data_dict[section] = section_dict
    return data_dict

def process_pca_files(settings):
    """Process all PCA files in the input directory."""
    input_dir = settings["INPUT_DIR"]
    output_dir = settings["OUTPUT_DIR"]
    archive_dir = settings["ARCHIVE_DIR"]
    repo_dir = settings["GIT_LOCAL_REPO_DIR"]

    # Process each .pca file
    files_processed = False
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(".pca"):
            try:
                ini_path = os.path.join(input_dir, filename)
                base_name = os.path.splitext(filename)[0]
                json_file = base_name + ".json"
                json_path = os.path.join(output_dir, json_file)

                # Convert and save as JSON
                logger.info(f"Processing file: {filename}")
                data = ini_to_dict(ini_path)
                with open(json_path, "w") as f:
                    json.dump(data, f, indent=4)

                # Copy to repository if configured
                if repo_dir:
                    json_repo_path = os.path.join(repo_dir, 'json')
                    os.makedirs(json_repo_path, exist_ok=True)
                    repo_json_path = os.path.join(json_repo_path, json_file)
                    shutil.copy2(json_path, repo_json_path)
                    files_processed = True

                # Archive original file
                shutil.copy2(ini_path, os.path.join(archive_dir, filename))
                os.remove(ini_path)  # Remove original after successful processing

                # Create readme file
                readme_filename = f"{base_name}_metadataparser_readme.txt"
                readme_path = os.path.join(input_dir, readme_filename)
                with open(readme_path, "w") as readme_file:
                    readme_file.write(
                        f"This file indicates that '{filename}' has been parsed and archived.\n"
                        f"JSON output is at '{output_dir}'\n"
                        f"A copy of the original is in '{archive_dir}'"
                    )
                
                logger.info(f"Successfully processed {filename}")

            except Exception as e:
                logger.error(f"Failed to process {filename}: {str(e)}")
                continue

    # Commit and push changes if files were processed
    if files_processed and repo_dir:
        try:
            commit_and_push_changes(
                repo_dir=repo_dir,
                commit_message="Auto-commit: PCA to JSON updates",
                branch=settings["BRANCH"],
                username=settings["USERNAME"],
                token=settings["TOKEN"]
            )
        except Exception as e:
            logger.error(f"Failed to push changes to repository: {str(e)}")
            raise

def main():
    """Main execution function."""
    try:
        logger.info("Starting PCA parser service")
        settings = read_config()

        # Initialize or update Git repository if configured
        if settings["GIT_LOCAL_REPO_DIR"]:
            init_or_update_repo(
                repo_dir=settings["GIT_LOCAL_REPO_DIR"],
                repo_url=settings["REPO_URL"],
                branch=settings["BRANCH"],
                username=settings["USERNAME"],
                token=settings["TOKEN"]
            )

        process_pca_files(settings)
        logger.info("Processing complete")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise

if __name__ == "__main__":
    main()
