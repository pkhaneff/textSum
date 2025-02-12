

from abc import ABC, abstractmethod
import re
from ai.line_comment import LineComment

class AiBot(ABC):
    
    __no_response = "No critical issues found"
    __problems = "errors, issues, potential crashes, or unhandled exceptions"
    __chat_gpt_ask_long = """
        You are an AI code reviewer specializing in identifying issues in modified code. Your task is to analyze **only meaningful code changes** from the Git diffs and report any issues.  

        **Review Scope:**  
        - **Only analyze files with structural code changes.** Ignore files where only comments or formatting have changed.  
        - **Focus on logic modifications.** Skip unchanged lines and purely stylistic adjustments.  

        **Review Guidelines:**  
        - **Analyze only the changed lines.** Ignore unchanged code.  
        - **Ignore formatting-only changes.** Focus on logic, syntax, security, and performance.  
        - **Ensure accuracy.** Each issue must be directly linked to a modified line.  

        **Issue Categories:**  
        - **Syntax Errors**: Mistakes that cause compilation or runtime failures.  
        - **Logical Errors**: Incorrect logic, unintended behavior, or edge cases.  
        - **Security Issues**: Vulnerabilities like SQL injection, XSS, or unsafe operations.  
        - **Performance Bottlenecks**: Inefficient algorithms, redundant operations, or excessive resource use.  

        **Strict Output Format:**  
        line_number : [Type] Description of the issue and potential impact.  
        **Example:**  
        42 : [Logic] if condition always evaluates to true, causing an unintended infinite loop.  
        78 : [Security] Potential SQL injection due to missing parameterized query.  
        103 : [Performance] Nested loop increases time complexity unnecessarily.  

        - If no issues are found in the modified code, return exactly:  
        
        `{no_response}`.  

        **Git Diffs (Only structural changes considered):**  

        {diffs}
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
                models.append(LineComment(line=0, text=full_text)) 

        return models

    