# Setup Guide

Complete setup instructions for Google Drive ↔ Obsidian Vault Sync

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Google Cloud Setup (Account A - Docs)](#google-cloud-setup-account-a---docs)
3. [Google Cloud Setup (Account B - Vault)](#google-cloud-setup-account-b---vault)
4. [Local Environment Setup](#local-environment-setup)
5. [Configuration](#configuration)
6. [Railway Deployment](#railway-deployment)
7. [Verification](#verification)

---

## Prerequisites

### Required

- Two Google accounts:
  - **Account A**: Contains your Google Docs to sync
  - **Account B**: Will store your Obsidian vault in Google Drive

- Google Drive Desktop Client installed on your computer

- Python 3.11+ (for local testing)

- Railway account (for cloud deployment)

### Optional

- Obsidian Sync subscription (for multi-device Obsidian sync)

---

## Google Cloud Setup (Account A - Docs)

These steps create a Service Account that can access your Google Docs.

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with **Account A**
3. Click "Select a project" → "New Project"
4. Name: `obsidian-sync-docs` (or your choice)
5. Click "Create"

### 2. Enable APIs

1. Navigate to "APIs & Services" → "Library"
2. Search and enable:
   - **Google Drive API**
   - **Google Docs API**

### 3. Create Service Account

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "Service Account"
3. Fill in:
   - Name: `obsidian-sync-account-a`
   - ID: (auto-generated)
   - Description: "Sync service for Google Docs"
4. Click "Create and Continue"
5. Skip role assignment (click "Continue", then "Done")

### 4. Create and Download Key

1. Click on the service account you just created
2. Go to "Keys" tab
3. Click "Add Key" → "Create new key"
4. Choose "JSON"
5. Click "Create"
6. **Save this file** as `account_a_credentials.json`
7. **Keep it secure** - this file grants access to your Google Drive

### 5. Share Google Docs with Service Account

For each Google Doc you want to sync:

1. Open the Google Doc
2. Click "Share"
3. Copy the service account email from the JSON file:
   - Look for `"client_email": "obsidian-sync-account-a@...iam.gserviceaccount.com"`
4. Paste it in the share dialog
5. Grant **Editor** access
6. Click "Send" (uncheck "Notify people")

---

## Google Cloud Setup (Account B - Vault)

Repeat similar steps for Account B (vault storage).

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. **Sign OUT and sign in with Account B**
3. Create new project: `obsidian-sync-vault`

### 2. Enable APIs

Enable:
- **Google Drive API**

(Docs API not needed for Account B)

### 3. Create Service Account

1. Create service account: `obsidian-sync-account-b`
2. Download key as `account_b_credentials.json`

### 4. Share Vault Folder with Service Account

1. In Google Drive (Account B), create or locate your vault folder
2. Right-click → "Share"
3. Share with the Account B service account email
4. Grant **Editor** access

### 5. Get Vault Folder ID

1. Open the vault folder in Google Drive
2. Look at the URL: `https://drive.google.com/drive/folders/FOLDER_ID`
3. Copy the `FOLDER_ID` part
4. Save this - you'll need it for configuration

---

## Local Environment Setup

### 1. Clone or Create Project

```bash
cd /Users/weilinchen/Documents/Sync_GDrvie_Obsidian
```

### 2. Install Python Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Setup Credentials

Place the credential files in your project directory:

```bash
# DO NOT commit these to git!
account_a_credentials.json
account_b_credentials.json
```

Or set environment variables:

```bash
export ACCOUNT_A_CREDENTIALS_PATH="/path/to/account_a_credentials.json"
export ACCOUNT_B_CREDENTIALS_PATH="/path/to/account_b_credentials.json"
```

---

## Configuration

### 1. Create Config File

```bash
cp config.yaml.example config.yaml
```

### 2. Edit config.yaml

```yaml
sync_interval: 300  # 5 minutes

vault_folder_id: "YOUR_VAULT_FOLDER_ID_HERE"

mappings:
  - doc_id: "YOUR_GOOGLE_DOC_ID"
    vault_path: "01. Inbox/notes.md"

  # Add more mappings as needed
```

### 3. Find Google Doc IDs

For each document you want to sync:

1. Open the Google Doc in your browser
2. Look at the URL:
   ```
   https://docs.google.com/document/d/1abc...xyz/edit
                                    ^^^^^^^^^^^
                                    This is the doc_id
   ```
3. Add to `mappings` in config.yaml

### 4. Test Configuration

```bash
# Test sync once
python sync.py --once --debug

# Check for errors in output
```

---

## Railway Deployment

### 1. Prepare Repository

```bash
# Initialize git if not already
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: Google Drive <-> Obsidian sync"

# Push to GitHub
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### 2. Create Railway Project

1. Go to [Railway](https://railway.app/)
2. Sign in / Create account
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your repository

### 3. Configure Environment Variables

In Railway project settings, add these variables:

#### Required Variables

```bash
# Account A credentials (entire JSON file content)
ACCOUNT_A_CREDENTIALS='{"type":"service_account","project_id":"...","private_key_id":"...","private_key":"...","client_email":"...","client_id":"...","auth_uri":"...","token_uri":"...","auth_provider_x509_cert_url":"...","client_x509_cert_url":"..."}'

# Account B credentials (entire JSON file content)
ACCOUNT_B_CREDENTIALS='{"type":"service_account",...}'

# Vault folder ID
VAULT_FOLDER_ID="your_folder_id_here"

# Sync interval (seconds)
SYNC_INTERVAL="300"
```

#### Option 1: Using CONFIG_YAML

```bash
CONFIG_YAML='
sync_interval: 300
vault_folder_id: "folder_id"
mappings:
  - doc_id: "doc_id_1"
    vault_path: "path1.md"
  - doc_id: "doc_id_2"
    vault_path: "path2.md"
'
```

#### Option 2: Using CONFIG_MAPPINGS

```bash
CONFIG_MAPPINGS='[{"doc_id":"doc_id_1","vault_path":"path1.md"},{"doc_id":"doc_id_2","vault_path":"path2.md"}]'
```

#### Option 3: Using Google Sheet (recommended for many docs)

```bash
# Required
SHEET_ID="your_google_sheet_id"          # e.g., 1Goi2qjaw26_yDPAxtKx5Mdgbr8knhSCWaeRPXiV-qTM

# Optional
SHEET_RANGE="Sheet1!A:B"                 # default; first row headers: doc_id, vault_path
```

Notes:
- Share the Sheet with the Account A service account email so it can read it.
- When `SHEET_ID` is set, mappings from the Sheet override `config.yaml` / `CONFIG_YAML` / `CONFIG_MAPPINGS`.

### 4. Deploy

1. Railway will automatically deploy when you push to GitHub
2. Check deployment logs for any errors
3. Look for "Starting sync" messages

### 5. Monitor

- Check Railway logs regularly
- Look for conflict warnings
- Monitor sync success/error counts

---

## Verification

### 1. Test Local Sync

```bash
# Run once with debug output
python sync.py --once --debug

# Expected output:
# - "Loaded sync state..."
# - "Syncing: doc_id <-> vault_path"
# - "Sync Results: ✓ Success: X"
```

### 2. Verify Files

1. Check your Google Drive (Account B)
2. Look for markdown files at specified paths
3. Content should match corresponding Google Docs

### 3. Test Bi-directional Sync

**Test 1: Doc → Markdown**

1. Edit a Google Doc (Account A)
2. Wait for sync interval or run `python sync.py --once`
3. Check markdown file in Google Drive (Account B)
4. Should reflect the changes

**Test 2: Markdown → Doc**

1. Edit markdown file via Google Drive or local Obsidian
2. Wait for sync
3. Check Google Doc
4. Should reflect the changes

**Test 3: Conflict Detection**

1. Edit both Doc and Markdown (don't sync between)
2. Run sync
3. Should log a conflict
4. Check `conflicts.log`

### 4. Verify Railway Deployment

1. Make a change to a Google Doc
2. Wait 5-10 minutes
3. Check markdown in Google Drive
4. Should be synced

---

## Common Issues

### Service Account Cannot Access Files

**Problem**: "File not found" or "Permission denied"

**Solution**:
- Verify you shared the file/folder with the service account email
- Check the email matches exactly (from credentials JSON)
- Ensure "Editor" permission was granted

### Sync State Not Saving

**Problem**: Every sync acts like first sync

**Solution**:
- Check vault folder permissions
- Verify service account can write to folder
- Look for `.sync_state.json` in vault root

### Railway Deployment Fails

**Problem**: Build or runtime errors

**Solution**:
- Check Python version in `runtime.txt` matches Railway support
- Verify `Procfile` syntax
- Check Railway logs for specific error messages
- Ensure all environment variables are set

### Markdown Formatting Issues

**Problem**: Formatting lost or incorrect

**Solution**:
- Google Docs HTML export is limited
- Complex formatting may not convert perfectly
- Consider simplifying docs for better conversion
- Check markdownify options in `converter.py`

---

## Next Steps

1. **Setup Google Drive Desktop Client**:
   - Install on your computer
   - Sign in with Account B
   - Sync the vault folder to local path
   - Point Obsidian to this local folder

2. **Setup Obsidian Sync** (optional):
   - For multi-device Obsidian sync
   - Works alongside Google Drive sync

3. **Create More Mappings**:
   - Add more docs to `config.yaml`
   - Test each mapping individually first

4. **Monitor and Adjust**:
   - Review logs regularly
   - Adjust sync interval based on usage
   - Handle conflicts promptly

---

## Security Notes

- **Never commit credentials to Git**
- Use `.gitignore` to exclude credential files
- Railway environment variables are encrypted
- Service Account keys grant full access - keep them secure
- Consider rotating keys periodically
- Use minimum necessary permissions

---

## Support

If you encounter issues:

1. Check logs with `--debug` flag
2. Verify all IDs and credentials
3. Test with single mapping first
4. Review Railway logs for deployment issues
5. Check Google Cloud Console for API errors

For questions specific to:
- Google Cloud: [Google Cloud Support](https://cloud.google.com/support)
- Railway: [Railway Discord](https://discord.gg/railway)
- Obsidian: [Obsidian Forum](https://forum.obsidian.md/)
