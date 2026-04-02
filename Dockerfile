FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y g++ \
    libxcb1 \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libgl1 \
    libglib2.0-0 \
    wget &&\
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
RUN mkdir -p /root/.deepface/weights
RUN wget https://github.com/serengil/deepface_models/releases/download/v1.0/vgg_face_weights.h5 \
  -O /root/.deepface/weights/vgg_face_weights.h5
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "FaceController:app", "--host", "0.0.0.0", "--port", "8000"]