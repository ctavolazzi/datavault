from typing import Any, Dict
from pathlib import Path
from datetime import datetime

def format_file_info(info: Dict[str, Any]) -> str:
    """Format file analysis information for display"""
    output = ["\n📄 File Information", "=" * 50]
    
    # Basic information
    output.extend([
        f"\n📊 Basic Info:",
        f"  Size: {_format_size(info['size'])}",
        f"  Created: {info['created']:%Y-%m-%d %H:%M:%S}",
        f"  Modified: {info['modified']:%Y-%m-%d %H:%M:%S}",
        f"  Type: {info['type']}",
        f"  MIME Type: {info['mime_type']}"
    ])
    
    # Hash if available
    if 'hash' in info:
        output.extend([
            f"\n🔒 Hash:",
            f"  MD5: {info['hash']}"
        ])
    
    # Preview if available
    if 'preview' in info:
        output.extend([
            f"\n👁️  Preview:",
            "  " + "\n  ".join(info['preview'].split('\n')[:5])
        ])
        if len(info['preview'].split('\n')) > 5:
            output.append("  ...")
    
    return "\n".join(output)

def _format_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB" 