FROM python:3.11-slim

WORKDIR /app

# Install fonts-liberation and create arial-compatible symlinks for PDF generation
RUN apt-get update && apt-get install -y --no-install-recommends \
        fonts-liberation \
        curl \
    && mkdir -p /app/fonts \
    && ln -s /usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf    /app/fonts/arial.ttf \
    && ln -s /usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf        /app/fonts/arialbd.ttf \
    && ln -s /usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf      /app/fonts/ariali.ttf \
    && ln -s /usr/share/fonts/truetype/liberation/LiberationSans-BoldItalic.ttf  /app/fonts/arialbi.ttf \
    && rm -rf /var/lib/apt/lists/*

# uv is required by langgraph-cli when langgraph.json uses source.kind="uv"
RUN pip install --no-cache-dir uv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
