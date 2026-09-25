FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY omniscore ./omniscore
COPY data/calibration.json ./data/calibration.json
ENV OMNISCORE_CACHE=/app/data/cache
EXPOSE 8000
CMD ["uvicorn", "omniscore.api:app", "--host", "0.0.0.0", "--port", "8000"]
