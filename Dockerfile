FROM python:3.11

RUN apt-get update && \
    apt-get install -y tesseract-ocr tesseract-ocr-jpn && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN which tesseract

ENV TESSDATA_PREFIX="/usr/share/tesseract-ocr/4.00/tessdata"

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
