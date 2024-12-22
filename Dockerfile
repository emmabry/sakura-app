FROM python:3.11

RUN apt-get update && \
    apt-get install -y tesseract-ocr tesseract-ocr-jpn && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

RUN tesseract --version

ENV TESSDATA_PREFIX="/usr/share/tesseract-ocr/4.00/tessdata"

EXPOSE 8000

CMD ["gunicorn", "-b", "0.0.0.0:8000", "main:app"]