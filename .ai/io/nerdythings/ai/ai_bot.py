

from abc import ABC, abstractmethod
import re
from ai.line_comment import LineComment

class AiBot(ABC):
    
    __no_response = "No critical issues found"
    __problems = "errors, issues, potential crashes, or unhandled exceptions"
    __chat_gpt_ask_long = """
        You are an AI code reviewer specializing in security, performance, and logic issues. 
        Your task is to analyze only meaningful code changes from Git diffs and report any issues.

        🔹 **Review Scope:**
        - Focus strictly on logic modifications, ignoring formatting or purely stylistic changes.
        - Provide only high-confidence findings. If uncertain, do not report.

        🔹 **Comment Format:**
        line_number : [Issue Type] **Clear Explanation**. (Impact + Suggested Fix)
        E.g.:  
        42 : [Security] **Potential SQL Injection**. User input is directly concatenated into an SQL query. Consider using parameterized queries.

        🔹 **Strict Validation:**  
        - Each issue must be linked to a specific coding standard (e.g., OWASP, PEP8, Google Code Style).  
        - If no issues are found, return exactly: `{no_response}`.

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

                # 🔹 Bỏ qua các comment mơ hồ
                if "potential" in description.lower() and "consider" not in description.lower():
                    continue  # Nếu AI chỉ nói "có thể", nhưng không có đề xuất, bỏ qua

                # 🔹 Chuẩn hóa nội dung comment
                clean_description = description.capitalize().strip()
                if not clean_description.endswith("."):
                    clean_description += "."

                models.append(LineComment(line=int(line_number), text=f"[{issue_type}] {clean_description}"))
            else:
                models.append(LineComment(line=0, text=full_text))

        return models
    