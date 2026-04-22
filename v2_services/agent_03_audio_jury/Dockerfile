FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY audio_wav.py judge.py main.py pipeline_judge.py .
COPY jury ./jury
ENV PYTHONUNBUFFERED=1
EXPOSE 8103
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8103"]
