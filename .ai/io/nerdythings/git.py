import re
import subprocess
from typing import List
from log import Log

class Git:
    @staticmethod
    def _run_subprocess(command: List[str]) -> str:
        """Execute a shell command and return its output."""
        Log.print_green(" ".join(command))
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
        if result.returncode == 0:
            return result.stdout.strip()
        Log.print_red(f"Error: {result.stderr.strip()}")
        raise RuntimeError(f"Error running {command}: {result.stderr.strip()}")

    @staticmethod
    def is_sha(ref: str) -> bool:
        """Check if a reference is a valid SHA-1 hash."""
        return bool(ref and re.fullmatch(r"[0-9a-f]{40}", ref.lower()))

    @staticmethod
    def get_remote_name() -> str:
        """Retrieve the name of the remote repository."""
        result = Git._run_subprocess(["git", "remote", "-v"])
        return result.splitlines()[0].split()[0] if result else "origin"

    @staticmethod
    def get_last_commit_sha(file: str) -> str:
        """Get the last commit SHA of a given file."""
        result = Git._run_subprocess(["git", "log", "-1", "--format=%H", "--", file])
        return result.splitlines()[0] if result else ""

    @staticmethod
    def get_open_pr_base_head() -> tuple[str, str] | None:
        """Retrieve the base and head branch references of an open PR."""
        try:
            pr_info = Git._run_subprocess(["gh", "pr", "view", "--json", "baseRefName,headRefName"])
            match = re.search(r'"baseRefName":\s*"(.*?)".*"headRefName":\s*"(.*?)"', pr_info, re.DOTALL)
            return (match.group(1), match.group(2)) if match else None
        except RuntimeError:
            return None

    @staticmethod
    def get_diff_files() -> List[str]:
        """Get a list of changed files in an open PR."""
        pr_refs = Git.get_open_pr_base_head()
        if not pr_refs:
            Log.print_yellow("No open PR found. Skipping review.")
            return []
        base, head = pr_refs
        remote_name = Git.get_remote_name()
        command = ["git", "diff", "--name-only", f"{remote_name}/{base}", f"{remote_name}/{head}"]
        return Git._run_subprocess(command).splitlines()

    @staticmethod
    def get_diff_in_file(file_path: str) -> str:
        """Get the diff of a specific file in an open PR."""
        pr_refs = Git.get_open_pr_base_head()
        if not pr_refs:
            return ""
        base, head = pr_refs
        remote_name = Git.get_remote_name()
        command = ["git", "diff", f"{remote_name}/{base}", f"{remote_name}/{head}", "--", file_path]
        return Git._run_subprocess(command)
