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
    github = GitHub(vars.token, vars.owner, vars.repo, vars.pull_number)

    remote_name = Git.get_remote_name()
    
    Log.print_green("Remote is", remote_name)
    changed_files = Git.get_diff_files(remote_name=remote_name, head_ref=vars.head_ref, base_ref=vars.base_ref)
    Log.print_green("Found changes in files", changed_files)
    if not changed_files:
        Log.print_red("No changes between branches")
        return  # Dừng nếu không có thay đổi

    for file in changed_files:
        Log.print_green("Checking file", file)

        _, file_extension = os.path.splitext(file)
        file_extension = file_extension.lstrip('.')
        if not vars.target_extensions or file_extension not in vars.target_extensions:
            Log.print_yellow(f"Skipping unsupported extension: {file_extension} (file {file})")
            continue

        try:
            with open(file, 'r') as file_opened:
                file_content = file_opened.read()
        except FileNotFoundError:
            Log.print_yellow(f"File was removed, skipping: {file}")
            continue

        if not file_content:
            Log.print_red(f"File is empty: {file}")
            continue

        file_diffs = Git.get_diff_in_file(remote_name=remote_name, head_ref=vars.head_ref, base_ref=vars.base_ref, file_path=file)
        if not file_diffs:
            Log.print_red(f"No diffs found for file: {file}")
            continue
        
        Log.print_green(f"Asking AI. Content Len: {len(file_content)}, Diff Len: {len(file_diffs)}")
        response = ai.ai_request_diffs(code=file_content, diffs=file_diffs)

        if AiBot.is_no_issues_text(response):
            Log.print_green(f"No issues found in file: {file}")
            post_general_comment(github, file, "AI review: ✅ No issues detected in this file.")
            continue

        responses = AiBot.split_ai_response(response)
        if not responses:
            Log.print_red(f"AI response parsing failed: {responses}")
            continue

        result = False
        commit_id = vars.commit_id  # 🔹 Lấy commit ID từ GitHub Action
        Log.print_yellow(f"Using commit SHA from GitHub Action: {commit_id}")

        for response in responses:
            if response.line and commit_id:
                result = post_line_comment(github=github, file=file, text=response.text, line=response.line, commit_id=commit_id)

            if not result:
                result = post_general_comment(github=github, file=file, text=response.text)

            if not result:
                Log.print_red(f"Failed to post comment for file: {file}")

def post_line_comment(github: GitHub, file: str, text: str, line: int, commit_id: str):
    Log.print_green(f"Posting line comment on {file}:{line}")
    try:
        git_response = github.post_comment_to_line(
            text=text, 
            commit_id=commit_id, 
            file_path=file, 
            line=line
        )
        Log.print_yellow(f"Posted successfully: {git_response}")
        return True
    except RepositoryError as e:
        Log.print_red(f"Failed line comment for {file}:{line} -> {e}")
        return False

def post_general_comment(github: GitHub, file: str, text: str) -> bool:
    Log.print_green(f"Posting general comment on {file}")
    try:
        message = f"{file}\n{text}"
        git_response = github.post_comment_general(message)
        Log.print_yellow(f"Posted successfully: {git_response}")
        return True
    except RepositoryError as e:
        Log.print_red(f"Failed general comment for {file} -> {e}")
        return False

if __name__ == "__main__":
    main()
