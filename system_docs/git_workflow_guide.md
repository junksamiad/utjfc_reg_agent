# Git Workflow Guide - UTJFC Registration Agent

## Overview

This document outlines the Git branching strategy and workflow for the UTJFC Registration Agent project. The workflow follows a three-tier approach designed to ensure code quality, testing, and stable production releases.

## Branch Structure

### 🚀 Production Branch: `main`
- **Purpose**: Production-ready code deployed to live environment
- **Deployment**: AWS Elastic Beanstalk production environment
- **Protection**: Only accepts merges from `dev` branch
- **Stability**: Always deployable, thoroughly tested code

### 🧪 Development Branch: `dev` 
- **Purpose**: Integration and testing environment
- **Testing**: All features are integrated and tested here
- **Staging**: Pre-production environment for validation
- **Quality Gate**: Features must pass testing before merging to `main`

### 🔧 Feature Branches: `feature/*`
- **Purpose**: Individual feature development
- **Naming**: `feature/feature-name` (e.g., `feature/automated-payment-chasing`)
- **Isolation**: Each feature developed in isolation
- **Merge Target**: Always merge into `dev` branch first

## Workflow Process

### 1. Starting a New Feature

```bash
# Ensure you're on dev and up to date
git checkout dev
git pull origin dev

# Create new feature branch
git checkout -b feature/feature-name

# Push to remote and set upstream
git push -u origin feature/feature-name
```

### 2. Developing the Feature

```bash
# Regular commits during development
git add .
git commit -m "Add feature implementation"
git push origin feature/feature-name

# Keep feature branch updated with dev (if needed)
git checkout dev
git pull origin dev
git checkout feature/feature-name
git merge dev
```

### 3. Feature Ready for Testing

```bash
# Ensure feature is complete and tested
git checkout feature/feature-name
git push origin feature/feature-name

# Switch to dev branch
git checkout dev
git pull origin dev

# Merge feature into dev
git merge feature/feature-name
git push origin dev

# Optional: Delete feature branch if complete
git branch -d feature/feature-name
git push origin --delete feature/feature-name
```

### 4. Deploy to Production

```bash
# After dev testing is complete
git checkout main
git pull origin main

# Merge dev into main
git merge dev
git push origin main

# Tag the release (recommended)
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

## Branch Protection Rules

### Main Branch Protection
- **Require pull request reviews**: Recommended for team development
- **Require status checks**: Ensure CI/CD passes
- **Require up-to-date branches**: Force rebase before merge
- **Restrict pushes**: Only allow merges from `dev`

### Dev Branch Protection
- **Allow feature merges**: Accept merges from `feature/*` branches
- **Require basic checks**: Ensure code quality
- **Integration testing**: Run automated tests

## Feature Branch Naming Conventions

### Standard Formats
```
feature/feature-name               # New feature
feature/automated-payment-chasing  # Current example
bugfix/issue-description          # Bug fixes
hotfix/critical-fix               # Emergency production fixes
chore/maintenance-task            # Maintenance work
```

### Examples
- `feature/sms-notification-system`
- `feature/sibling-discount-automation`
- `bugfix/payment-webhook-timeout`
- `hotfix/registration-validation-error`
- `chore/update-dependencies`

## Deployment Environments

### Production Environment
- **Branch**: `main`
- **URL**: https://urmstontownjfc.co.uk
- **AWS**: Elastic Beanstalk production environment
- **Database**: Production Airtable base

### Development Environment  
- **Branch**: `dev`
- **URL**: Development domain (if applicable)
- **AWS**: Development/staging environment
- **Database**: Development Airtable base or test data

## Best Practices

### Commit Messages
```bash
# Good commit messages
git commit -m "Add automated payment chasing system"
git commit -m "Fix webhook timeout handling"
git commit -m "Update payment validation logic"

# Avoid generic messages
git commit -m "Updates"
git commit -m "Fix stuff"
git commit -m "WIP"
```

### Feature Development
1. **Small, focused features**: Keep features manageable
2. **Regular commits**: Commit early and often
3. **Test locally**: Ensure feature works before pushing
4. **Clean history**: Squash commits if needed before merge

### Code Quality
1. **Test thoroughly**: Test all functionality before merging
2. **Document changes**: Update documentation as needed
3. **Review code**: Self-review before creating pull requests
4. **Follow conventions**: Maintain consistent code style

## Emergency Procedures

### Hotfix Process
```bash
# Create hotfix from main
git checkout main
git pull origin main
git checkout -b hotfix/critical-fix

# Implement fix
git add .
git commit -m "Fix critical production issue"
git push -u origin hotfix/critical-fix

# Merge directly to main
git checkout main
git merge hotfix/critical-fix
git push origin main

# Also merge to dev to keep in sync
git checkout dev
git merge hotfix/critical-fix
git push origin dev

# Delete hotfix branch
git branch -d hotfix/critical-fix
git push origin --delete hotfix/critical-fix
```

### Rollback Process
```bash
# Revert to previous commit
git checkout main
git revert <commit-hash>
git push origin main

# Or reset to previous tag
git reset --hard <tag-name>
git push --force-with-lease origin main
```

## Integration with Development Tools

### VS Code/IDE Integration
- Install Git extensions for visual branch management
- Use built-in merge conflict resolution
- Enable Git blame/history for code review

### CI/CD Integration
- Automated tests run on `dev` branch
- Deployment scripts triggered by `main` branch updates
- Quality gates prevent bad code from reaching production

## Current Branch Status

### Active Branches
- **`main`**: Production code (latest stable release)
- **`dev`**: Development integration branch
- **`feature/automated-payment-chasing`**: Current feature in development

### Workflow Example
```
feature/automated-payment-chasing → dev → main
        ↓                         ↓      ↓
    Development              Integration Production
```

## Troubleshooting

### Common Issues
1. **Merge conflicts**: Resolve in IDE, test, then commit
2. **Branch out of sync**: Pull latest changes before merging
3. **Accidental commits**: Use `git revert` for published commits
4. **Feature branch too old**: Merge latest `dev` into feature branch

### Recovery Commands
```bash
# Undo last commit (not pushed)
git reset --soft HEAD~1

# Undo changes to file
git checkout -- filename

# See commit history
git log --oneline -10

# Check branch status
git status
git branch -a
```

## Team Collaboration

### Pull Request Process
1. Create feature branch
2. Implement feature
3. Push to remote
4. Create pull request to `dev`
5. Code review and approval
6. Merge to `dev`
7. Test in development environment
8. Merge `dev` to `main` when ready

### Code Review Guidelines
- **Functionality**: Does the code work as expected?
- **Quality**: Is the code clean and maintainable?
- **Testing**: Are there adequate tests?
- **Documentation**: Is the code well-documented?

---

## Quick Reference

### Essential Commands
```bash
# Check current branch
git branch

# Create and switch to new branch
git checkout -b branch-name

# Switch branches
git checkout branch-name

# Merge branch
git merge branch-name

# Delete branch
git branch -d branch-name

# Push branch
git push origin branch-name

# Pull latest changes
git pull origin branch-name
```

This workflow ensures code quality, enables safe experimentation, and maintains a stable production environment while supporting rapid feature development.