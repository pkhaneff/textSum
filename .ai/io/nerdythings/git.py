import re
import subprocess
from typing import List
from log import Log

class Git:
    @staticmethod
    def __run_subprocess(command):
        Log.print_green(command)
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
        if result.returncode == 0:
            return result.stdout
        else:
            Log.print_red(f"Error running {command}: {result.stderr}")
            raise Exception(f"Error running {command}: {result.stderr}")

    @staticmethod
    def get_remote_name() -> str:
        command = ["git", "remote", "-v"]
        result = Git.__run_subprocess(command)
        lines = result.strip().splitlines()
        return lines[0].split()[0] if lines else "origin"

    @staticmethod
    def get_last_commit_sha(file: str) -> str:
        command = ["git", "log", "-1", "--format=%H", "--", file]
        result = Git.__run_subprocess(command)
        lines = result.strip().splitlines()
        return lines[0] if lines else ""

    @staticmethod
    def get_diff_files(base_ref: str, head_ref: str) -> List[str]:
        remote_name = Git.get_remote_name()
        command = ["git", "diff", "--name-only", f"{remote_name}/{base_ref}", f"{remote_name}/{head_ref}"]
        result = Git.__run_subprocess(command)
        return result.strip().splitlines()

    @staticmethod
    def get_diff_in_file(base_ref: str, head_ref: str, file_path: str) -> str:
        remote_name = Git.get_remote_name()
        command = ["git", "diff", f"{remote_name}/{base_ref}", f"{remote_name}/{head_ref}", "--", file_path]
        return Git.__run_subprocess(command)
