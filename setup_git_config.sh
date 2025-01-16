#!/bin/bash

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root"
    exit 1
fi

# Function to prompt for GitHub token
get_github_token() {
    while true; do
        read -p "Enter your GitHub personal access token: " github_token
        if [ -n "$github_token" ]; then
            break
        else
            echo "Token cannot be empty. Please try again."
        fi
    done
    echo "$github_token"
}

# Function to prompt for GitHub username
get_github_username() {
    while true; do
        read -p "Enter your GitHub username: " github_username
        if [ -n "$github_username" ]; then
            break
        else
            echo "Username cannot be empty. Please try again."
        fi
    done
    echo "$github_username"
}

# Main setup
echo "Setting up Git configurations..."

# Get GitHub credentials
GITHUB_TOKEN=$(get_github_token)
GITHUB_USERNAME=$(get_github_username)

# Set up git credentials
echo "https://$GITHUB_USERNAME:$GITHUB_TOKEN@github.com" > /root/.git-credentials
chmod 600 /root/.git-credentials

# Configure git globally
cd /opt/pca_parser/gitrepo
git config --global credential.helper store
git config --global user.name "PCA Parser"
git config --global user.email "$GITHUB_USERNAME@users.noreply.github.com"

# Configure repository
git config remote.origin.url "https://github.com/$GITHUB_USERNAME/NOCTURN-Raspi-test.git"

# Test the connection
echo "Testing GitHub connection..."
if git ls-remote >/dev/null 2>&1; then
    echo "GitHub configuration successful!"
else
    echo "Error: Could not connect to GitHub. Please check your credentials and try again."
    exit 1
fi

# Set correct permissions
chown -R root:root /opt/pca_parser/gitrepo
chmod -R 755 /opt/pca_parser/gitrepo

echo "Git configuration completed successfully!" 