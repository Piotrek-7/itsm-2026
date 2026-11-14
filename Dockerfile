# ai-generated: 100% - Codex pinned and updated the base and removed pip from the runtime image.
FROM python:3.13-slim@sha256:e48f59cdba69a3cbd9ed2cf0f348d90d45a8d350d98134cf1070bc106ee9ed90 AS common
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY src/ /app/src/
RUN mkdir -p /data
ENV SVCDESK_DB=/data/svcdesk.db
EXPOSE 8080
CMD ["uvicorn", "svcdesk.main:app", "--app-dir", "/app/src", "--host", "0.0.0.0", "--port", "8080", "--no-access-log"]

FROM common AS tests
COPY tests/requirements.txt /app/tests/requirements.txt
RUN pip install --no-cache-dir -r /app/tests/requirements.txt
COPY tests/ /app/tests/
COPY fixtures/ /app/fixtures/
CMD ["python", "/app/tests/run.py"]

FROM common AS application
RUN pip uninstall -y pip
