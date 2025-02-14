

import os
from openai import OpenAI
from ai.ai_bot import AiBot

class ChatGPT(AiBot):

    def __init__(self, token, model):
        self.__chat_gpt_model = model
        self.__client = OpenAI(api_key = token)

    def ai_request_diffs(self, code, diffs):
        try:
            stream = self.__client.chat.completions.create(
                messages=[
                    {"role": "user", "content": AiBot.build_ask_text(code=code, diffs=diffs)}
                ],
                model=self.__chat_gpt_model,
                stream=True,
            )
            content = []
        except Exception as e:
            print(f"API Error: {e}")
        for chunk in stream:
            print(f"Chunk received: {chunk}")
            if chunk.choices and len(chunk.choices) > 0 and hasattr(chunk.choices[0], 'delta') and chunk.choices[0].delta and hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                content.append(chunk.choices[0].delta.content)  
        return " ".join(content)
    