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

    changed_files = Git.get_diff_files(head_ref=vars.head_ref, base_ref=vars.base_ref)
    Log.print_yellow(f"DEBUG: Changed files detected: {changed_files}")
    Log.print_green("Found changes in files", changed_files)

    if not changed_files:
        Log.print_red("No changes between commits")
        return

    if github:
        latest_commit_id = vars.head_ref
        Log.print_yellow(f"Using latest commit SHA: {latest_commit_id}")

        for file in changed_files:
            process_file(file, ai, github, latest_commit_id)
    else:
        Log.print_yellow("No associated pull request, skipping comment posting")

def get_code_snippet(file_path, line_number, context_lines=2):
    """
    Extracts a code snippet from a file, including the specified line and surrounding context.

    Args:
        file_path (str): The path to the file.
        line_number (int): The line number to center the snippet around.
        context_lines (int): The number of lines of context to include before and after the target line.

    Returns:
        str: A formatted code snippet, or None if there's an error.
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()

        start_line = max(0, line_number - context_lines - 1)  # Adjust for 0-based indexing
        end_line = min(len(lines), line_number + context_lines)

        snippet_lines = lines[start_line:end_line]

        snippet = "".join(snippet_lines) # changed code to extract string

        return snippet
    except Exception as e:
        Log.print_red(f"Error extracting code snippet from {file_path}: {e}")
        return None

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

    file_diffs = Git.get_diff_in_file(head_ref=vars.head_ref, base_ref=vars.base_ref, file_path=file)
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
            code_snippet = get_code_snippet(file, response.line)
            if code_snippet:
                comment_text = f"{response.text}\n\n```\n{code_snippet}\n```"  # Include snippet in comment
            else:
                comment_text = response.text # just response if cannot extract
            result = post_line_comment(github, file, comment_text, response.line, commit_id)
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
        git_response = github.post_comment_general(message, commit_id)
        Log.print_yellow(f"Posted successfully: {git_response}")
        return True
    except RepositoryError as e:
        Log.print_red(f"Failed general comment for {file} -> {e}")
        return False

if __name__ == "__main__":
    main()