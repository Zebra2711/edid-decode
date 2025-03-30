#!/usr/bin/env python3
import os
import subprocess
from typing import List, Tuple

class CommitSyncer:
    def __init__(self):
        self.base_dir = os.getcwd()
        self.v4l_utils_path = os.path.join(self.base_dir, 'v4l-utils')
        self.edid_decode_path = self.base_dir
        self.source_dir = 'utils/edid-decode'
        self.starting_commit = os.getenv('INPUT_STARTING_COMMIT', '363495b6df0dc30a0d63d49720ebbfa33f65c91f')
    
    def run_git_command(self, cmd: List[str], cwd: str) -> Tuple[str, str, int]:
        """Run a git command and return stdout, stderr, and return code"""
        try:
            process = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=False
            )
            return process.stdout.strip(), process.stderr.strip(), process.returncode
        except subprocess.SubprocessError as e:
            return '', str(e), 1
    
    def get_edid_decode_commits(self) -> List[str]:
        """Get commits affecting the edid-decode directory"""
        stdout, _, _ = self.run_git_command(
            ['git', 'rev-list', '--reverse', f'{self.starting_commit}..HEAD'],
            self.v4l_utils_path
        )
        
        commits = []
        for commit_hash in stdout.split('\n'):
            if not commit_hash:
                continue
                
            # Check commit message
            msg, _, _ = self.run_git_command(
                ['git', 'log', '-1', '--pretty=format:%s', commit_hash],
                self.v4l_utils_path
            )
            
            if not msg.startswith('edid-decode:'):
                continue
                
            # Check changed files
            files, _, _ = self.run_git_command(
                ['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', commit_hash],
                self.v4l_utils_path
            )
            
            if any(f.startswith(self.source_dir) for f in files.split('\n')):
                commits.append(commit_hash)
                
        return commits
    
    def copy_files_from_commit(self, commit_hash: str) -> bool:
        """Copy files from a specific commit"""
        # Get commit message
        msg, _, _ = self.run_git_command(
            ['git', 'log', '-1', '--pretty=format:%s%n%n%b', commit_hash],
            self.v4l_utils_path
        )
        
        # Get changed files in the commit
        files, _, _ = self.run_git_command(
            ['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', commit_hash],
            self.v4l_utils_path
        )
        
        edid_files = [
            f for f in files.split('\n')
            if f.startswith(self.source_dir)
        ]
        
        if not edid_files:
            return False
        
        # Copy each file
        for file_path in edid_files:
            # Extract file content from the commit
            content, _, code = self.run_git_command(
                ['git', 'show', f'{commit_hash}:{file_path}'],
                self.v4l_utils_path
            )
            if code != 0:
                continue
                
            # Write to target repository
            target_path = os.path.basename(file_path)
            try:
                with open(os.path.join(self.edid_decode_path, target_path), 'w') as f:
                    f.write(content)
            except IOError:
                continue
        
        # Stage changes
        self.run_git_command(['git', 'add', '.'], self.edid_decode_path)
        
        # Create commit
        commit_msg = msg
        commit_msg = f"{commit_msg}\n\nSynced from v4l-utils commit {commit_hash}"
        
        _, _, code = self.run_git_command(
            ['git', 'commit', '-m', commit_msg],
            self.edid_decode_path
        )
        
        return code == 0
    
    def sync(self):
        """Main sync process"""
        commits = self.get_edid_decode_commits()
        if not commits:
            print("No edid-decode commits to sync")
            return
        
        success_count = sum(1 for commit in commits if self.copy_files_from_commit(commit))
        print(f"Synced {success_count}/{len(commits)} commits successfully")

if __name__ == "__main__":
    syncer = CommitSyncer()
    syncer.sync()
