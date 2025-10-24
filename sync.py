#!/usr/bin/env python3
"""
Google Drive <-> Obsidian Vault Sync

Main entry point for the synchronization service
"""

import os
import sys
import yaml
import json
import logging
import argparse
import signal
import time
import schedule
from datetime import datetime

from modules.auth import DualAccountAuth
from modules.gdrive_client import GoogleDocsClient, VaultDriveClient
from modules.sync_engine import SyncEngine
from modules.conflict_handler import ConflictHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
shutdown_flag = False


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    global shutdown_flag
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_flag = True


def load_config(config_path: str = None) -> dict:
    """
    Load configuration from file or environment

    Args:
        config_path: Path to config file

    Returns:
        dict: Configuration
    """
    # Try to load from file
    if config_path and os.path.exists(config_path):
        logger.info(f"Loading config from {config_path}")
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config

    # Try to load from environment variable
    config_yaml = os.getenv('CONFIG_YAML')
    if config_yaml:
        logger.info("Loading config from CONFIG_YAML environment variable")
        config = yaml.safe_load(config_yaml)
        return config

    # Default minimal config
    logger.warning("No config file found, using environment variables only")
    return {
        'sync_interval': int(os.getenv('SYNC_INTERVAL', 300)),
        'vault_folder_id': os.getenv('VAULT_FOLDER_ID'),
        'mappings': json.loads(os.getenv('CONFIG_MAPPINGS', '[]'))
    }


def initialize_services(config: dict):
    """
    Initialize authentication and services

    Args:
        config: Configuration dictionary

    Returns:
        tuple: (docs_client, vault_client, sync_engine)
    """
    logger.info("Initializing services...")

    # Initialize authentication
    auth = DualAccountAuth()
    if not auth.is_authenticated():
        raise ValueError("Authentication failed. Check credentials environment variables.")

    # Get credentials
    account_a_creds = auth.get_account_a_credentials()
    account_b_creds = auth.get_account_b_credentials()

    # Initialize clients
    docs_client = GoogleDocsClient(account_a_creds)
    vault_client = VaultDriveClient(
        account_b_creds,
        config['vault_folder_id']
    )

    # Initialize sync engine
    sync_engine = SyncEngine(
        docs_client=docs_client,
        vault_client=vault_client,
        mappings=config['mappings']
    )

    logger.info("Services initialized successfully")
    return docs_client, vault_client, sync_engine


def run_sync(sync_engine: SyncEngine):
    """
    Run a single sync iteration

    Args:
        sync_engine: Sync engine instance
    """
    logger.info("=" * 80)
    logger.info(f"Starting sync at {datetime.now().isoformat()}")
    logger.info("=" * 80)

    try:
        results = sync_engine.sync_all()

        logger.info("-" * 80)
        logger.info("Sync Results:")
        logger.info(f"  ✓ Success: {results['success']}")
        logger.info(f"  ⚠ Conflicts: {results['conflicts']}")
        logger.info(f"  ✗ Errors: {results['errors']}")
        logger.info(f"  - Skipped: {results['skipped']}")
        logger.info("-" * 80)

        # Print conflict details if any
        if results['conflicts'] > 0:
            conflict_handler = ConflictHandler()
            conflicts = [
                d['result'] for d in results['details']
                if d['result'].get('status') == 'conflict'
            ]
            logger.warning(f"\n{results['conflicts']} conflict(s) detected!")
            logger.warning("Please review and resolve conflicts manually.")

    except Exception as e:
        logger.error(f"Error during sync: {e}", exc_info=True)


def run_once(config: dict):
    """
    Run sync once and exit

    Args:
        config: Configuration dictionary
    """
    logger.info("Running sync once...")

    docs_client, vault_client, sync_engine = initialize_services(config)
    run_sync(sync_engine)

    logger.info("Single sync completed, exiting")


def run_continuous(config: dict):
    """
    Run sync continuously with scheduling

    Args:
        config: Configuration dictionary
    """
    interval = config.get('sync_interval', 300)
    logger.info(f"Starting continuous sync with {interval}s interval")

    docs_client, vault_client, sync_engine = initialize_services(config)

    # Schedule sync
    schedule.every(interval).seconds.do(run_sync, sync_engine)

    # Run initial sync immediately
    run_sync(sync_engine)

    logger.info("Entering main loop... Press Ctrl+C to stop")

    # Main loop
    while not shutdown_flag:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
            time.sleep(5)  # Wait before retrying

    logger.info("Shutting down gracefully")


def show_status(config: dict):
    """
    Show current sync status

    Args:
        config: Configuration dictionary
    """
    try:
        docs_client, vault_client, sync_engine = initialize_services(config)
        status = sync_engine.get_sync_status()

        print("\n" + "=" * 80)
        print("SYNC STATUS")
        print("=" * 80)
        print(f"Last run: {status['last_run']}")
        print(f"Total files tracked: {status['total_files']}")
        print(f"Pending conflicts: {status['pending_conflicts']}")
        print("\nFile Status:")
        print("-" * 80)

        for doc_id, file_info in status.get('files', {}).items():
            print(f"\nDoc ID: {doc_id}")
            print(f"  Path: {file_info.get('vault_path')}")
            print(f"  Last synced: {file_info.get('last_synced_at')}")
            print(f"  Direction: {file_info.get('direction')}")

        print("=" * 80)

    except Exception as e:
        logger.error(f"Error showing status: {e}", exc_info=True)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Google Drive <-> Obsidian Vault Sync'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to config file (default: config.yaml)'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run sync once and exit'
    )
    parser.add_argument(
        '--interval',
        type=int,
        help='Sync interval in seconds (overrides config)'
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show current sync status'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )

    args = parser.parse_args()

    # Set log level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

    # Load configuration
    try:
        config = load_config(args.config)

        # Override interval if specified
        if args.interval:
            config['sync_interval'] = args.interval

        # Validate config
        if not config.get('vault_folder_id'):
            raise ValueError("vault_folder_id not found in config")
        if not config.get('mappings'):
            raise ValueError("No mappings configured")

        logger.info(f"Loaded {len(config['mappings'])} mapping(s)")

    except Exception as e:
        logger.error(f"Error loading config: {e}")
        sys.exit(1)

    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Run based on mode
    try:
        if args.status:
            show_status(config)
        elif args.once:
            run_once(config)
        else:
            run_continuous(config)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
