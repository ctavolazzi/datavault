import shutil
import os
from pathlib import Path

def sync_to_quartz(source_dir, target_dir):
    """
    Syncs files from datavault to quartz content directory

    Args:
        source_dir: Path to datavault directory
        target_dir: Path to quartz content directory
    """
    # Convert strings to Path objects
    source = Path(source_dir)
    target = Path(target_dir)

    # Ensure both directories exist
    if not source.exists():
        raise ValueError(f"Source directory does not exist: {source}")
    if not target.exists():
        raise ValueError(f"Target directory does not exist: {target}")

    # Copy files
    try:
        # Copy all markdown files
        for file in source.glob('**/*.md'):
            # Get relative path to maintain directory structure
            rel_path = file.relative_to(source)
            dest_file = target / rel_path

            # Create parent directories if they don't exist
            dest_file.parent.mkdir(parents=True, exist_ok=True)

            # Copy the file
            shutil.copy2(file, dest_file)
            print(f"Copied: {file} -> {dest_file}")

    except Exception as e:
        print(f"Error during sync: {e}")

if __name__ == "__main__":
    source_dir = "/Users/ctavolazzi/Code/datavault/dev/quatz-tunnel"
    target_dir = "/Users/ctavolazzi/Code/quartz/content"

    sync_to_quartz(source_dir, target_dir)