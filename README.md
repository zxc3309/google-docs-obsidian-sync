# Google Docs -> Obsidian Vault Sync

將 Google Docs（Account A）單向同步為 Markdown 檔案，寫入另一個 Google Drive（Account B）中的 Obsidian Vault。部署於 Railway，全自動雲端執行。

## Architecture

```
Google Drive Account A (Google Docs)
        │
        │  Service Account A 讀取 Doc，匯出 HTML
        ▼
  ┌─────────────────────┐
  │  Railway Worker      │
  │  (本程式, 每 5 分鐘)  │
  │                     │
  │  HTML → Markdown    │
  └─────────────────────┘
        │
        │  Service Account B 寫入 Markdown
        ▼
Google Drive Account B (Vault Copy)
        │
        │  Google Drive Desktop Client
        ▼
Local Obsidian Vault
```

**同步方向：單向（Google Docs → Vault），Vault 端的修改會被覆蓋。**

## Features

- **單向同步**：Google Docs HTML → Markdown，自動寫入 Vault
- **排程輪詢**：預設每 300 秒檢查一次，可自訂間隔
- **狀態追蹤**：透過 `.sync_state.json` 記錄每份文件的同步時間，只同步有變更的文件
- **雙帳號隔離**：兩個 Google 帳號各用獨立的 Service Account
- **映射設定彈性**：支援 `config.yaml`、環境變數、或 Google Sheets 作為映射來源
- **Railway 部署**：以 Worker 模式運行，搭配 Volume 持久化同步狀態

## Prerequisites

1. **兩個 Google 帳號**：
   - **Account A**：存放 Google Docs 原始文件
   - **Account B**：存放 Obsidian Vault（透過 Google Drive Desktop Client 同步至本地）

2. **兩個 GCP Service Account**（各自建在不同 GCP Project 下）：
   - Account A 的 Service Account：需對目標 Google Docs 有 Editor 權限
   - Account B 的 Service Account：需對 Vault 資料夾有 Editor 權限

3. **Google Drive Desktop Client**（登入 Account B），將 Vault 同步至本地給 Obsidian 使用

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set environment variables

```bash
# Service Account 憑證（JSON 檔案路徑，本地開發用）
export ACCOUNT_A_CREDENTIALS_PATH="path/to/account_a_service_account.json"
export ACCOUNT_B_CREDENTIALS_PATH="path/to/account_b_service_account.json"

# Vault 資料夾 ID
export VAULT_FOLDER_ID="your_vault_folder_id"
```

### 3. Create config

```bash
cp config.yaml.example config.yaml
# 編輯 config.yaml，填入 Google Doc ID 與 Vault 路徑的映射
```

### 4. Run

```bash
# 單次同步
python sync.py --once

# 持續同步（每 5 分鐘）
python sync.py --interval 300

# 查看同步狀態
python sync.py --status

# Debug 模式
python sync.py --debug
```

## Railway Deployment

### Environment Variables

| 變數 | 說明 |
|------|------|
| `ACCOUNT_A_CREDENTIALS` | Account A Service Account JSON（完整內容） |
| `ACCOUNT_B_CREDENTIALS` | Account B Service Account JSON（完整內容） |
| `VAULT_FOLDER_ID` | Account B Google Drive 中 Vault 資料夾的 ID |
| `CONFIG_YAML` | `config.yaml` 的完整內容 |
| `SYNC_INTERVAL` | 同步間隔秒數（預設 300） |
| `SHEET_ID` | （選填）Google Sheet ID，用來讀取映射 |
| `SHEET_RANGE` | （選填）Sheet 範圍，預設 `Sheet1!A:B` |

### Persistent Volume

Railway 上需掛載 Volume 至 `/data`，用來持久化 `.sync_state.json`。否則每次部署都會重新同步所有文件。

### Deploy

1. 連結 GitHub repo 至 Railway
2. 設定上述環境變數
3. 掛載 Volume 至 `/data`
4. 部署為 Worker（`Procfile`: `worker: python sync.py`）

## Configuration

### config.yaml

```yaml
sync_interval: 300

vault_folder_id: "your_vault_folder_id"

mappings:
  - doc_id: "google_doc_id"
    vault_path: "path/in/vault.md"
```

### Google Sheets 映射（選填）

設定 `SHEET_ID` 環境變數後，程式會從 Google Sheet 讀取映射，覆蓋 `config.yaml` 中的設定。

- 將 Sheet 分享給 Account A 的 Service Account email
- 第一列為標題：`doc_id`, `vault_path`
- 後續每列為一組映射

### 找到 ID

- **Google Doc ID**：URL 中 `https://docs.google.com/document/d/<DOC_ID>/edit`
- **Folder ID**：URL 中 `https://drive.google.com/drive/folders/<FOLDER_ID>`

## Project Structure

```
.
├── sync.py                  # 主程式入口
├── modules/
│   ├── auth.py              # 雙帳號 Service Account 認證
│   ├── gdrive_client.py     # Google Docs / Drive / Sheets API 封裝
│   ├── converter.py         # HTML → Markdown 轉換
│   ├── sync_engine.py       # 同步引擎（變更偵測、狀態管理）
│   └── conflict_handler.py  # 衝突偵測與記錄
├── config.yaml.example      # 設定範本
├── requirements.txt         # Python 套件
├── Procfile                 # Railway 部署設定
└── runtime.txt              # Python 版本（3.11）
```

## How It Works

1. **輪詢**：每 N 秒檢查所有映射文件
2. **變更偵測**：比對 Google Doc 修改時間與上次同步時間
3. **匯出轉換**：透過 Google Docs API 匯出 HTML，用 `markdownify` 轉為 Markdown
4. **寫入 Vault**：透過 Google Drive API（Account B 憑證）寫入對應路徑
5. **狀態儲存**：更新 `.sync_state.json`，記錄同步時間與方向

## Troubleshooting

### 認證錯誤

- 確認 Service Account JSON 格式正確
- 確認 Google Docs 已分享給 Account A 的 Service Account email
- 確認 Vault 資料夾已分享給 Account B 的 Service Account email

### 同步沒有觸發

- 用 `--once --debug` 執行，檢查 log 輸出
- 確認 `vault_folder_id` 正確
- 確認 `mappings` 中的 `doc_id` 和 `vault_path` 正確

### Vault 修改被覆蓋

這是預期行為。目前為單向同步（Doc → Vault），Vault 端的修改會在下次 Doc 變更時被覆蓋。
