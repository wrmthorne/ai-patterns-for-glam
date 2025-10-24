# Publishing Setup Guide

This document explains how to publish the book to Hugging Face Spaces using GitHub Actions.

## Overview

- **Source code**: GitHub (private repository)
- **Published book**: Hugging Face Space (public)
- **Deployment**: Manual trigger OR automatic on `publish` branch

## One-Time Setup

### 1. Create Hugging Face Space

1. Go to https://huggingface.co/new-space
2. Choose a name: `ai-patterns-for-glam` (or similar)
3. Select license: Apache 2.0 (or your preference)
4. Choose SDK: **Static** (important!)
5. Make it Public
6. Click "Create Space"

### 2. Get Hugging Face Token

1. Go to https://huggingface.co/settings/tokens
2. Click "New token"
3. Name: `github-actions-publish`
4. Role: **Write** (needed to push to Space)
5. Copy the token (you'll need it in next step)

### 3. Configure GitHub Secrets

In your GitHub repository:

1. Go to **Settings → Secrets and variables → Actions**
2. Click **New repository secret**
3. Add these three secrets:

   **HF_TOKEN**
   - Value: The token you copied from HF

   **HF_USERNAME**
   - Value: Your HF username (e.g., `davanstrien`)

   **HF_SPACE**
   - Value: `YOUR_USERNAME/ai-patterns-for-glam` (e.g., `davanstrien/ai-patterns-for-glam`)

### 4. Enable GitHub Actions

1. Go to **Settings → Actions → General**
2. Under "Actions permissions", select **Allow all actions**
3. Click **Save**

## How to Publish

You have **two options** for publishing:

### Option 1: Manual Trigger (Recommended)

Publish whenever you're ready:

1. Go to **Actions** tab in GitHub
2. Click **Publish to Hugging Face** workflow
3. Click **Run workflow** button
4. Select branch (usually `main`)
5. Click **Run workflow**

GitHub will:
- Build the book
- Deploy to HF Space
- You'll get a ✅ or ❌ notification

### Option 2: Automatic via `publish` Branch

Create a dedicated publishing branch:

```bash
# Create and push a 'publish' branch
git checkout -b publish
git push -u origin publish

# Now any push to 'publish' triggers deployment
git checkout main
# ... make changes ...
git commit -m "Update content"

# When ready to publish:
git checkout publish
git merge main
git push  # This triggers deployment
```

**Workflow:**
1. Work on `main` branch (private, not published)
2. When ready to publish, merge `main` → `publish`
3. Push to `publish` triggers automatic deployment

## Viewing the Published Book

After deployment completes:
- **HF Space URL**: `https://huggingface.co/spaces/YOUR_USERNAME/ai-patterns-for-glam`

## Workflow Details

The GitHub Action does:

1. ✅ Checks out your code
2. ✅ Installs Quarto
3. ✅ Installs Python dependencies
4. ✅ Runs `quarto render`
5. ✅ Pushes rendered book to HF Space

## Troubleshooting

### Action fails with "permission denied"
- Check that HF_TOKEN has **Write** permission
- Verify token hasn't expired

### Book doesn't update on HF
- Check the Actions tab for error messages
- Verify HF_SPACE secret matches your Space name exactly

### Python dependencies fail
- Make sure `requirements.txt` is up to date
- Test locally: `quarto render`

## Local Preview Before Publishing

Always preview locally before publishing:

```bash
# Render and preview
quarto preview

# Or just render
quarto render

# Check _book/ folder for output
```

## Updating Content Workflow

Recommended workflow:

```bash
# 1. Work on main branch
git checkout main

# 2. Make changes, test locally
quarto preview

# 3. Commit changes
git add .
git commit -m "Add new chapter on X"
git push origin main

# 4. When ready to publish:
# Option A: Use GitHub UI manual trigger
# Option B: Merge to publish branch
git checkout publish
git merge main
git push origin publish
```

This keeps `main` as your working branch and gives you full control over when the public book updates.
