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
    
    if os.getenv("GITHUB_EVENT_NAME") != "pull_request" or not vars.pull_number:
        Log.print_red("Skipping review: No open pull request detected.")
        return
    
    github = GitHub(vars.github_token, vars.owner, vars.repo, vars.pull_number)
    ai = ChatGPT(vars.chat_gpt_token, vars.chat_gpt_model)
    
    vars.head_ref = os.getenv("GITHUB_SHA")
    vars.base_ref = os.getenv("GITHUB_BEFORE") or os.getenv("GITHUB_REF_NAME")
    
    if not vars.head_ref or not vars.base_ref:
        Log.print_red("Skipping review: Missing head_ref or base_ref.")
        return
    
    changed_files = Git.get_diff_files(head_ref=vars.head_ref, base_ref=vars.base_ref)
    if not changed_files:
        Log.print_red("Skipping review: No changes detected in PR.")
        return
    
    Log.print_green(f"Reviewing {len(changed_files)} changed files in PR #{vars.pull_number}...")
    for file in changed_files:
        process_file(file, ai, github, vars.head_ref)

def process_file(file, ai, github, commit_id):
    Log.print_green(f"Checking file: {file}")
    _, file_extension = os.path.splitext(file)
    vars = EnvVars()
    
    if vars.target_extensions and file_extension.lstrip('.') not in vars.target_extensions:
        Log.print_yellow(f"Skipping unsupported file type: {file_extension}")
        return
    
    try:
        with open(file, 'r', encoding="utf-8", errors="replace") as f:
            file_content = f.read()
    except FileNotFoundError:
        Log.print_yellow(f"File removed, skipping: {file}")
        return
    
    if not file_content:
        Log.print_red(f"Skipping empty file: {file}")
        return
    
    file_diffs = Git.get_diff_in_file(head_ref=vars.head_ref, base_ref=vars.base_ref, file_path=file)
    if not file_diffs:
        Log.print_red(f"No diffs found for file: {file}")
        return
    
    response = ai.ai_request_diffs(code=file_content, diffs=file_diffs)
    if AiBot.is_no_issues_text(response):
        Log.print_green(f"No issues found in {file}")
        post_general_comment(github, file, "✅ No issues detected.", commit_id)
        return
    
    for response in AiBot.split_ai_response(response):
        if hasattr(response, 'line') and response.line:
            if post_line_comment(github, file, response.text, response.line, commit_id):
                continue
        post_general_comment(github, file, response.text, commit_id)

def post_line_comment(github, file, text, line, commit_id):
    Log.print_green(f"Posting line comment on {file}:{line}")
    try:
        return github.post_comment_to_line(text, commit_id, file, line)
    except RepositoryError as e:
        Log.print_red(f"Failed line comment on {file}:{line} -> {e}")
        return False

def post_general_comment(github, file, text, commit_id):
    Log.print_green(f"Posting general comment on {file}")
    try:
        message = f"{file}\n{text}"
        return github.post_comment_general(message, commit_id)
    except RepositoryError as e:
        Log.print_red(f"Failed general comment on {file} -> {e}")
        return False

if __name__ == "__main__":
    main()
