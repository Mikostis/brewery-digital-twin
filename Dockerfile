FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir -e .

COPY scripts ./scripts

EXPOSE 8000

CMD ["fastapi", "run", "src/brewery_twin/main.py", "--host", "0.0.0.0", "--port", "8000"]
