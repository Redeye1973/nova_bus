FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py stat_progression_checker.py economy_validator.py difficulty_curve_analyzer.py judge_balance.py ./
ENV PYTHONUNBUFFERED=1
EXPOSE 8110
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8110"]
