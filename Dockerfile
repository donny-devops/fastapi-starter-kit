FROM python:3.12-slim

# Install only production dependencies — strip dev/test packages before pip sees them
WORKDIR /app

COPY requirements.txt .
RUN sed '/^\s*#/d; /^\s*$/d; /pytest/d; /ruff/d' requirements.txt \
    > requirements.prod.txt \
    && pip install --no-cache-dir -r requirements.prod.txt \
    && rm requirements.prod.txt

COPY . .

# Run as non-root; /app/data holds the SQLite file in Compose
RUN adduser --disabled-password --gecos "" appuser \
    && mkdir -p /app/data \
    && chown -R appuser:appuser /app /app/data
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
