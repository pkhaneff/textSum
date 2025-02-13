import os
from git import Git
from ai.chat_gpt import ChatGPT
from ai.ai_bot import AiBot
from log import Log
from env_vars import EnvVars
from repository.github import GitHub
from repository.repository import RepositoryError

def main():
    vars = EnvVars()
    vars.check_vars()

    ai = ChatGPT(vars.chat_gpt_token, vars.chat_gpt_model)
    github = GitHub(vars.token, vars.owner, vars.repo, vars.pull_number) if vars.pull_number else None

    if not github:
        Log.print_yellow("No associated pull request, skipping comment posting")
        return

    commits = github.get_commits_in_pr()
    if not commits:
        Log.print_red("No commits found in PR")
        return

    for commit in commits:
        commit_sha = commit['sha']
        Log.print_yellow(f"Processing commit: {commit_sha}")

        changed_files = github.get_changed_files_in_commit(commit_sha)
        if not changed_files:
            Log.print_red(f"No changes detected in commit {commit_sha}")
            continue

        Log.print_green(f"Changed files in commit {commit_sha}: {changed_files}")

        for file in changed_files:
            process_file(file, ai, github, commit_sha)

def process_file(file, ai, github, commit_id):
    Log.print_green("Checking file", file)
    
    _, file_extension = os.path.splitext(file)
    file_extension = file_extension.lstrip('.')
    vars = EnvVars()
    if not vars.target_extensions or file_extension not in vars.target_extensions:
        Log.print_yellow(f"Skipping unsupported extension: {file_extension} (file {file})")
        return

    try:
        with open(file, 'r', encoding="utf-8", errors="replace") as file_opened:
            file_content = file_opened.read()
    except FileNotFoundError:
        Log.print_yellow(f"File was removed, skipping: {file}")
        return

    if not file_content:
        Log.print_red(f"File is empty: {file}")
        return

    file_diffs = Git.get_diff_in_file(commit_id=commit_id, file_path=file)
    if not file_diffs:
        Log.print_red(f"No diffs found for file: {file}")
        return

    Log.print_green(f"Asking AI. Content Len: {len(file_content)}, Diff Len: {len(file_diffs)}")
    response = ai.ai_request_diffs(code=file_content, diffs=file_diffs)

    if AiBot.is_no_issues_text(response):
        Log.print_green(f"No issues found in file: {file}")
        post_general_comment(github, file, "AI review: ✅ No issues detected in this file.", commit_id)
        return

    responses = AiBot.split_ai_response(response)
    if not responses:
        Log.print_red(f"AI response parsing failed: {responses}")
        return

    for response in responses:
        result = False
        if hasattr(response, 'line') and response.line:
            result = post_line_comment(github, file, response.text, response.line, commit_id)
        if not result:
            result = post_general_comment(github, file, response.text, commit_id)
        if not result:
            Log.print_red(f"Failed to post comment for file: {file}")

def post_line_comment(github: GitHub, file: str, text: str, line: int, commit_id: str):
    Log.print_green(f"Posting line comment on {file}:{line}")
    try:
        if not github:
            return False
        if hasattr(github, 'post_comment_to_line'):
            git_response = github.post_comment_to_line(
                text=text, 
                commit_id=commit_id, 
                file_path=file, 
                line=line
            )
        else:
            Log.print_yellow("Method post_comment_to_line not found, using general comment instead")
            return post_general_comment(github, file, f"Line {line}: {text}", commit_id)
        
        Log.print_yellow(f"Posted successfully: {git_response}")
        return True
    except RepositoryError as e:
        Log.print_red(f"Failed line comment for {file}:{line} -> {e}")
        return False

def post_general_comment(github: GitHub, file: str, text: str, commit_id: str) -> bool:
    Log.print_green(f"Posting general comment on {file}")
    try:
        message = f"{file}\n{text}"
        git_response = github.post_comment_to_commit(message, commit_id)
        Log.print_yellow(f"Posted successfully: {git_response}")
        return True
    except RepositoryError as e:
        Log.print_red(f"Failed general comment for {file} -> {e}")
        return False

if __name__ == "__main__":
    main()
