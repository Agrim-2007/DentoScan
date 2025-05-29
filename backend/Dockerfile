FROM python:3.9-slim-buster

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libxrender1 \
    libfontconfig1 \
    libsm6 \
    libxext6 \
    libqtgui4 \
    libqt4-test \
    libhdf5-dev \
    libatlas-base-dev \
    build-essential \
    libpulse-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p uploads converted

COPY . .

EXPOSE 8000

CMD ["/bin/sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]