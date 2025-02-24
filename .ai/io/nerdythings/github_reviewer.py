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

def update_pr_summary_comment(changed_files, ai, github):
    Log.print_green("Updating PR summary comment...")
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
    
    try:
        existing_comments = github.get_comments()
        summary_comment = next((comment for comment in existing_comments if PR_SUMMARY_COMMENT_IDENTIFIER in comment["body"]), None)
        
        updated_comment = f"{PR_SUMMARY_COMMENT_IDENTIFIER}\n## Summary by BapAI.ReviewCode\n\n{new_summary}"
        
        if summary_comment:
            github.update_comment(summary_comment["id"], updated_comment)
            Log.print_yellow("Updated existing PR summary comment.")
        else:
            github.post_comment_general(updated_comment)
            Log.print_yellow("Posted new PR summary comment.")
    except RepositoryError as e:
        Log.print_red(f"Failed to update PR summary comment: {e}")

def main():
    vars, github, ai = setup()
    if not vars:
        return
    
    changed_files = get_changed_files(vars)
    if not changed_files:
        return
    
    update_pr_summary_comment(changed_files, ai, github)

if __name__ == "__main__":
    main()
