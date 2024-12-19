# Stage 1: Cài đặt dependencies
FROM python:3.10-slim AS builder

WORKDIR /app

# Cài đặt pip và các dependencies
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip \
    && pip install --target=/app/dependencies -r requirements.txt

# Stage 2: Tạo image cuối cùng
FROM python:3.10-slim

WORKDIR /app

# Copy dependencies đã được cài đặt từ stage 1
COPY --from=builder /app/dependencies /usr/local/lib/python3.10/site-packages

# Copy toàn bộ code ứng dụng
COPY . .

# Chạy ứng dụng với uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--reload"]
