
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

COPY . ./

CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--reload"]