#!/usr/bin/env python3

import configparser
import json
import os
import shutil
from git import Repo  # Provided by GitPython

def read_config():
    """Reads settings from config.ini (same directory) and returns them as a dictionary."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.ini")

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    config = configparser.ConfigParser()
    config.read(config_path)

    settings = {
        "INPUT_DIR": config.get("General", "INPUT_DIR"),
        "OUTPUT_DIR": config.get("General", "OUTPUT_DIR"),
        "ARCHIVE_DIR": config.get("General", "ARCHIVE_DIR"),
        "GIT_LOCAL_REPO_DIR": config.get("General", "GIT_LOCAL_REPO_DIR"),
        "REPO_URL": config.get("Git", "REPO_URL"),
        "BRANCH": config.get("Git", "BRANCH", fallback="main"),
        "USERNAME": config.get("Git", "USERNAME", fallback=""),
        "TOKEN": config.get("Git", "PERSONAL_ACCESS_TOKEN", fallback=""),
    }
    return settings

def init_or_update_repo(repo_dir, repo_url, branch, username, token):
    """
    Checks if repo_dir is a valid git repo. If not, clone it.
    If it is, pull the latest changes from the remote.
    """
    if not os.path.exists(repo_dir):
        print(f"Cloning repository from {repo_url} into {repo_dir}...")
        os.makedirs(repo_dir, exist_ok=True)

        # If we have creds, embed them in the clone URL
        if username and token:
            protocol_removed = repo_url.replace("https://", "")
            repo_url_with_creds = f"https://{username}:{token}@{protocol_removed}"
        else:
            repo_url_with_creds = repo_url

        Repo.clone_from(repo_url_with_creds, repo_dir, branch=branch)
    else:
        print(f"Found existing repo at {repo_dir}. Pulling latest changes...")
        repo = Repo(repo_dir)
        origin = repo.remotes.origin
        origin.pull(branch)

def commit_and_push_changes(repo_dir, commit_message, branch, username, token):
    """
    Stages changes, commits, and pushes to the remote repository.
    """
    repo = Repo(repo_dir)

    # Ensure we're on the desired branch
    if repo.active_branch.name != branch:
        print(f"Checking out branch '{branch}'...")
        repo.git.checkout(branch)

    # Stage all changes
    repo.git.add(A=True)

    # Commit only if there is something to commit
    if repo.is_dirty(untracked_files=True):
        print("Committing changes...")
        repo.index.commit(commit_message)

        # If we have creds, update the remote URL
        if username and token:
            origin = repo.remote("origin")
            old_url = origin.url.replace("https://", "")
            new_url = f"https://{username}:{token}@{old_url}"
            origin.set_url(new_url)

        print("Pushing changes to remote...")
        repo.remotes.origin.push(branch)
    else:
        print("No changes to commit.")

def ini_to_dict(file_path):
    """
    Parse an INI-like .pca file into a Python dict.
    """
    parser = configparser.ConfigParser()
    parser.optionxform = str  # preserve case of keys
    parser.read(file_path)

    data_dict = {}
    for section in parser.sections():
        section_dict = {}
        for key, value in parser.items(section):
            try:
                if "." in value:
                    section_dict[key] = float(value)
                else:
                    section_dict[key] = int(value)
            except ValueError:
                section_dict[key] = value
        data_dict[section] = section_dict
    return data_dict

def process_pca_files(settings):
    """
    Convert .pca -> .json, archive .pca, leave readme, copy .json to local git repo, commit & push.
    """
    input_dir = settings["INPUT_DIR"]
    output_dir = settings["OUTPUT_DIR"]
    archive_dir = settings["ARCHIVE_DIR"]

    # Make sure directories exist
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(archive_dir, exist_ok=True)

    for filename in os.listdir(input_dir):
        if filename.lower().endswith(".pca"):
            ini_path = os.path.join(input_dir, filename)
            base_name = os.path.splitext(filename)[0]
            json_filename = base_name + ".json"
            json_path = os.path.join(output_dir, json_filename)

            # Convert PCA -> JSON
            data = ini_to_dict(ini_path)
            with open(json_path, "w") as f:
                json.dump(data, f, indent=4)

            # Copy .pca to archive
            shutil.copy2(ini_path, os.path.join(archive_dir, filename))

            # Leave a small .txt readme in input folder
            readme_filename = f"{base_name}_metadataparser_readme.txt"
            readme_path = os.path.join(input_dir, readme_filename)
            with open(readme_path, "w") as readme_file:
                readme_file.write(
                    f"This file indicates that '{filename}' has been parsed and archived.\n"
                    f"JSON output is at '{output_dir}'. A copy of the original is in '{archive_dir}'."
                )

    # Now copy new/updated JSON to local repo
    repo_dir = settings["GIT_LOCAL_REPO_DIR"]
    if repo_dir and os.path.exists(repo_dir):
        json_repo_subfolder = os.path.join(repo_dir, "json")
        os.makedirs(json_repo_subfolder, exist_ok=True)

        # Copy all .json from OUTPUT_DIR -> GIT_LOCAL_REPO_DIR/json
        for json_file in os.listdir(output_dir):
            if json_file.lower().endswith(".json"):
                src = os.path.join(output_dir, json_file)
                dst = os.path.join(json_repo_subfolder, json_file)
                shutil.copy2(src, dst)

        # Commit and push
        commit_and_push_changes(
            repo_dir=repo_dir,
            commit_message="Auto-commit: PCA to JSON updates",
            branch=settings["BRANCH"],
            username=settings["USERNAME"],
            token=settings["TOKEN"]
        )

def main():
    try:
        settings = read_config()

        # Initialize or update local Git repo if specified
        if settings["GIT_LOCAL_REPO_DIR"]:
            init_or_update_repo(
                repo_dir=settings["GIT_LOCAL_REPO_DIR"],
                repo_url=settings["REPO_URL"],
                branch=settings["BRANCH"],
                username=settings["USERNAME"],
                token=settings["TOKEN"]
            )

        # Process .pca files
        process_pca_files(settings)

        print("All processing complete.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
