FROM python:3.13-slim
WORKDIR /experiment
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY capture.py .
CMD ["python", "capture.py"]
