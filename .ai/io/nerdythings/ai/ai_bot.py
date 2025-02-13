

from abc import ABC, abstractmethod
import re
from ai.line_comment import LineComment

class AiBot(ABC):
    
    __no_response = "No critical issues found"
    __problems = "errors, issues, potential crashes, or unhandled exceptions"
    __chat_gpt_ask_long = """
        You are an AI code reviewer specializing in identifying issues in modified code. Your task is to analyze the **entire codebase** while giving priority to meaningful changes from the Git diffs. You must return highly relevant insights, with precise identification of syntax and logic errors.  

        ### **Review Scope:**  
        - **Analyze the entire codebase,** ensuring any dependencies between unchanged and modified code are considered.  
        - **Prioritize changes from Git diffs,** but cross-check them against the whole context for logical consistency.  

        ### **Review Guidelines:**  
        - **Identify only real issues.** False positives reduce accuracy.  
        - **Ensure high precision for syntax and logic errors.** Every issue must be verifiable.  
        - **Categorize findings clearly** based on error type.  
        - **Do not return minor stylistic or formatting concerns unless they impact functionality.**  

        ### **Issue Categories:**  
        - **[Syntax]**: Errors that cause compilation or runtime failures.  
        - **[Logic]**: Flaws leading to unintended behavior, incorrect results, or edge cases.  
        - **[Security]**: Vulnerabilities such as SQL injection, XSS, or unsafe input handling.  
        - **[Performance]**: Inefficient algorithms, redundant operations, or unnecessary resource usage.  

        ### **Output Format (Strictly Follow This Structure):**  
        Each issue must be reported as:  
        [line_number] [Error Type] [AI review]

        
        #### **Example Output:**  
        42 [Logic] The if condition always evaluates to true, which may cause an infinite loop.
        78 [Security] Potential SQL injection due to missing parameterized query.
        103 [Performance] The nested loop increases time complexity unnecessarily.

        
        - **If no issues are found, return exactly:**  
        
        ### **Code to Review (Entire Context Analyzed, Prioritizing Git Diffs):**  

        {diffs}
          
        {code}  
                                                                          
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

                if "potential" in description.lower() and "consider" not in description.lower():
                    continue  

                clean_description = description.capitalize().strip()
                if not clean_description.endswith("."):
                    clean_description += "."

                models.append(LineComment(line=int(line_number), text=f"[{issue_type}] {clean_description}"))
            else:
                models.append(LineComment(line=0, text=full_text))

        return models


    