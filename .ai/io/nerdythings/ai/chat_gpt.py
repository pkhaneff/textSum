import os
from openai import OpenAI
import traceback
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
        
    def ai_request_summary(self, file_changes):
        try:
            summary_request = """
            Tóm tắt nội dung PR. Đưa ra bảng gồm 2 cột:
            - Cột 1: Tên file thay đổi
            - Cột 2: Tóm tắt thay đổi của từng file
            
            Danh sách thay đổi:
            """
            
            for file_name, file_content in file_changes.items():
                summary_request += f"\nFile: {file_name}\nNội dung thay đổi:\n{file_content}\n"
            
            response = self.__client.chat.completions.create(
                messages=[{"role": "user", "content": summary_request}],
                model=self.__chat_gpt_model,
                stream=False,
                max_tokens=2048  
            )

            if response and response.choices and len(response.choices) > 0:
                ai_message = response.choices[0].message
                if hasattr(ai_message, "content") and ai_message.content:
                    return ai_message.content.strip()
                else:
                    return "⚠️ AI không cung cấp phản hồi hợp lệ."
            return "⚠️ Không nhận được phản hồi từ AI."
        except Exception as e:
            print(f"🚨 API Error: {e}")
            print(traceback.format_exc())  # In lỗi chi tiết
            return f"❌ Error occurred: {str(e)}"
