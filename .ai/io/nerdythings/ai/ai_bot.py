

from abc import ABC, abstractmethod
import re
from ai.line_comment import LineComment

class AiBot(ABC):
    
    __no_response = "No critical issues found"
    __problems="errors, issues, potential crashes or unhandled exceptions"
    __chat_gpt_ask_long = """
        You are an AI code reviewer. Your task is to analyze the provided code changes (Git diffs) and full source code of a file, then identify **all potential issues** including but not limited to:
        - **Syntax Errors**: Any incorrect syntax that would cause compilation or runtime failure.
        - **Logical Errors**: Flaws in the code logic that might lead to incorrect results, unintended behavior, or unexpected crashes.
        - **Performance Issues**: Inefficient loops, redundant operations, memory leaks, or excessive resource consumption.

        **Instructions:**
        - Review the Git diffs carefully and check how they modify the existing code.
        - Compare the changes against the full source code to determine their impact.
        - Identify any issues that could arise from the new changes.
        - Do **not** add introductory or concluding statements.
        - Provide your findings in the following strict format:  
          ```
          line_number : [Type of Issue] Description of the issue and potential consequences.
          ```
          **Example output:**
          ```
          23 : [Security] SQL query is vulnerable to injection due to missing parameterized queries.
          45 : [Logic] Division by zero possible when variable `x` is zero.
          78 : [Performance] Unnecessary nested loop increases time complexity to O(n^2).
          ```
        - Make sure to strictly follow the given format, do not add any extra explanations.
        If no issues are found, respond with exactly: "{no_response}".

        **Git Diffs:**
        ```
        {diffs}
        ```

        **Full Code:**
        ```
        {code}
        ```
    """


    @abstractmethod
    def ai_request_diffs(self, code, diffs) -> str:
        pass

    @staticmethod
    def build_ask_text(code, diffs) -> str:
        return AiBot.__chat_gpt_ask_long.format(
            problems = AiBot.__problems,
            no_response = AiBot.__no_response,
            diffs = diffs,
            code = code,
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
        
        lines = input.strip().split("\n")
        models = []

        for full_text in lines:
            full_text = full_text.strip()
            if not full_text:
                continue

            match = re.match(r"(\d+)\s*:\s*\[(.*?)\]\s*(.*)", full_text)
            if match:
                line_number, issue_type, description = match.groups()
                models.append(LineComment(line=int(line_number), text=f"[{issue_type}] {description}"))
            else:
                models.append(LineComment(line=0, text=full_text))  # Nếu không có số dòng, ta để 0 (đánh dấu lỗi tổng quát)

        return models

    