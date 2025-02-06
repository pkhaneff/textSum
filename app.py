from fastapi import FastAPI
from pydantic import BaseModel
from transformers import T5Tokenizer, T5ForConditionalGeneration
from fastapi.middleware.cors import CORSMiddleware
import re

# Init app
app = FastAPI(title='Text Summarization System', description="Summarize dialogues with T5", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model and tokenizer on CPU
model = T5ForConditionalGeneration.from_pretrained("phuckhang1908/T5_summary")
tokenizer = T5Tokenizer.from_pretrained("phuckhang1908/T5_summary")
model = model.to("cpu")

# Input schema for requests
class DialogueInput(BaseModel):
    dialogue: str

# Clean text function
def clean_text(text: str) -> str:
    text = re.sub(r'\r\n|\n', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'<.*?>', '', text)
    text = '\n'.join([line.strip() for line in text.split('\n') if line.strip()])
    return text.lower()

# Summarization function
def summarize_dialogue(dialogue: str) -> str:
    dialogue = clean_text(dialogue)
    inputs = tokenizer(dialogue, return_tensors="pt", truncation=True, padding="max_length", max_length=512)

    # Generate summary on CPU
    outputs = model.generate(
        inputs["input_ids"],
        max_length=150,
        num_beams=4,
        early_stopping=True
    )
    summary = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return summary

# API endpoint for text summarization
@app.post('/summarize/')
def summarize(dialogue_input: DialogueInput):
summary = summarize_dialogue(dialogue_input.dialogue)
    return {'summary-text': chattext}
