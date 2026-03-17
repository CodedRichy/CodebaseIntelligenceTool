import os
import tempfile
from typing import Dict, List, Optional
from git import Repo
from pydantic import BaseModel

class RepositoryInfo(BaseModel):
    url: str
    local_path: str
    name: str
    files: List[Dict] = []
    classes: List[Dict] = []
    functions: List[Dict] = []
    imports: List[Dict] = []
    dependencies: List[Dict] = []

class RepoIngestionService:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()

    async def clone_repository(self, repo_url: str) -> RepositoryInfo:
        """Clone a Git repository to a temporary directory."""
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        local_path = os.path.join(self.temp_dir, repo_name)

        # Clone the repository
        Repo.clone_from(repo_url, local_path)

        return RepositoryInfo(
            url=repo_url,
            local_path=local_path,
            name=repo_name
        )

    async def scan_repository(self, repo_info: RepositoryInfo) -> RepositoryInfo:
        """Scan the repository and extract basic file information."""
        files = []

        for root, dirs, filenames in os.walk(repo_info.local_path):
            # Skip .git directory and common non-code directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv']]

            for filename in filenames:
                if self._is_code_file(filename):
                    file_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(file_path, repo_info.local_path)

                    files.append({
                        'path': rel_path,
                        'absolute_path': file_path,
                        'extension': os.path.splitext(filename)[1],
                        'size': os.path.getsize(file_path)
                    })

        repo_info.files = files
        return repo_info

    def _is_code_file(self, filename: str) -> bool:
        """Check if a file is a code file based on extension."""
        code_extensions = {
            '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.hpp',
            '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala'
        }
        return any(filename.endswith(ext) for ext in code_extensions)

    async def cleanup_repository(self, repo_info: RepositoryInfo):
        """Clean up the cloned repository."""
        import shutil
        if os.path.exists(repo_info.local_path):
            shutil.rmtree(repo_info.local_path)
