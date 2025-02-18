from abc import ABC, abstractmethod
import re
from ai.line_comment import LineComment

class AiBot(ABC):
    
    __no_response = "No critical issues found"
    __problems = "errors, security issues, performance bottlenecks, or bad practices"
    __chat_gpt_ask_long = """
        You are an AI code reviewer with expertise in multiple programming languages.
        Your goal is to analyze Git diffs and identify potential issues.

        **Review Scope:**
        - Focus on meaningful structural changes, ignoring formatting or comments.
        - Provide clear explanations and actionable suggestions.
        - Categorize issues by severity: **Warning, Error, Critical**.

        **Review Guidelines:**
        - **Syntax Errors**: Compilation/runtime failures.
        - **Logical Errors**: Incorrect conditions, infinite loops, unexpected behavior.
        - **Security Issues**: SQL injection, XSS, hardcoded secrets, unvalidated inputs.
        - **Performance Bottlenecks**: Unoptimized loops, redundant computations.
        - **Best Practices Violations**: Only report issues on unchanged or newly introduced code.

        **Output Format:**
        Each issue should follow the following Markdown format, resembling a commit log:

        ```markdown
        ### [Line {line_number}] - [{severity}] - [{type}] - {issue_description}

        **Code:**
        ```diff
        {code}
        ```

        **Suggested Fix:**
        {suggested_fix}
               
        **Note:**

        *   `Code` and `Suggested Fix` are wrapped with ```diff to show code diffs and fixes.
        *   Titles and instructions are formatted for readability.
    """

    @abstractmethod
    def ai_request_diffs(self, code, diffs) -> str:
        pass

    @staticmethod
    def build_ask_text(code, diffs) -> str:
        if isinstance(diffs, list) and diffs:
            line_number = diffs[0].get("line_number", "N/A")
            severity = diffs[0].get("severity", "Warning")
            issue_type = diffs[0].get("type", "General Issue") 
            issue_description = diffs[0].get("issue_description", "No description")
            suggested_fix = diffs[0].get("suggested_fix", "")
            code_content = diffs[0].get("code", "")  # Lấy nội dung code từ diff
        elif isinstance(diffs, dict):
            line_number = diffs.get("line_number", "N/A")
            severity = diffs.get("severity", "Warning")
            issue_type = diffs.get("type", "General Issue") 
            issue_description = diffs.get("issue_description", "No description")
            suggested_fix = diffs.get("suggested_fix", "")
            code_content = diffs.get("code", "")  # Lấy nội dung code từ diff
        else:
            line_number = "N/A"
            severity = "Warning"
            issue_type = "General Issue"
            issue_description = "No description"
            suggested_fix = ""
            code_content = ""

        return AiBot.__chat_gpt_ask_long.format(
            problems=AiBot.__problems,
            no_response=AiBot.__no_response,
            diffs=diffs,
            code=code_content,
            line_number=line_number,
            severity=severity,
            type=issue_type,
            issue_description=issue_description,
            suggested_fix=suggested_fix
        )

    @staticmethod
    def is_no_issues_text(source: str) -> bool:
        target = AiBot.__no_response.replace(" ", "")
        source_no_spaces = source.replace(" ", "")
        return source_no_spaces.startswith(target)
    
    @staticmethod
    def split_ai_response(input) -> list[LineComment]:
        if not input:
            return []

        comments = []
        current_comment = None
        in_code_block = False

        for line in input.splitlines():
            line = line.strip()
            if not line:
                continue

            if line.startswith("###"):
                # Xử lý tiêu đề mới
                match = re.match(r"### \[Line (\d+)\] - \[(.*?)\] - \[(.*?)\] - (.*)", line)
                if match:
                    line_number, severity, issue_type, description = match.groups()
                    line_number = int(line_number)

                    clean_description = description.capitalize().strip()
                    if not clean_description.endswith("."):
                        clean_description += "."

                    # Lưu comment hiện tại nếu có
                    if current_comment:
                        comments.append(current_comment)

                    # Tạo comment mới
                    current_comment = LineComment(line=line_number, text=f"### [{severity}] [{issue_type}] - {clean_description}\n\n")
                    in_code_block = False  # Đặt lại trạng thái code block
            elif line.startswith("```diff"):
                # Bắt đầu code block
                in_code_block = True
                if current_comment:
                    current_comment.text += "```diff\n"
            elif line.startswith("```") and in_code_block:
                # Kết thúc code block
                in_code_block = False
                if current_comment:
                    current_comment.text += "```\n"
            else:
                # Nội dung của comment hoặc code
                if current_comment:
                    current_comment.text += line + "\n"

        # Lưu comment cuối cùng
        if current_comment:
            comments.append(current_comment)

        return comments