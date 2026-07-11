FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    python3 python3-pip ffmpeg \
    libgl1 libglib2.0-0 libsm6 libxext6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (cached layer)
COPY cv-pipeline/requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Pre-download YOLOv8n weights so cold starts are fast
RUN python3 -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

# Copy pipeline code
COPY cv-pipeline/ .

CMD ["python3", "-u", "handler.py"]
