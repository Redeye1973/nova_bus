FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo zlib1g \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py syntax_validator.py complexity_analyzer.py style_conformance.py security_scanner.py judge.py ./

ENV PYTHONUNBUFFERED=1
EXPOSE 8102

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8102"]
