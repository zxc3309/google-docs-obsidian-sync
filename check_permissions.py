"""
Diagnostic tool to check Google Docs permissions and accessibility
"""
import yaml
from modules.auth import DualAccountAuth

def check_doc_permissions():
    """Check if Service Account can access all mapped Google Docs"""

    # Load config
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    mappings = config.get('mappings', [])

    print(f"Checking {len(mappings)} Google Docs...\n")
    print("=" * 80)

    # Initialize auth
    import os
    os.environ['ACCOUNT_A_CREDENTIALS_PATH'] = 'account_aw_credentials.json'
    os.environ['ACCOUNT_B_CREDENTIALS_PATH'] = 'account_ce_credentials.json'

    auth = DualAccountAuth()

    from googleapiclient.discovery import build
    drive_service = build('drive', 'v3', credentials=auth.get_account_a_credentials())

    results = []

    for i, mapping in enumerate(mappings, 1):
        doc_id = mapping['doc_id']
        vault_path = mapping['vault_path']

        print(f"\n[{i}] Checking: {vault_path}")
        print(f"    Doc ID: {doc_id}")

        try:
            # Try to get file metadata
            file = drive_service.files().get(
                fileId=doc_id,
                fields='id,name,mimeType,permissions,owners'
            ).execute()

            print(f"    ✓ Name: {file.get('name')}")
            print(f"    ✓ Type: {file.get('mimeType')}")

            # Check owners
            owners = file.get('owners', [])
            if owners:
                print(f"    ✓ Owner: {owners[0].get('emailAddress', 'Unknown')}")

            results.append({
                'doc_id': doc_id,
                'vault_path': vault_path,
                'status': 'OK',
                'name': file.get('name')
            })

        except Exception as e:
            error_msg = str(e)
            print(f"    ✗ ERROR: {error_msg}")

            if '404' in error_msg or 'not found' in error_msg.lower():
                print(f"    → The Service Account cannot access this file")
                print(f"    → Please share the Google Doc with:")
                print(f"       obsidian-sync-account-aw@obsidian-sync-vault.iam.gserviceaccount.com")

            results.append({
                'doc_id': doc_id,
                'vault_path': vault_path,
                'status': 'ERROR',
                'error': error_msg
            })

    # Summary
    print("\n" + "=" * 80)
    print("\nSUMMARY:")
    print("-" * 80)

    ok_count = sum(1 for r in results if r['status'] == 'OK')
    error_count = sum(1 for r in results if r['status'] == 'ERROR')

    print(f"Total: {len(results)}")
    print(f"✓ Accessible: {ok_count}")
    print(f"✗ Not accessible: {error_count}")

    if error_count > 0:
        print("\n⚠️  ACTION REQUIRED:")
        print("Please share the following Google Docs with the Service Account:")
        print("Email: obsidian-sync-account-aw@obsidian-sync-vault.iam.gserviceaccount.com")
        print("\nDocuments that need sharing:")
        for r in results:
            if r['status'] == 'ERROR':
                print(f"  - {r['vault_path']} (Doc ID: {r['doc_id']})")
                print(f"    https://docs.google.com/document/d/{r['doc_id']}/edit")

if __name__ == '__main__':
    check_doc_permissions()
