from abc import ABC, abstractmethod
import re
from ai.line_comment import LineComment

class AiBot(ABC):
    
    __no_response = "No critical issues found"
    __problems = "errors, security issues, performance bottlenecks, or bad practices"
    __chat_gpt_ask_long = """
        You are an AI code reviewer with expertise in multiple programming languages.
        Your goal is to identify and explain issues found in modified code.
        
        **Review Scope:**  
        - **Focus on meaningful structural changes** in the Git diffs. Ignore changes related to formatting or comments.  
        - **Provide clear explanations** and suggestions for fixes.  
        - **Categorize issues by severity**: Warning, Error, Critical.  

        **Review Guidelines:**  
        - **Syntax Errors**: Any issue that leads to compilation or runtime failure.  
        - **Logical Errors**: Incorrect conditions, infinite loops, unexpected behavior.  
        - **Security Issues**: SQL injection, XSS, hardcoded secrets, unvalidated inputs.  
        - **Performance Bottlenecks**: Unoptimized loops, redundant computations.  
        - **Best Practices Violations**: Not following language-specific best practices.  

        **Strict Output Format:**  
        line_number : [Severity] [Type] Description of the issue and how to fix it.  
        **Example:**  
        42 : [Error] [Logic] if condition always evaluates to true, leading to an infinite loop. Suggested fix: review condition logic.  
        78 : [Critical] [Security] Potential SQL injection risk due to lack of input sanitization. Suggested fix: use parameterized queries.  
        103 : [Warning] [Performance] Unnecessary nested loops detected. Suggested fix: optimize using dictionary lookup.  

        - If no issues are found, return exactly:  
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
            problems=AiBot.__problems,
            no_response=AiBot.__no_response,
            diffs=diffs,
            code=code,
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

            match = re.match(r"(\d+)\s*:\s*\[(.*?)\]\s*\[(.*?)\]\s*(.*)", full_text)
            if match:
                line_number, severity, issue_type, description = match.groups()
                
                clean_description = description.capitalize().strip()
                if not clean_description.endswith("."):
                    clean_description += "."
                
                models.append(LineComment(line=int(line_number), text=f"[{severity}] [{issue_type}] {clean_description}"))
            else:
                models.append(LineComment(line=0, text=full_text))

        return models
