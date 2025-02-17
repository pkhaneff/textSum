import os
from git import Git
from ai.chat_gpt import ChatGPT
from log import Log
from ai.ai_bot import AiBot
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

    update_pr_summary(changed_files, ai, github)

    # Set to track files that have been reviewed
    reviewed_files = set()

    for file in changed_files:
        process_file(file, ai, github, vars, reviewed_files)

def update_pr_summary(changed_files, ai, github):
    """
    Cập nhật PR description nếu cần nhưng không post comment PR summary.
    """
    Log.print_green("Updating PR summary...")

    file_contents = []
    for file in changed_files:
        try:
            with open(file, 'r', encoding="utf-8", errors="replace") as f:
                content = f.read()
                file_contents.append(f"### {file}\n{content[:1000]}...\n") 
        except FileNotFoundError:
            Log.print_yellow(f"File not found: {file}")
            continue

    if not file_contents:
        return

    full_context = "\n\n".join(file_contents)
    new_summary = ai.ai_request_summary(code=full_context)

    pr_data = github.get_pull_request()
    existing_body = pr_data["body"] if pr_data["body"] else ""

    updated_body = f"{existing_body}\n\n## PR Summary\n\n{new_summary}"

    github.update_pull_request(updated_body)
    Log.print_yellow("Updated PR description with PR summary.")

def process_file(file, ai, github, vars, reviewed_files):
    if file in reviewed_files:
        Log.print_green(f"Skipping file `{file}` as it has already been reviewed.")
        return

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

    handle_ai_response(response, github, file, file_diffs, reviewed_files)

def handle_ai_response(response, github, file, file_diffs, reviewed_files):
    # Kiểm tra nếu không có phản hồi từ AI hoặc phản hồi không có lỗi
    if not response or AiBot.is_no_issues_text(response):
        Log.print_green(f"No issues detected in `{file}`.")
        reviewed_files.add(file)  # Đánh dấu file là đã review
        return

    # Phân tích các gợi ý từ phản hồi
    suggestions = parse_ai_suggestions(response)
    if not suggestions:
        Log.print_red(f"Failed to parse AI suggestions for `{file}`.")
        return

    # Tạo comment nếu có gợi ý từ AI
    comment_body = f"### AI Review for `{file}`\n\n"
    for suggestion in suggestions:
        comment_body += f"- {suggestion.strip()}\n"

    try:
        # Kiểm tra nếu bình luận đã tồn tại trước đó
        existing_comments = github.get_comments()
        comment_already_posted = False
        for comment in existing_comments:
            if comment['body'] == comment_body:
                comment_already_posted = True
                break
        
        # Nếu chưa đăng bình luận giống, thì đăng bình luận mới
        if not comment_already_posted:
            github.post_comment_general(comment_body)
            Log.print_yellow(f"Posted review for `{file}`")
        else:
            Log.print_green(f"Review for `{file}` already posted, skipping.")
            
    except RepositoryError as e:
        Log.print_red(f"Failed to post review for `{file}`: {e}")

    # Đánh dấu file là đã review
    reviewed_files.add(file)

def parse_ai_suggestions(response):
    return response.split("\n\n") if response else []

if __name__ == "__main__":
    main()
