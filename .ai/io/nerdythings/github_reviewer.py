import os
import re
from git import Git
from ai.chat_gpt import ChatGPT
from log import Log
from ai.ai_bot import AiBot
from env_vars import EnvVars
from repository.github import GitHub
from repository.repository import RepositoryError

PR_SUMMARY_COMMENT_IDENTIFIER = "<!-- PR SUMMARY COMMENT -->"
EXCLUDED_FOLDERS = {".ai/io/nerdythings", ".github/workflows"}

def setup():
    vars = EnvVars()
    vars.check_vars()
    
    if os.getenv("GITHUB_EVENT_NAME") != "pull_request" or not vars.pull_number:
        Log.print_red("This action only runs on pull request events.")
        return None, None, None
    
    github = GitHub(vars.token, vars.owner, vars.repo, vars.pull_number)
    ai = ChatGPT(vars.chat_gpt_token, vars.chat_gpt_model)
    return vars, github, ai

def get_changed_files(vars):
    changed_files = Git.get_diff_files(head_ref=vars.head_ref, base_ref=vars.base_ref)
    if not changed_files:
        Log.print_red("No changes detected.")
        return []
    
    filtered_files = [
        file for file in changed_files
        if not any(file.startswith(excluded) for excluded in EXCLUDED_FOLDERS)
    ]
    
    if not filtered_files:
        Log.print_green("All changed files are excluded from review.")
    else:
        Log.print_yellow(f"Filtered changed files: {filtered_files}")
    
    return filtered_files

def update_pr_summary(changed_files, ai, github):
    Log.print_green("Updating PR description...")
    file_contents = []
    
    for file in changed_files:
        try:
            with open(file, 'r', encoding="utf-8", errors="replace") as f:
                content = f.read()
                file_contents.append(f"### {file}\n{content[:1000]}...\n")
        except FileNotFoundError:
            Log.print_yellow(f"File not found: {file}")
    
    if not file_contents:
        return
    
    full_context = {file: content[:1000] for file, content in zip(changed_files, file_contents)}
    new_summary = ai.ai_request_summary(file_changes=full_context)
    pr_data = github.get_pull_request()
    current_body = pr_data.get("body") or ""
    
    if PR_SUMMARY_COMMENT_IDENTIFIER in current_body:
        updated_body = re.sub(
            f"{PR_SUMMARY_COMMENT_IDENTIFIER}.*",
            f"{PR_SUMMARY_COMMENT_IDENTIFIER}\n## Summary by BapAI.ReviewCode\n\n{new_summary}",
            current_body,
            flags=re.DOTALL
        )
    else:
        updated_body = f"{PR_SUMMARY_COMMENT_IDENTIFIER}\n## Summary by BapAI.ReviewCode\n\n{new_summary}\n\n{current_body}"
    
    try:
        github.update_pull_request(updated_body)
        Log.print_yellow("PR description updated successfully!")
    except RepositoryError as e:
        Log.print_red(f"Failed to update PR description: {e}")

def process_file(file, ai, vars):
    Log.print_green(f"Reviewing file: {file}")
    
    try:
        with open(file, 'r', encoding="utf-8", errors="replace") as f:
            file_content = f.read()
    except FileNotFoundError:
        Log.print_yellow(f"File not found: {file}")
        return None
    
    file_diffs = Git.get_diff_in_file(head_ref=vars.head_ref, base_ref=vars.base_ref, file_path=file)
    if not file_diffs:
        Log.print_red(f"No diffs found for: {file}")
        return None
    
    if file_diffs:
        diff_code = "\n".join(diff["code"] for diff in file_diffs)
        Log.print_green(f"AI analyzing changes in {file}...")
        return ai.ai_request_diffs(code=diff_code, diffs=file_diffs)

def post_ai_comments_per_file(ai_responses, github):
    if not ai_responses:
        Log.print_green("No issues detected across all files.")
        return
    
    try:
        existing_comments = github.get_comments()
        
        for file, response in ai_responses.items():
            if not response or AiBot.is_no_issues_text(response):
                Log.print_green(f"No issues detected in {file}.")
                continue
            
            suggestions = parse_ai_suggestions(response)
            if not suggestions:
                Log.print_red(f"Failed to parse AI suggestions for {file}.")
                continue
            
            comment_body = f"### AI Review for {file}\n\n" + "\n".join(f"- {s.strip()}" for s in suggestions)
            
            if not any(comment['body'] == comment_body for comment in existing_comments):
                github.post_comment_general(comment_body)
                Log.print_yellow(f"Posted review for {file}")
            else:
                Log.print_green(f"Review for {file} already posted, skipping.")
    except RepositoryError as e:
        Log.print_red(f"Failed to post AI review comments: {e}")

def parse_ai_suggestions(response):
    return response.split("\n\n") if response else []

def main():
    vars, github, ai = setup()
    if not vars:
        return
    
    changed_files = get_changed_files(vars)
    if not changed_files:
        return
    
    update_pr_summary(changed_files, ai, github)
    
    ai_responses = {file: process_file(file, ai, vars) for file in changed_files if process_file(file, ai, vars)}
    
    post_ai_comments_per_file(ai_responses, github)

if __name__ == "__main__":
    main()
