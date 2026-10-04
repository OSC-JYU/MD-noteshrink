FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=9023

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api.py noteshrink.py md_storage.py md_service.py service.json ./
COPY help/index.md ./help/index.md

# uploads/ and output/ belong to the user the service runs as (uid 1000, as in the compose stack)
RUN mkdir -p uploads output && chown -R 1000:1000 /app
USER 1000

EXPOSE 9023

CMD ["python", "api.py"]
