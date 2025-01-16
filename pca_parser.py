#!/usr/bin/env python3

import configparser
import json
import os
import shutil
import urllib.parse
import logging
from git import Repo

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
            logger.error(f"Directory does not exist: {directory}")
            raise FileNotFoundError(f"Required directory does not exist: {directory}")

    return settings

def init_or_update_repo(repo_dir, repo_url, branch, username, token):
    """Initialize or update the Git repository."""
    try:
        # Prepare the URL with credentials if provided
        if username and token:
            protocol_removed = repo_url.replace("https://", "")
            username_encoded = urllib.parse.quote(username, safe="")
            token_encoded = urllib.parse.quote(token, safe="")
            repo_url_with_creds = f"https://{username_encoded}:{token_encoded}@{protocol_removed}"
        else:
            repo_url_with_creds = repo_url

        # Remove directory if it exists but is not a valid repo
        if os.path.exists(repo_dir):
            try:
                repo = Repo(repo_dir)
                logger.info(f"Found existing repo at {repo_dir}. Pulling latest changes...")
                origin = repo.remotes.origin
                if username and token:
                    old_url = origin.url.replace("https://", "")
                    new_url = f"https://{username_encoded}:{token_encoded}@{old_url}"
                    origin.set_url(new_url)
                origin.pull(branch)
                logger.info("Repository updated successfully")
            except (InvalidGitRepositoryError, NoSuchPathError):
                logger.info(f"Removing invalid repository at {repo_dir}")
                shutil.rmtree(repo_dir)
                os.makedirs(repo_dir, exist_ok=True)
                logger.info(f"Cloning repository from {repo_url} into {repo_dir}...")
                Repo.clone_from(repo_url_with_creds, repo_dir, branch=branch)
                logger.info("Repository cloned successfully")
        else:
            # Fresh clone
            os.makedirs(repo_dir, exist_ok=True)
            logger.info(f"Cloning repository from {repo_url} into {repo_dir}...")
            Repo.clone_from(repo_url_with_creds, repo_dir, branch=branch)
            logger.info("Repository cloned successfully")

    except Exception as e:
        logger.error(f"Git operation failed: {str(e)}")
        # If we catch any error during the process, clean up the directory
        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)
            os.makedirs(repo_dir)
        raise

def commit_and_push_changes(repo_dir, commit_message, branch, username, token):
    """Commit and push changes to the repository."""
    try:
        repo = Repo(repo_dir)
        
        # Ensure we're on the correct branch
        if repo.active_branch.name != branch:
            logger.info(f"Checking out branch '{branch}'...")
            repo.git.checkout(branch)

        # Add all changes
        repo.git.add(A=True)

        if repo.is_dirty(untracked_files=True):
            logger.info("Committing changes...")
            repo.index.commit(commit_message)

            # Update remote URL with credentials if provided
            if username and token:
                origin = repo.remote("origin")
                old_url = origin.url.replace("https://", "")
                username_encoded = urllib.parse.quote(username, safe="")
                token_encoded = urllib.parse.quote(token, safe="")
                new_url = f"https://{username_encoded}:{token_encoded}@{old_url}"
                origin.set_url(new_url)

            logger.info("Pushing changes to remote...")
            repo.remotes.origin.push(branch)
            logger.info("Changes pushed successfully")
        else:
            logger.info("No changes to commit")
    except Exception as e:
        logger.error(f"Failed to commit and push changes: {str(e)}")
        raise

def ini_to_dict(file_path):
    """Convert .pca file (INI format) to dictionary."""
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
    
    # Process each .pca file
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

                # Archive original file
                shutil.copy2(ini_path, os.path.join(archive_dir, filename))

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

    # Copy JSON files to Git repo if configured
    repo_dir = settings["GIT_LOCAL_REPO_DIR"]
    if repo_dir and os.path.exists(repo_dir):
        try:
            json_repo_subfolder = os.path.join(repo_dir, "json")
            os.makedirs(json_repo_subfolder, exist_ok=True)

            for file_name in os.listdir(output_dir):
                if file_name.lower().endswith(".json"):
                    src = os.path.join(output_dir, file_name)
                    dst = os.path.join(json_repo_subfolder, file_name)
                    shutil.copy2(src, dst)

            commit_and_push_changes(
                repo_dir=repo_dir,
                commit_message="Auto-commit: PCA to JSON updates",
                branch=settings["BRANCH"],
                username=settings["USERNAME"],
                token=settings["TOKEN"]
            )
        except Exception as e:
            logger.error(f"Failed to update Git repository: {str(e)}")
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
