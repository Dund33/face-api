FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y g++ \
    libxcb1 \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libgl1 \
    libglib2.0-0 &&\
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "FaceController:app", "--host", "0.0.0.0", "--port", "8000"]