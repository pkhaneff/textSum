from fastapi import FastAPI, Request
from pydantic import BaseModel
from transformers import T5Tokenizer, T5ForConditionalGeneration
from fastapi.middleware.cors import CORSMiddleware
import re

#init app
app = FastAPI(title='Text Summarization System', description="Summarize dialogues with T5", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#load model and tokenizer
model = T5ForConditionalGeneration.from_pretrained("./saved_summary_model")
tokenizer = T5Tokenizer.from_pretrained("./saved_summary_model")

#ensure the model is on the correct device
device = "cuda" if model.device.type == "cuda" else "cpu"
model = model.to(device)

#input schema for requests
class DialogueInput(BaseModel):
    dialogue: str

#clean text func
def clean_text(text: str) -> str:
    text = re.sub(r'\r\n|\n', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'<.*?>', '', text)
    text = '\n'.join([line.strip() for line in text.split('\n') if line.strip()])
    return text.lower()

#summarization function
def summarize_dialogue(dialogue: str) -> str:
    dialogue = clean_text(dialogue)
    print(dialogue)
    inputs = tokenizer(dialogue, return_tensors="pt", truncation=True, padding="max_length", max_length=512)
    inputs = {key: value.to(device) for key, value in inputs.items()}

    #generate summary
    outputs= model.generate(
        inputs["input_ids"],
        max_length = 150,
        num_beams = 4,
        early_stopping = True
    )
    summary = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return summary

#API endpoints for text summarization
@app.post('/summarize/')
async def summarize(dialogue_input: DialogueInput):
    summary = summarize_dialogue(dialogue_input.dialogue)
    return {'summary': summary}