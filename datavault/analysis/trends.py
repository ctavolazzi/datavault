from pathlib import Path
import sqlite3
from datetime import datetime

class QualityTrends:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS quality_metrics (
                    file_path TEXT,
                    timestamp DATETIME,
                    avg_complexity FLOAT,
                    duplicate_blocks INT,
                    lint_issues INT
                )
            """)

    def store_metrics(self, file_path: str, metrics: dict):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO quality_metrics 
                VALUES (?, ?, ?, ?, ?)
            """, (
                file_path,
                datetime.now(),
                metrics.get('complexity', {}).get('average_complexity', 0),
                metrics.get('duplication', {}).get('duplicate_blocks', 0),
                metrics.get('lint', {}).get('issues_count', 0)
            ))

    def get_trends(self, file_path: str, days: int = 30):
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute("""
                SELECT timestamp, avg_complexity, duplicate_blocks, lint_issues
                FROM quality_metrics
                WHERE file_path = ?
                AND timestamp > datetime('now', ?)
                ORDER BY timestamp
            """, (file_path, f'-{days} days')).fetchall() 