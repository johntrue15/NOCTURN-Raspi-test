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

# Function to prompt for branch
get_branch_name() {
    while true; do
        read -p "Enter branch name (Test-1-16/main): " branch_name
        # Default to Test-1-16 if empty
        if [ -z "$branch_name" ]; then
            branch_name="Test-1-16"
        fi
        # Validate branch name
        if [[ "$branch_name" == "Test-1-16" ]] || [[ "$branch_name" == "main" ]]; then
            break
        else
            echo "Invalid branch name. Please enter 'Test-1-16' or 'main'"
        fi
    done
    echo "$branch_name"
}

# Main setup
echo "Setting up Git configurations..."

# Get GitHub credentials and branch
GITHUB_TOKEN=$(get_github_token)
GITHUB_USERNAME=$(get_github_username)
BRANCH_NAME=$(get_branch_name)

# Set up git credentials
echo "https://$GITHUB_USERNAME:$GITHUB_TOKEN@github.com" > /root/.git-credentials
chmod 600 /root/.git-credentials

# Configure git globally
git config --global credential.helper store
git config --global user.name "PCA Parser"
git config --global user.email "$GITHUB_USERNAME@users.noreply.github.com"
git config --global init.defaultBranch "main"
git config --global pull.rebase false

# Initialize git repository if it doesn't exist
cd /opt/pca_parser/gitrepo
if [ ! -d .git ]; then
    git init
    git remote add origin "https://github.com/$GITHUB_USERNAME/NOCTURN-Raspi-test.git"
    # Create and switch to specified branch
    git fetch origin
    git checkout -b "$BRANCH_NAME" "origin/$BRANCH_NAME"
fi

# Configure repository
git config remote.origin.url "https://github.com/$GITHUB_USERNAME/NOCTURN-Raspi-test.git"

# Test the connection
echo "Testing GitHub connection..."
if git ls-remote >/dev/null 2>&1; then
    echo "GitHub configuration successful!"
    
    # Ensure we're on the correct branch and it's up to date
    git fetch origin
    git checkout "$BRANCH_NAME" || git checkout -b "$BRANCH_NAME" "origin/$BRANCH_NAME"
    git pull origin "$BRANCH_NAME" || true
    
    echo "Repository setup completed successfully on branch: $BRANCH_NAME"
else
    echo "Error: Could not connect to GitHub. Please check your credentials and try again."
    exit 1
fi

# Set correct permissions
chown -R root:root /opt/pca_parser/gitrepo
chmod -R 755 /opt/pca_parser/gitrepo

verify_git_setup() {
    echo "Verifying git configuration..."
    echo "Current branch:"
    git branch --show-current
    echo "Remote configuration:"
    git remote -v
    echo "Testing repository access..."
    if git fetch origin --quiet 2>/dev/null; then
        echo "✓ Repository access verified"
        return 0
    else
        echo "✗ Repository access failed"
        return 1
    fi
}

verify_git_setup || echo "Warning: Git verification failed"
echo "Git configuration completed successfully!" 