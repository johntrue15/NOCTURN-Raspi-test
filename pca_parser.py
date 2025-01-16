#!/usr/bin/env python3

import configparser
import json
import os
import shutil
import urllib.parse
import getpass  # NEW: to get local username reliably
from git import Repo

def read_config():
    """Reads settings from config.ini (same directory) and returns them as a dictionary,
       replacing {LOCALUSER} with the actual username."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.ini")

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    config = configparser.ConfigParser()
    config.read(config_path)

    # Detect the username of the local device
    local_user = getpass.getuser()
    
    # Pull raw values from config
    input_dir   = config.get("General", "INPUT_DIR")
    output_dir  = config.get("General", "OUTPUT_DIR")
    archive_dir = config.get("General", "ARCHIVE_DIR")
    repo_dir    = config.get("General", "GIT_LOCAL_REPO_DIR")

    # Replace the placeholder {LOCALUSER} with the actual username
    input_dir   = input_dir.replace("{LOCALUSER}", local_user)
    output_dir  = output_dir.replace("{LOCALUSER}", local_user)
    archive_dir = archive_dir.replace("{LOCALUSER}", local_user)
    repo_dir    = repo_dir.replace("{LOCALUSER}", local_user)

    # Read Git settings
    repo_url = config.get("Git", "REPO_URL")
    branch   = config.get("Git", "BRANCH", fallback="main")
    username = config.get("Git", "USERNAME", fallback="")
    token    = config.get("Git", "PERSONAL_ACCESS_TOKEN", fallback="")

    # Build final settings dict
    settings = {
        "INPUT_DIR": input_dir,
        "OUTPUT_DIR": output_dir,
        "ARCHIVE_DIR": archive_dir,
        "GIT_LOCAL_REPO_DIR": repo_dir,
        "REPO_URL": repo_url,
        "BRANCH": branch,
        "USERNAME": username,
        "TOKEN": token
    }
    return settings

def init_or_update_repo(repo_dir, repo_url, branch, username, token):
    """(Same as before, just ensure no path changes needed.)"""
    if not os.path.exists(repo_dir):
        print(f"Cloning repository from {repo_url} into {repo_dir}...")
        os.makedirs(repo_dir, exist_ok=True)

        if username and token:
            protocol_removed = repo_url.replace("https://", "")
            username_encoded = urllib.parse.quote(username, safe="")
            token_encoded    = urllib.parse.quote(token, safe="")
            repo_url_with_creds = f"https://{username_encoded}:{token_encoded}@{protocol_removed}"
        else:
            repo_url_with_creds = repo_url

        Repo.clone_from(repo_url_with_creds, repo_dir, branch=branch)
    else:
        print(f"Found existing repo at {repo_dir}. Pulling latest changes...")
        repo = Repo(repo_dir)
        origin = repo.remotes.origin
        origin.pull(branch)

def commit_and_push_changes(repo_dir, commit_message, branch, username, token):
    """(Same as before, uses URL-encoded credentials if provided.)"""
    repo = Repo(repo_dir)
    if repo.active_branch.name != branch:
        print(f"Checking out branch '{branch}'...")
        repo.git.checkout(branch)

    repo.git.add(A=True)

    if repo.is_dirty(untracked_files=True):
        print("Committing changes...")
        repo.index.commit(commit_message)

        if username and token:
            origin = repo.remote("origin")
            old_url = origin.url.replace("https://", "")
            username_encoded = urllib.parse.quote(username, safe="")
            token_encoded    = urllib.parse.quote(token, safe="")
            new_url = f"https://{username_encoded}:{token_encoded}@{old_url}"
            origin.set_url(new_url)

        print("Pushing changes to remote...")
        repo.remotes.origin.push(branch)
    else:
        print("No changes to commit.")

def ini_to_dict(file_path):
    """(Same as before, parse .pca -> dict.)"""
    parser = configparser.ConfigParser()
    parser.optionxform = str
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
    """(Same as before, just uses updated settings for directories.)"""
    input_dir   = settings["INPUT_DIR"]
    output_dir  = settings["OUTPUT_DIR"]
    archive_dir = settings["ARCHIVE_DIR"]

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(archive_dir, exist_ok=True)

    for filename in os.listdir(input_dir):
        if filename.lower().endswith(".pca"):
            ini_path   = os.path.join(input_dir, filename)
            base_name  = os.path.splitext(filename)[0]
            json_file  = base_name + ".json"
            json_path  = os.path.join(output_dir, json_file)

            data = ini_to_dict(ini_path)
            with open(json_path, "w") as f:
                json.dump(data, f, indent=4)

            shutil.copy2(ini_path, os.path.join(archive_dir, filename))

            readme_filename = f"{base_name}_metadataparser_readme.txt"
            readme_path     = os.path.join(input_dir, readme_filename)
            with open(readme_path, "w") as readme_file:
                readme_file.write(
                    f"This file indicates that '{filename}' has been parsed and archived.\n"
                    f"JSON output is at '{output_dir}'. A copy of the original is in '{archive_dir}'."
                )

    # If pushing changes to Git
    repo_dir = settings["GIT_LOCAL_REPO_DIR"]
    if repo_dir and os.path.exists(repo_dir):
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

def main():
    try:
        settings = read_config()

        if settings["GIT_LOCAL_REPO_DIR"]:
            init_or_update_repo(
                repo_dir=settings["GIT_LOCAL_REPO_DIR"],
                repo_url=settings["REPO_URL"],
                branch=settings["BRANCH"],
                username=settings["USERNAME"],
                token=settings["TOKEN"]
            )

        process_pca_files(settings)
        print("All processing complete.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
