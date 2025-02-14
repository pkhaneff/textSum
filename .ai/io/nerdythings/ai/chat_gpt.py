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
                messages=[
                    {"role": "user", "content": AiBot.build_ask_text(code=code, diffs=diffs)}
                ],
                model=self.__chat_gpt_model,
                stream=False,
            )

            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content.strip()  
            else:
                return "No response from AI."
        except Exception as e:
            print(f"API Error: {e}")
            return "Error occurred during AI processing."
