#!/usr/bin/env python3
"""
Quick integration check for loading mappings from Google Sheet or config.

Usage:
    python test_sheet_mappings.py [optional_config_path]

Expected env (for sheet mode):
    SHEET_ID (required to use sheet)
    SHEET_RANGE (optional, default Sheet1!A:B)
    ACCOUNT_A_CREDENTIALS / ACCOUNT_A_CREDENTIALS_PATH
    ACCOUNT_B_CREDENTIALS / ACCOUNT_B_CREDENTIALS_PATH
    VAULT_FOLDER_ID (still required)
"""

import os
import sys
from typing import List, Dict

from sync import load_config


def validate_mappings(mappings: List[Dict[str, str]]) -> List[str]:
    errors = []
    seen = set()

    for idx, m in enumerate(mappings, start=1):
        doc_id = m.get('doc_id', '').strip()
        vault_path = m.get('vault_path', '').strip()

        if not doc_id:
            errors.append(f"Row {idx}: missing doc_id")
        if not vault_path:
            errors.append(f"Row {idx}: missing vault_path")
        if doc_id in seen:
            errors.append(f"Row {idx}: duplicate doc_id {doc_id}")
        seen.add(doc_id)

    return errors


def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else None

    try:
        config = load_config(config_path)
    except Exception as e:
        print(f"[FAIL] Could not load config: {e}")
        sys.exit(1)

    mappings = config.get('mappings', [])
    sheet_id = os.getenv('SHEET_ID') or config.get('sheet_id')
    sheet_range = os.getenv('SHEET_RANGE', config.get('sheet_range', 'Sheet1!A:B'))

    source = "Google Sheet" if sheet_id else "config"
    print(f"Loaded mappings from {source}")
    if sheet_id:
        print(f"  SHEET_ID: {sheet_id}")
        print(f"  SHEET_RANGE: {sheet_range}")

    print(f"Total mappings: {len(mappings)}")
    for m in mappings:
        print(f"  - {m.get('doc_id')} -> {m.get('vault_path')}")

    if not mappings:
        print("[FAIL] No mappings loaded")
        sys.exit(1)

    errors = validate_mappings(mappings)
    if errors:
        print("[FAIL] Validation errors:")
        for err in errors:
            print(f"  * {err}")
        sys.exit(1)

    print("[OK] Mappings look valid")
    sys.exit(0)


if __name__ == "__main__":
    main()

