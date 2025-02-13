from fastapi import FastAPI
from pydantic import BaseModel
from transformers import T5Tokenizer, T5ForConditionalGeneration
from fastapi.middleware.cors import CORSMiddleware
import re

app = FastAPI(title='Text Summarization System', description="Summarize dialogues with T5", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = T5ForConditionalGeneration.from_pretrained("phuckhang1908/T5_summary")
tokenizer = T5Tokenizer.from_pretrained("phuckhang1908/T5_summary")
model = model.to("cpu")

class DialogueInput(BaseModel):
    dialogue: str

def clean_text(text: str) -> str:
    text = re.sub(r'\r\n|\n', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'<.*?>', '', text)
    text = '\n'.join([line.strip() for line in text.split('\n') if line.strip()])
    return text.lower()

def summarize_dialogue(dialogue: str) -> str:
    inputs = tokenizer(dialogue, return_tensors="pt")

    outputs = model.generate(inputs["input_ids"], max_length=1000)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)


@app.post('/summarize/')
async def summarize(dialogue_input: DialogueInput):
    summary = summarize_dialogue(dialogue_input.dialogue * 1000000) 
    return {'summary': summary}

