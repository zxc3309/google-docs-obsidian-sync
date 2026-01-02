# Google Drive ↔ Obsidian Vault Sync

Automatically synchronize Google Docs (from one Google account) with Markdown files in your Obsidian vault (stored in another Google account's Drive).

## Architecture

```
Local Obsidian Vault (/Users/weilinchen/Documents/CEsecondbrain)
    ↕ (Obsidian Sync - for multi-device sync)
Other Devices

Local Obsidian Vault
    ↕ (Google Drive Desktop Client - Account B)
Google Drive Account B (Vault Copy)
    ↕ (Railway - This Sync Program)
Google Drive Account A (Google Docs)
```

## Features

- **Bi-directional sync**: Changes in Google Docs → Markdown, and Markdown → Google Docs
- **Conflict detection**: Alerts when both sides are modified simultaneously
- **Automatic conversion**: Google Docs HTML → Markdown with proper formatting
- **Scheduled polling**: Configurable sync interval
- **Railway deployment**: Runs in the cloud, no local machine needed
- **Multi-account support**: Different Google accounts for Docs and Vault

## Quick Start

### Prerequisites

1. Two Google accounts:
   - **Account A**: Contains your Google Docs
   - **Account B**: Contains your Obsidian vault in Google Drive

2. Google Drive Desktop Client installed (logged in with Account B)

3. Obsidian vault synced to Google Drive via Desktop Client

### Local Development

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Google Cloud credentials** (see SETUP_GUIDE.md)

3. **Create config file**:
   ```bash
   cp config.yaml.example config.yaml
   # Edit config.yaml with your settings
   ```

4. **Set environment variables**:
   ```bash
   export ACCOUNT_A_CREDENTIALS_PATH="path/to/account_a_service_account.json"
   export ACCOUNT_B_CREDENTIALS_PATH="path/to/account_b_service_account.json"
   ```

5. **Run sync**:
   ```bash
   # Run once
   python sync.py --once

   # Run continuously with 5-minute interval
   python sync.py --interval 300

   # Show status
   python sync.py --status
   ```

## Railway Deployment

1. **Push to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/your-repo.git
   git push -u origin main
   ```

2. **Deploy to Railway**:
   - Connect your GitHub repository
   - Set environment variables (see SETUP_GUIDE.md)
   - Deploy as Worker

3. **Configure environment variables** in Railway:
   - `ACCOUNT_A_CREDENTIALS`: Service Account JSON (Account A)
   - `ACCOUNT_B_CREDENTIALS`: Service Account JSON (Account B)
   - `VAULT_FOLDER_ID`: Google Drive folder ID for vault
   - `CONFIG_YAML`: Your config.yaml content (or use file)
   - `SYNC_INTERVAL`: Sync interval in seconds (e.g., 300)
   - `SHEET_ID` (optional): Google Sheet ID for mappings (share with Account A service account)
   - `SHEET_RANGE` (optional): Range to read, default `Sheet1!A:B` with header row `doc_id, vault_path`

## Configuration

Edit `config.yaml`:

```yaml
sync_interval: 300  # seconds

vault_folder_id: "your_vault_folder_id"

mappings:
  - doc_id: "google_doc_id_from_account_a"
    vault_path: "path/in/vault.md"
```

### Using Google Sheet for mappings

- Set `SHEET_ID` (and optionally `SHEET_RANGE`, default `Sheet1!A:B`) in Railway.
- Share the Sheet with the Account A service account email so it can read it.
- First row headers must be `doc_id` and `vault_path`; data rows list each mapping.
- When `SHEET_ID` is set, mappings from the Sheet override `config.yaml`/`CONFIG_YAML`.

### Finding IDs

- **Google Doc ID**: From URL `https://docs.google.com/document/d/DOC_ID/edit`
- **Folder ID**: From URL `https://drive.google.com/drive/folders/FOLDER_ID`

## Usage

### Command Line Options

```bash
python sync.py [OPTIONS]

Options:
  --config PATH     Path to config file (default: config.yaml)
  --once            Run sync once and exit
  --interval SEC    Sync interval in seconds
  --status          Show current sync status
  --debug           Enable debug logging
```

### Conflict Resolution

When both Google Doc and Markdown are modified since last sync:

1. Sync will detect the conflict and log it
2. Check `conflicts.log` for details
3. Manually review and resolve (keep one version or merge)
4. Next sync will proceed based on modification times

## Project Structure

```
.
├── sync.py                  # Main entry point
├── modules/
│   ├── auth.py             # Google authentication
│   ├── gdrive_client.py    # Drive API wrapper
│   ├── converter.py        # Doc ↔ Markdown conversion
│   ├── sync_engine.py      # Core sync logic
│   └── conflict_handler.py # Conflict management
├── config.yaml.example     # Configuration template
├── requirements.txt        # Python dependencies
├── Procfile               # Railway deployment
└── README.md              # This file
```

## How It Works

1. **Polling**: Every X seconds, check all mapped files
2. **Change Detection**: Compare modification times with last sync
3. **Direction Determination**:
   - If only Doc changed → sync to Markdown
   - If only Markdown changed → sync to Doc
   - If both changed → flag as conflict
4. **Conversion**:
   - Doc → Markdown: Export as HTML, convert with markdownify
   - Markdown → Doc: Convert to plain text, update via Docs API
5. **State Tracking**: Save sync state to `.sync_state.json` in vault

## Troubleshooting

### Authentication Errors

- Verify Service Account credentials are valid
- Check that Service Accounts have access to both Google Drives
- Ensure API scopes include Drive and Docs

### Sync Not Working

- Check logs for error messages
- Verify vault_folder_id is correct
- Ensure mappings use correct doc_id and vault_path
- Test with `--once` and `--debug` flags

### Conflicts

- Review `conflicts.log`
- Manually resolve by editing one version
- Next sync will detect the newer version

## Support

For issues, questions, or contributions:
- Check SETUP_GUIDE.md for detailed setup instructions
- Review logs with `--debug` flag
- Check Railway logs if deployed

## License

MIT
