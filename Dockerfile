FROM python:3.13-slim AS application
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY src/ /app/src/
RUN mkdir -p /data
ENV SVCDESK_DB=/data/svcdesk.db
EXPOSE 8080
CMD ["uvicorn", "svcdesk.main:app", "--app-dir", "/app/src", "--host", "0.0.0.0", "--port", "8080"]

FROM application AS tests
COPY tests/requirements.txt /app/tests/requirements.txt
RUN pip install --no-cache-dir -r /app/tests/requirements.txt
COPY tests/ /app/tests/
COPY fixtures/ /app/fixtures/
CMD ["python", "/app/tests/run.py"]
