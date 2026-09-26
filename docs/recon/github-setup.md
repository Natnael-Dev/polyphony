# GitHub Public Repository Initialization & Push Guide

This guide provides exact, step-by-step instructions for creating the public GitHub repository and pushing the local Dark Factory codebase for submission.

---

## 1. Create Public Repository on GitHub

1. Open your browser and navigate to [https://github.com/new](https://github.com/new).
2. Set **Repository name** (recommended choices from our project branding):
   - `dark-factory-pocketful`
   - `pocketful-dark-factory`
   - `band-dark-factory`
3. Set Visibility: **Public** *(Mandatory: Hackathon judges must be able to clone and inspect without authentication)*.
4. **DO NOT** check:
   - "Add a README file"
   - "Add .gitignore"
   - "Choose a license"  
   *(The repository must be completely empty so our existing commit history pushes cleanly)*.
5. Click **Create repository**.

---

## 2. Push Local Commits (PowerShell / Terminal)

Open PowerShell in the workspace root (`c:\Users\HP\dev\WeAreDevelopers x BAND`):

```powershell
# Step 1: Navigate to repository root
cd "c:\Users\HP\dev\WeAreDevelopers x BAND"

# Step 2: Verify git status is clean and local tracking files are ignored
git status
```

> [!CRITICAL]
> **PRE-PUSH PRIVACY AUDIT**:
> Verify that `git status` does **NOT** list `PROGRESS.md`, `SESSION_LOG.md`, `DECISIONS.md`, or any `.env` files. If any appear, verify `.gitignore` before proceeding.

```powershell
# Step 3: Ensure current branch is named 'main'
git branch -M main

# Step 4: Link your new GitHub remote
# (Replace <YOUR_GITHUB_USERNAME> and <REPO_NAME> with your actual GitHub details)
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/<REPO_NAME>.git

# Step 5: Verify the remote URL
git remote -v

# Step 6: Push all commits and set upstream tracking
git push -u origin HEAD
```

---

## 3. Verify Remote Repository Structure

Once pushed, open your repository on GitHub (`https://github.com/<YOUR_GITHUB_USERNAME>/<REPO_NAME>`) and verify that:
1. The root contains:
   - `README.md`
   - `FACTORY.md`
   - `mandates/` (`architect.md`, `developer.md`, `qa-auditor.md`)
   - `stage-1/`
   - `docs/` (`docs/STATE.md`, `docs/recon/`)
   - `band/`
2. **Neither** `hackathon_docs/` nor local tracking files (`PROGRESS.md`, `SESSION_LOG.md`, `DECISIONS.md`) appear in the public file listing.
3. Your commit log shows clean atomic commits matching your local history.
