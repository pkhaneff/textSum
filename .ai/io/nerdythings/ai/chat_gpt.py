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
        
    def ai_request_summary(self, code):
        try:
            response = self.__client.chat.completions.create(
                messages=[{"role": "user", "content": f"Tóm tắt nội dung PR:\n\n{code}"}],
                model=self.__chat_gpt_model,
                stream=False,
                max_tokens=1024  
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
            return "❌ Lỗi xảy ra khi xử lý AI."
    