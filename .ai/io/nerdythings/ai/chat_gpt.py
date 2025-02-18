import os
from openai import OpenAI
from ai.ai_bot import AiBot

class ChatGPT(AiBot):

    def __init__(self, token, model):
        self.__chat_gpt_model = model
        self.__client = OpenAI(api_key=token)

    def ai_request_diffs(self, code, diffs):
        try:
            response = self.__client.chat.completions.create(
                messages=[{
                    "role": "user", 
                    "content": AiBot.build_ask_text(code=code, diffs=diffs)
                }],
                model=self.__chat_gpt_model,
                stream=False,
                max_tokens=4096  
            )

            print("🔍 Raw response:", response)

            if response and hasattr(response, "choices") and len(response.choices) > 0:
                ai_message = response.choices[0].message
                print("🔍 AI message:", ai_message)

                if hasattr(ai_message, "content") and ai_message.content:
                    return ai_message.content.strip()
                else:
                    return "⚠️ AI không cung cấp phản hồi hợp lệ."
            return "⚠️ Không nhận được phản hồi từ AI."
        except Exception as e:
            import traceback
            print(f"🚨 API Error: {e}")
            print(traceback.format_exc())  # In lỗi chi tiết
            return f"❌ Error occurred: {str(e)}"
        
    def ai_request_summary(self, code, file_changes):
        try:
            summary = self.__client.chat.completions.create(
                messages=[{"role": "user", "content": f"Tóm tắt nội dung PR:\n\n{code}"}],
                model=self.__chat_gpt_model,
                stream=False,
                max_tokens=1024  
            )

            if summary and summary.choices and len(summary.choices) > 0:
                ai_message = summary.choices[0].message
                if hasattr(ai_message, "content") and ai_message.content:
                    summary_text = ai_message.content.strip()
                    table = self.create_change_table(file_changes)
                    return f"{summary_text}\n\n{table}"
                else:
                    return "⚠️ AI không cung cấp phản hồi hợp lệ."
            return "⚠️ Không nhận được phản hồi từ AI."
        except Exception as e:
            print(f"🚨 API Error: {e}")
            return "❌ Lỗi xảy ra khi xử lý AI."

    def create_change_table(self, file_changes):
        table_header = "| File | Summary Change |\n|------|----------------|\n"
        table_rows = ""
        for file, change in file_changes.items():
            table_rows += f"| {file} | {change} |\n"
        return table_header + table_rows