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
        - Each issue should follow the following Markdown format, resembling a commit log:

        ```markdown
        ### [Line {line_number}] - [{severity}] - [{type}] - {issue_description}

        **Code:**
        ```diff
        {code_diff}

        Suggested Fix (nếu có):
        {suggested_fix}

        Hướng dẫn:
        - Thay thế {line_number} bằng số dòng liên quan.
        - Chỉ bao gồm phần Suggested Fix nếu vấn đề cần một giải pháp. Nếu code đúng, bỏ qua phần này.
        - Bỏ qua Suggested Fix nếu vấn đề đã rõ ràng hoặc không yêu cầu thay đổi code.
        - Nếu không tìm thấy vấn đề nào, trả về chính xác: {no_response}.

        Ví dụ:
        ### [Line 15] - [Warning] - [Logical Errors] - Biến 'data' có thể chưa được khởi tạo.

        **Code:**
        ```diff
        - let result = data.length;
        + let result = data ? data.length : 0;

        Suggested Fix:
        Kiểm tra xem biến 'data' có giá trị trước khi truy cập thuộc tính 'length'.

        let result = data ? data.length : 0;
                
        **Lưu ý:**

        * Phần `Code` và `Suggested Fix` vẫn được bọc trong dấu ```diff và ``` để thể hiện code diff và code sửa lỗi.
        * Các tiêu đề và hướng dẫn được định dạng để dễ đọc.
        * Bỏ các dấu gạch đầu dòng thừa.

        **Lý do sửa đổi:**

        * Loại bỏ các định dạng Markdown phức tạp như dấu chấm đầu dòng để dễ copy.
        * Sử dụng các tiêu đề đơn giản để phân biệt các phần.
        * Giữ lại các khối code để dễ dàng nhận biết code diff và code sửa lỗi.
    """

    @abstractmethod
    def ai_request_diffs(self, code, diffs) -> str:
        pass

    @staticmethod
    def build_ask_text(code, diffs) -> str:
        if isinstance(diffs, list) and len(diffs) > 0:
            line_number = diffs[0].get("line_number", "N/A")
            severity = diffs[0].get("severity", "Warning")
            issue_type = diffs[0].get("type", "General Issue") 
        elif isinstance(diffs, dict):
            line_number = diffs.get("line_number", "N/A")
            severity = diffs.get("severity", "Warning")
            issue_type = diffs.get("type", "General Issue") 
        else:
            line_number = "N/A"
            severity = "Warning"
            issue_type = "General Issue"

        return AiBot.__chat_gpt_ask_long.format(
            problems=AiBot.__problems,
            no_response=AiBot.__no_response,
            diffs=diffs,
            code=code,
            line_number=line_number,
            severity=severity,
            type=issue_type 
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

            match = re.match(r"(⚠️|❌)\s*\[(.*?)\]\s*\[(.*?)\]\s*(.*)", full_text)
            if match and all(match.groups()):
                severity_icon, severity, issue_type, description = match.groups()
                clean_description = description.capitalize().strip() if description else "No description provided"
                if not clean_description.endswith("."):
                    clean_description += "."
                models.append(LineComment(line=0, text=f"{severity_icon} [{severity}] [{issue_type}] {clean_description}"))
            elif full_text.strip():  
                models.append(LineComment(line=0, text=full_text))

        return models
