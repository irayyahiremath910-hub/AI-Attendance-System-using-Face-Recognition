# GitHub Deployment Guide

## Overview
This guide provides instructions for deploying the AI Attendance System to GitHub and managing the repository for team collaboration.

## Repository Setup

### Initial Repository Creation
```bash
# Initialize repository (if not already done)
git init
git remote add origin https://github.com/yourusername/AI-Attendance-System-using-Face-Recognition.git
git branch -M main
git push -u origin main
```

### Clone for Development
```bash
git clone https://github.com/yourusername/AI-Attendance-System-using-Face-Recognition.git
cd AI-Attendance-System-using-Face-Recognition
```

## Branch Strategy

### Main Branch Protection
- Requires code review before merge
- Runs automated tests before merge
- Maintains clean, deployable code

### Development Branches
```bash
# Create feature branch
git checkout -b feature/new-feature

# Create bugfix branch
git checkout -b bugfix/issue-description

# Create hotfix branch
git checkout -b hotfix/critical-issue
```

## Commit Strategy

### Commit Guidelines
- Write descriptive commit messages
- Keep commits focused on single changes
- Use present tense ("Add feature" not "Added feature")
- Reference issues when applicable

### Commit Message Format
```
Type: Subject

Description (optional)

Fixes: #123
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation change
- `style`: Code style change
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `test`: Test addition/modification
- `chore`: Build/dependency changes

## Pull Request Workflow

### Create Pull Request
```bash
# Push feature branch
git push origin feature/new-feature

# Create PR on GitHub
# - Add descriptive title and description
# - Link related issues
# - Request reviewers
```

### Code Review
- Address reviewer feedback
- Push fixes to the same branch
- PR automatically updates

### Merge Pull Request
- Requires at least 1 approval
- All checks must pass
- Squash commits for clarity (recommended)
- Delete branch after merge

## Continuous Integration

### GitHub Actions
Automated workflows run on:
- Push to main branch
- Pull request creation
- Scheduled builds

**Configured Checks:**
- Lint Python code
- Run unit tests
- Security scanning
- Docker image build
- Database migrations test

## Deployment from GitHub

### Automated Deployment
Triggered on push to main branch:
```bash
1. Build Docker image
2. Push to registry
3. Deploy to production
4. Run smoke tests
5. Monitor application
```

### Manual Deployment
```bash
# Pull latest code
git pull origin main

# Run deployment
./deploy.sh
```

## Release Management

### Create Release
```bash
# Tag a release
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# On GitHub:
# - Go to Releases
# - Create release from tag
# - Add release notes
# - Publish release
```

### Release Checklist
- [ ] Update version in code
- [ ] Update CHANGELOG.md
- [ ] Update README.md
- [ ] Run all tests
- [ ] Test deployment
- [ ] Create git tag
- [ ] Create GitHub release
- [ ] Update documentation

## Secrets Management

### GitHub Secrets
```bash
# Configure in repository settings:
Settings > Secrets and variables > Actions

# Required secrets:
- DOCKER_HUB_USERNAME
- DOCKER_HUB_PASSWORD
- AWS_ACCESS_KEY_ID (if using AWS)
- AWS_SECRET_ACCESS_KEY (if using AWS)
- PRODUCTION_SERVER_IP
- PRODUCTION_SERVER_KEY
- DATABASE_PASSWORD
```

### Environment Variables
- Use .env.production (not committed)
- Use GitHub environment secrets
- Keep sensitive data out of code

## Team Collaboration

### Code Review
- Assign reviewers before merge
- Address all feedback
- Keep discussions professional
- Merge only after approval

### Issue Tracking
- Create issues for bugs and features
- Label issues appropriately
- Assign to team members
- Track progress with milestones

### Documentation
- Keep README.md updated
- Update CHANGELOG.md
- Document new features
- Add code comments for complex logic

## Troubleshooting

### Merge Conflicts
```bash
# Update your branch
git fetch origin
git merge origin/main

# Resolve conflicts in editor
# Mark as resolved
git add .
git commit -m "Resolve merge conflicts"
```

### Revert Commit
```bash
# Revert last commit (creates new commit)
git revert HEAD

# Revert to specific commit
git revert <commit-hash>
```

### Force Push (Use Carefully)
```bash
# Force push (only on feature branches!)
git push -f origin feature/my-feature
```

## Monitoring Deployments

### View Deployment Status
- GitHub Actions tab
- Review workflow runs
- Check deployment logs

### Rollback Deployment
```bash
# Revert to previous commit
git revert <commit-hash>
git push origin main

# Or rollback on server
git reset --hard <previous-commit>
./deploy.sh
```

## Best Practices

1. **Always branch**: Never commit directly to main
2. **Small PRs**: Keep pull requests focused and reviewable
3. **Test locally**: Run tests before pushing
4. **Document changes**: Update docs with code changes
5. **Review PRs**: Take code review seriously
6. **Keep branches updated**: Rebase regularly
7. **Meaningful commits**: Write clear commit messages
8. **Protect main**: Configure branch protection rules

## Resources

- GitHub Guides: https://guides.github.com/
- Git Documentation: https://git-scm.com/doc
- GitHub Actions: https://github.com/features/actions
- Git Workflow: https://git-scm.com/book/en/v2
