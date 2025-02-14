import os
from git import Git 
from ai.chat_gpt import ChatGPT
from log import Log
from env_vars import EnvVars
from repository.github import GitHub
from repository.repository import RepositoryError

def main():
    vars = EnvVars()
    vars.check_vars()

    if os.getenv("GITHUB_EVENT_NAME") != "pull_request" or not vars.pull_number:
        Log.print_red("This action only runs on pull request events.")
        return

    github = GitHub(vars.token, vars.owner, vars.repo, vars.pull_number)
    ai = ChatGPT(vars.chat_gpt_token, vars.chat_gpt_model)
    
    changed_files = Git.get_diff_files(head_ref=vars.head_ref, base_ref=vars.base_ref)
    if not changed_files:
        Log.print_red("No changes detected.")
        return
    
    Log.print_yellow(f"Changed files: {changed_files}")
    
    for file in changed_files:
        process_file(file, ai, github, vars)

def process_file(file, ai, github, vars):
    Log.print_green(f"Reviewing file: {file}")
    
    try:
        with open(file, 'r', encoding="utf-8", errors="replace") as f:
            file_content = f.read()
    except FileNotFoundError:
        Log.print_yellow(f"File not found: {file}")
        return
    
    file_diffs = Git.get_diff_in_file(head_ref=vars.head_ref, base_ref=vars.base_ref, file_path=file)
    if not file_diffs:
        Log.print_red(f"No diffs found for: {file}")
        return
    
    Log.print_green(f"AI analyzing changes in {file}...")
    response = ai.ai_request_diffs(code=file_content, diffs=file_diffs)
    
    handle_ai_response(response, github, file)

def handle_ai_response(response, github, file):
    if "no issues" in response.lower():
        Log.print_green(f"No issues in {file}")
        github.post_comment_general(f"✅ AI review: No issues found in {file}.")
        return
    
    suggestions = parse_ai_suggestions(response)
    if not suggestions:
        Log.print_red(f"Failed to parse AI suggestions for {file}")
        return
    
    for suggestion in suggestions:
        post_comment(github, file, suggestion)

def parse_ai_suggestions(response):
    # Dummy function: Needs real parsing logic
    return response.split("\n\n") if response else []

def post_comment(github, file, suggestion):
    try:
        github.post_comment_general(f"{file}\n{suggestion}")
        Log.print_yellow(f"Posted review for {file}")
    except RepositoryError as e:
        Log.print_red(f"Failed to post review for {file}: {e}")

if __name__ == "__main__":
    main()
