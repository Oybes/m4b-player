FROM python:3.12-slim

# Install system dependencies (including ffmpeg for metadata/conversion)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create volume mount targets
RUN mkdir -p /app/audiobooks /app/data /app/data/whisper_models

ENV PORT=8765
ENV DATA_DIR=/app/data
ENV AUDIOBOOKS_DIR=/app/audiobooks
ENV HF_HOME=/app/data/whisper_models

EXPOSE 8765

CMD ["python", "main.py"]
