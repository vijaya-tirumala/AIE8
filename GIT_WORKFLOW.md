# Git Workflow: Upstream/Downstream Repository Pattern

This guide outlines the 4-step workflow for working with upstream and downstream repositories in the AIMS (AI Maker Space) project.

## Repository Setup

- **Upstream**: The main AIMS repository (source of truth)
- **Origin**: Your personal fork/downstream repository
- **Local**: Your local working copy

## The 4-Step Workflow

### Step 1: Pull Latest Changes from Upstream
```bash
git pull upstream main
```
- This fetches and merges the latest changes from the AIMS repository
- Ensures your local code is up-to-date with the main project
- Resolves any conflicts if they exist

### Step 2: Make Changes and Stage Them
```bash
# Make your code changes here
# Edit files, add features, fix bugs, etc.

# Stage all changes
git add .
```
- Make your modifications to the codebase
- Use `git add .` to stage all changes for commit
- Alternative: `git add <specific-file>` to stage individual files

### Step 3: Commit Changes with a Helpful Message
```bash
git commit -m "Your descriptive commit message here"
```
- Create a commit with a clear, descriptive message
- Good commit messages explain what was changed and why
- Examples:
  - `git commit -m "Add user authentication feature"`
  - `git commit -m "Fix bug in data validation logic"`
  - `git commit -m "Update documentation for API endpoints"`

### Step 4: Push Changes to Your Downstream Repository
```bash
git push origin main
```
- Pushes your committed changes to your personal fork (origin)
- Makes your changes available in your downstream repository
- Prepares for potential pull request to upstream

## Complete Workflow Example

```bash
# Step 1: Get latest changes
git pull upstream main

# Step 2: Make changes and stage them
# ... make your code changes ...
git add .

# Step 3: Commit with message
git commit -m "Implement new feature X with improved error handling"

# Step 4: Push to your fork
git push origin main
```

## Best Practices

1. **Always pull upstream first** - Ensures you're working with the latest code
2. **Make atomic commits** - Each commit should represent a single logical change
3. **Write clear commit messages** - Help others understand what you changed
4. **Test your changes** - Verify everything works before pushing
5. **Keep commits focused** - Don't mix unrelated changes in one commit

## Troubleshooting

- **Merge conflicts**: Resolve conflicts manually, then `git add .` and `git commit`
- **Push rejected**: Your local branch might be behind; try `git pull origin main` first
- **Wrong remote**: Verify your remotes with `git remote -v`

## Next Steps

After pushing to your downstream repository, you can:
- Create a pull request to contribute back to the upstream repository
- Continue making more changes following the same workflow
- Collaborate with others through your fork
