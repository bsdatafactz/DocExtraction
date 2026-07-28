FROM python:3.12-slim

WORKDIR /app

# libgl1/libglib2.0-0: required by opencv (a paddleocr dependency);
# libgomp1: OpenMP runtime paddlepaddle's CPU kernels link against.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
