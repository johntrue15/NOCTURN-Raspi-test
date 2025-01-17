#!/bin/bash

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root"
    exit 1
fi

# Add at the beginning after root check
echo "Verifying Git dependencies..."
if ! pip3 show gitpython >/dev/null 2>&1; then
    echo "Installing gitpython..."
    pip3 install gitpython
fi

if ! pip3 show configparser >/dev/null 2>&1; then
    echo "Installing configparser..."
    pip3 install configparser
fi

# Function to prompt for GitHub token
get_github_token() {
    while true; do
        read -p "Enter your GitHub personal access token: " github_token
        if [ -n "$github_token" ]; then
            # Test token validity silently
            if curl -s -H "Authorization: token $github_token" https://api.github.com/user >/dev/null 2>&1; then
                echo "Token validated successfully" >&2
                echo "$github_token"  # Output token only
                return 0
            else
                echo "Invalid token. Please check and try again." >&2
            fi
        else
            echo "Token cannot be empty. Please try again." >&2
        fi
    done
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
echo "$GITHUB_TOKEN" > /tmp/git_token  # Store token temporarily
GITHUB_USERNAME=$(get_github_username)
BRANCH_NAME=$(get_branch_name)

# Set up git credentials
printf "https://%s:%s@github.com\n" "$GITHUB_USERNAME" "$GITHUB_TOKEN" > /root/.git-credentials
chmod 600 /root/.git-credentials

# Configure git globally
git config --global credential.helper store
git config --global user.name "$GITHUB_USERNAME"
git config --global user.email "jtrue15@ufl.edu"
git config --global init.defaultBranch "main"
git config --global pull.rebase false

# Initialize git repository if it doesn't exist
cd /opt/pca_parser/gitrepo
if [ ! -d .git ]; then
    git init
    REPO_URL="https://${GITHUB_TOKEN}@github.com/${GITHUB_USERNAME}/NOCTURN-Raspi-test.git"
    git remote add origin "$REPO_URL"
    # Create and switch to specified branch
    git fetch origin
    git checkout -b "$BRANCH_NAME" "origin/$BRANCH_NAME"
fi

# Configure repository
REPO_URL="https://${GITHUB_TOKEN}@github.com/${GITHUB_USERNAME}/NOCTURN-Raspi-test.git"
git config remote.origin.url "$REPO_URL"

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

test_git_operations() {
    echo "Testing Git operations..."
    
    # Create test file
    echo "test" > test.txt
    
    # Try git operations
    if git add test.txt && \
       git commit -m "Test commit" && \
       git push origin "$BRANCH_NAME"; then
        echo "Git operations test successful"
        git rm test.txt
        git commit -m "Remove test file"
        git push origin "$BRANCH_NAME"
        return 0
    else
        echo "Git operations test failed"
        return 1
    fi
}

# Add test after repository setup
test_git_operations || echo "Warning: Git operations test failed" 