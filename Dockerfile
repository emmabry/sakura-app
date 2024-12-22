FROM python:3.9

RUN apt-get update && \
    apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-jpn

COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .