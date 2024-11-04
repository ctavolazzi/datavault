from git import Repo
from pathlib import Path

class GitIntegration:
    def __init__(self, repo_path: Path):
        self.repo = Repo(repo_path)

    def get_changed_files(self, since_commit: str = 'HEAD~1') -> list:
        """Get files changed since specified commit"""
        diff = self.repo.head.commit.diff(since_commit)
        return [d.a_path for d in diff if d.a_path.endswith('.py')]

    def get_file_history(self, file_path: str, commits: int = 10) -> list:
        """Get file changes across recent commits"""
        commits = list(self.repo.iter_commits(paths=file_path, max_count=commits))
        return [{
            'commit': commit.hexsha,
            'date': commit.committed_datetime,
            'author': commit.author.name,
            'message': commit.message.strip()
        } for commit in commits] 