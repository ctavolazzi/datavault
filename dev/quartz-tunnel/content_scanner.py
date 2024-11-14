import json
import os
from pathlib import Path
from datetime import datetime

def scan_content_directory(content_dir):
    """
    Scans the content directory and creates a JSON representation of its structure

    Args:
        content_dir: Path to the content directory to scan
    Returns:
        dict: Dictionary containing the directory structure and file metadata
    """
    content_map = {
        "last_updated": datetime.now().isoformat(),
        "root_path": str(content_dir),
        "files": [],
        "directories": {}
    }

    # Convert to Path object
    content_path = Path(content_dir)

    # Set to keep track of processed directories to prevent loops
    processed_dirs = set()

    def process_directory(current_path, current_dict):
        """
        Process a directory and its contents
        """
        # Get absolute path to check for loops
        abs_path = current_path.resolve()

        # Skip if we've seen this directory before
        if abs_path in processed_dirs:
            return

        processed_dirs.add(abs_path)

        for item in current_path.iterdir():
            # Skip hidden files and directories
            if item.name.startswith('.'):
                continue

            if item.is_file() and item.suffix == '.md':
                # Get file metadata
                file_info = {
                    "name": item.name,
                    "path": str(item.relative_to(content_path)),
                    "size": item.stat().st_size,
                    "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                }
                current_dict["files"].append(file_info)

            elif item.is_dir():
                # Create new directory entry
                current_dict["directories"][item.name] = {
                    "files": [],
                    "directories": {}
                }
                # Process subdirectory
                process_directory(item, current_dict["directories"][item.name])

    # Start processing from root
    process_directory(content_path, content_map)

    return content_map

def save_content_map(content_map, output_dir):
    """
    Saves the content map to a JSON file
    """
    output_path = Path(output_dir) / "content_map.json"

    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save with pretty printing
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(content_map, f, indent=2, ensure_ascii=False)

    return output_path

if __name__ == "__main__":
    # Define paths
    content_dir = "/Users/ctavolazzi/Code/quartz/content"
    output_dir = "/Users/ctavolazzi/Code/datavault/dev/quartz-tunnel"

    try:
        # Scan content directory
        print("Scanning content directory...")
        content_map = scan_content_directory(content_dir)

        # Save results
        output_file = save_content_map(content_map, output_dir)
        print(f"Content map saved to: {output_file}")

    except Exception as e:
        print(f"Error: {e}")