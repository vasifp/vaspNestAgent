# Jira Integration Guide

This guide explains how to set up and use the Jira integration for vaspNestAgent.

## Overview

The integration provides:
- **Automatic ticket transitions** when PRs are opened/merged
- **PR links** added as comments to Jira tickets
- **Ticket validation** to ensure PRs reference Jira tickets
- **Script to create stories** from the project specification

## Setup

### Step 1: Get Jira API Token

1. Go to [Atlassian API Tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token"
3. Give it a name like "vaspNestAgent GitHub Integration"
4. Copy the token (you won't see it again!)

### Step 2: Add GitHub Secrets

Add these secrets to your GitHub repository:

1. Go to your repository → Settings → Secrets and variables → Actions
2. Add the following secrets:

| Secret Name | Value |
|-------------|-------|
| `JIRA_BASE_URL` | `https://vaspinet.atlassian.net` |
| `JIRA_USER_EMAIL` | Your Atlassian account email |
| `JIRA_API_TOKEN` | The API token from Step 1 |

### Step 3: Configure Jira Project

Ensure your Jira project (VASPNET) has these workflow transitions:
- **To Do** → **In Progress**
- **In Progress** → **In Review**
- **In Review** → **Done**

The GitHub workflow will transition tickets to "In Review" when a PR is opened and "Done" when merged.

## Usage

### Branch Naming Convention

Include the Jira ticket ID in your branch name:

```bash
# Feature branches
git checkout -b feature/SCRUM-123-add-temperature-alerts

# Bug fix branches
git checkout -b fix/SCRUM-456-fix-cooldown-logic

# Hotfix branches
git checkout -b hotfix/SCRUM-789-critical-fix
```

### Commit Messages

Include the ticket ID in commit messages:

```bash
git commit -m "SCRUM-123: Add temperature alert feature"
git commit -m "SCRUM-123: Fix unit tests"
```

### Pull Request Titles

Include the ticket ID in PR titles:

```
SCRUM-123: Add temperature alert feature
```

### What Happens Automatically

1. **PR Opened:**
   - Ticket transitions to "In Review"
   - Comment added with PR link and details

2. **PR Merged:**
   - Ticket transitions to "Done"
   - Comment added with merge details

3. **PR Closed (not merged):**
   - Comment added noting PR was closed

4. **No Ticket Found:**
   - Warning displayed in PR checks
   - PR is not blocked (soft validation)

## Creating Jira Stories

### Option 1: Use the Script

```bash
# Set environment variables
export JIRA_BASE_URL="https://vaspinet.atlassian.net"
export JIRA_USER_EMAIL="your-email@example.com"
export JIRA_API_TOKEN="your-api-token"
export JIRA_PROJECT_KEY="SCRUM"

# Dry run to see what will be created
python scripts/create-jira-stories.py --dry-run

# Create all stories
python scripts/create-jira-stories.py

# Create specific story
python scripts/create-jira-stories.py --story 5
```

### Option 2: Manual Creation

See [docs/jira-stories.md](jira-stories.md) for all story definitions that can be manually created in Jira.

### Option 3: CSV Import

1. Export stories to CSV format
2. Go to Jira → Project Settings → Import Issues
3. Upload the CSV file

## Workflow Example

```bash
# 1. Create a branch with ticket ID
git checkout -b feature/SCRUM-42-add-humidity-display

# 2. Make changes
# ... edit files ...

# 3. Commit with ticket ID
git commit -m "SCRUM-42: Add humidity display to dashboard"

# 4. Push and create PR
git push -u origin feature/SCRUM-42-add-humidity-display

# 5. Create PR with ticket in title
# Title: "SCRUM-42: Add humidity display to dashboard"

# 6. Jira ticket automatically moves to "In Review"

# 7. After PR is merged, ticket moves to "Done"
```

## Troubleshooting

### Ticket Not Transitioning

1. Check that the ticket ID format is correct: `VASPNET-123`
2. Verify the workflow transition names match ("In Review", "Done")
3. Check GitHub Actions logs for errors
4. Ensure the API token has write permissions

### Authentication Errors

1. Verify `JIRA_USER_EMAIL` is your Atlassian account email
2. Regenerate the API token if expired
3. Check the token has the correct permissions

### Ticket Not Found

1. Ensure the ticket exists in the SCRUM project
2. Check the ticket ID is in the branch name or PR title
3. The pattern is case-insensitive: `SCRUM-123` or `scrum-123`

## GitHub Actions Workflow

The integration is defined in `.github/workflows/jira-integration.yml`:

```yaml
# Triggers on:
- Pull request opened/edited/closed/reopened
- Push to main/develop
- Branch creation (feature/*, fix/*, hotfix/*)

# Jobs:
- extract-ticket: Find Jira ticket ID
- pr-opened: Transition to "In Review"
- pr-merged: Transition to "Done"
- pr-closed: Add comment
- validate-ticket: Warn if no ticket found
```

## Best Practices

1. **Always include ticket ID** in branch names for automatic linking
2. **Use consistent naming** for easy tracking
3. **Keep PRs focused** on single tickets when possible
4. **Update ticket status** manually if automation fails
5. **Review Jira comments** to verify integration is working

## Security Notes

- API tokens should be stored as GitHub Secrets, never in code
- Use a service account for production integrations
- Rotate API tokens periodically
- Limit token permissions to what's needed
