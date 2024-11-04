from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import click

class StatusFormatter:
    def format_project_overview(self, stats: Dict[str, Any]) -> str:
        """Format basic project statistics"""
        return (
            f"\n📁 Project Directory: {stats['project_name']}\n"
            f"📊 Files: {stats['total_files']} ({stats['total_dirs']} directories)\n"
            f"🐍 Python Files: {stats['python_files']}\n"
            f"💾 Total Size: {stats['total_size_mb']:.2f} MB"
        )
    
    def format_file_types(self, file_types: List[tuple]) -> str:
        """Format file type distribution"""
        lines = ["\n📑 File Types:"]
        for ext, count in file_types:
            lines.append(f"   {ext:12} {count:5d} files")
        return "\n".join(lines)
    
    def format_recent_activity(self, activities: List[tuple]) -> str:
        """Format recent file activities"""
        lines = ["\n🕒 Recent Activity:"]
        for timestamp, file_path in activities:
            lines.append(
                f"   {timestamp.strftime('%Y-%m-%d %H:%M')} - {file_path.name}"
            )
        return "\n".join(lines)
    
    def format_quick_actions(self, has_python_files: bool) -> str:
        """Format suggested actions"""
        lines = ["\n💡 Quick Actions:"]
        if has_python_files:
            lines.extend([
                "   • Check code quality:",
                "     datavault quality"
            ])
        lines.extend([
            "   • Generate detailed report:",
            "     datavault report",
            "   • Search files:",
            "     datavault find --pattern '*.py'"
        ])
        return "\n".join(lines)
    
    def format_concerns(self, concerns: Dict[str, List[Path]]) -> str:
        """Format potential concerns"""
        lines = ["\n⚠️  Potential Concerns:"]
        if concerns['large_files']:
            lines.append(f"   • Found {len(concerns['large_files'])} large files (>1MB)")
        if concerns['empty_dirs']:
            lines.append(f"   • Found {len(concerns['empty_dirs'])} empty directories")
        return "\n".join(lines) 