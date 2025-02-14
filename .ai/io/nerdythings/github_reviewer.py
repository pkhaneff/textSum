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
        Log.print_red("This action only runs on pull request events.")
        return

    github = GitHub(vars.token, vars.owner, vars.repo, vars.pull_number)
    ai = ChatGPT(vars.chat_gpt_token, vars.chat_gpt_model)
    
    changed_files = Git.get_diff_files(head_ref=vars.head_ref, base_ref=vars.base_ref)
    if not changed_files:
        Log.print_red("No changes between commits")
        return
    
    Log.print_yellow(f"Detected changed files: {changed_files}")
    
    latest_commit_id = vars.head_ref
    Log.print_yellow(f"Using latest commit SHA: {latest_commit_id}")
    
    for file in changed_files:
        process_file(file, ai, github, latest_commit_id, vars)

def process_file(file, ai, github, commit_id, vars):
    Log.print_green(f"Processing file: {file}")
    
    file_extension = os.path.splitext(file)[1].lstrip('.')
    if vars.target_extensions and file_extension not in vars.target_extensions:
        Log.print_yellow(f"Skipping unsupported extension: {file_extension} ({file})")
        return
    
    try:
        with open(file, 'r', encoding="utf-8", errors="replace") as f:
            file_content = f.read()
    except FileNotFoundError:
        Log.print_yellow(f"File removed, skipping: {file}")
        return
    
    if not file_content:
        Log.print_red(f"File is empty: {file}")
        return
    
    file_diffs = Git.get_diff_in_file(head_ref=vars.head_ref, base_ref=vars.base_ref, file_path=file)
    if not file_diffs:
        Log.print_red(f"No diffs found for file: {file}")
        return
    
    Log.print_green(f"Requesting AI review. File length: {len(file_content)}, Diff length: {len(file_diffs)}")
    response = ai.ai_request_diffs(code=file_content, diffs=file_diffs)
    
    handle_ai_response(response, github, file, commit_id)

def handle_ai_response(response, github, file, commit_id):
    if AiBot.is_no_issues_text(response):
        Log.print_green(f"No issues found in file: {file}")
        post_general_comment(github, file, "AI review: ✅ No issues detected in this file.", commit_id)
        return
    
    responses = AiBot.split_ai_response(response)
    if not responses:
        Log.print_red(f"AI response parsing failed: {responses}")
        return
    
    for response in responses:
        posted = False
        if hasattr(response, 'line') and response.line:
            posted = post_line_comment(github, file, response.text, response.line, commit_id)
        if not posted:
            posted = post_general_comment(github, file, response.text, commit_id)
        if not posted:
            Log.print_red(f"Failed to post comment for file: {file}")

def post_line_comment(github, file, text, line, commit_id):
    try:
        if not github:
            return False
        
        if hasattr(github, 'post_comment_to_line'):
            response = github.post_comment_to_line(text=text, commit_id=commit_id, file_path=file, line=line)
        else:
            Log.print_yellow("Method post_comment_to_line not found, using general comment instead")
            return post_general_comment(github, file, f"Line {line}: {text}", commit_id)
        
        Log.print_yellow(f"Posted successfully: {response}")
        return True
    except RepositoryError as e:
        Log.print_red(f"Failed to post line comment for {file}:{line} -> {e}")
        return False

def post_general_comment(github, file, text, commit_id):
    try:
        message = f"{file}\n{text}"
        response = github.post_comment_general(message, commit_id)
        Log.print_yellow(f"Posted successfully: {response}")
        return True
    except RepositoryError as e:
        Log.print_red(f"Failed to post general comment for {file} -> {e}")
        return False

if __name__ == "__main__":
    main()
