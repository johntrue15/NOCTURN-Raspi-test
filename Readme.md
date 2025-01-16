
flowchart LR
    A[Main Repo: Click 'Start New Facility'] --> B[New Repo Creation via Template]
    B --> C[GitHub Actions sets up template (ReadMe & config)]
    C --> D[User modifies config.ini, opens PR -> main branch of new repo]
    D --> E[GitHub Actions merges PR, updates README to Step 3]
    E --> F[User sets Windows Shared Folder path, commits]
    F --> G[GitHub Actions checks path, updates README to Step 4]
    G --> H[User flashes Pi, obtains Device Flow code]
    H --> I[Pi device flow authorized, merges into main, updates README to Step 5]
    I --> J[User places .pca in shared folder]
    J --> K[GitHub Actions detects new metadata, triggers Release]
```
