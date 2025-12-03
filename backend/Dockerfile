FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Сначала только зависимости, чтобы слои кэшировались
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Затем основной код
COPY . .

# По умолчанию ожидаем, что переменные окружения (DB, Ollama и т.п.)
# будут переданы снаружи (docker-compose, Kubernetes и т.д.)

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]


