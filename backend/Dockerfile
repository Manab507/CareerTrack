# 1. Base Image
FROM python:3.11-slim

# 2. Install libpq (PostgreSQL er jonno dorkar)
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# 3. Container er vitore ekta folder banalam
WORKDIR /app

# 4. Requirements file ta copy korlam
COPY requirements.txt .

# 5. Package gulo install korlam
RUN pip install --no-cache-dir -r requirements.txt

# 6. Baki sob code copy korlam
COPY . .

# 7. Port 8000 open korlam
EXPOSE 8000

# 8. Server run korar command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]